"""
Serviço de elevação com cache inteligente (3 camadas).

Estratégia de Resolução (3 camadas):
1. Redis: Cache hot (últimas consultas - 7 dias)
2. PostgreSQL: Busca por proximidade (índice geográfico)
3. Open-Meteo API: Fallback para coordenadas novas

Padrão:
  Service Layer com múltiplas backends

Exemplo de uso:
    from backend.api.services.elevation_service import ElevationService
    
    # Inicializar
    service = ElevationService(redis_client, db_session)
    
    # Buscar elevação
    elevation = await service.get_nearest_city(
        lat=-15.7939,
        lon=-47.8828,
        max_distance_km=5.0
    )
    # {
    #     "city": "Brasília",
    #     "country": "Brazil",
    #     "elevation": 1050,
    #     "source": "database",
    #     "distance_km": 0.5
    # }

Referências:
  - Open-Meteo Elevation API: https://open-meteo.com/en/docs/elevation-api
  - PostgreSQL Geospatial: https://postgis.net/
"""

import csv
import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import httpx
import redis
from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.database.models import CityElevation

logger = logging.getLogger(__name__)


class ElevationService:
    """
    Serviço de elevação com cache inteligente (3 camadas).
    
    Camadas de resolução:
    1. **Redis Cache**: Últimas coordenadas consultadas (7 dias)
    2. **PostgreSQL DB**: Cidades próximas (busca por bbox)
    3. **Open-Meteo API**: Fallback para coordenadas novas
    
    Features:
    - Cache automático em Redis
    - Busca por proximidade inteligente
    - Fallback para API externa
    - Batch loading de cidades (48k)
    - Health check das 3 camadas
    - Função de limpeza de cache
    
    Performance:
    - Redis HIT: ~1ms
    - PostgreSQL HIT: ~10ms (índice)
    - API Fallback: ~500ms (com retry)
    
    Example:
        >>> service = ElevationService(redis_client, db_session)
        >>> elevation = await service.get_nearest_city(
        ...     lat=-15.7939,
        ...     lon=-47.8828
        ... )
        >>> print(f"Elevação: {elevation['elevation']}m")
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        db_session: Session,
        elevation_api_client: Optional[any] = None
    ):
        """
        Inicializa serviço de elevação.
        
        Args:
            redis_client: Cliente Redis para cache
            db_session: Session SQLAlchemy para PostgreSQL
            elevation_api_client: ElevationClient (opcional, para fallback)
        """
        self.redis = redis_client
        self.db = db_session
        self.elevation_client = elevation_api_client
        self.cache_ttl = 86400 * 7  # 7 dias
        self.cache_prefix = "elevation:"
        logger.info("ElevationService initialized")
    
    async def get_nearest_city(
        self,
        lat: float,
        lon: float,
        max_distance_km: float = 5.0
    ) -> Dict:
        """
        Busca elevação com estratégia 3-camadas.
        
        Fluxo de Resolução:
        1. Verifica cache Redis (exato)
        2. Busca cidade próxima no PostgreSQL (bbox)
        3. Fallback para Open-Meteo API
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            max_distance_km: Distância máxima para considerar (default 5km)
            
        Returns:
            Dict com elevação e metadados:
            {
                "elevation": 1050,
                "city": "Brasília",
                "country": "Brazil",
                "latitude": -15.7939,
                "longitude": -47.8828,
                "source": "database|redis|api",
                "distance_km": 0.5
            }
            
        Raises:
            ValueError: Se coordenadas inválidas
            httpx.HTTPError: Se API falhar e sem fallback
        """
        # Validar coordenadas
        if not -90 <= lat <= 90:
            raise ValueError(f"Latitude inválida: {lat}")
        if not -180 <= lon <= 180:
            raise ValueError(f"Longitude inválida: {lon}")
        
        cache_key = f"{self.cache_prefix}{lat:.4f}:{lon:.4f}"
        
        # CAMADA 1: Redis Cache (exato)
        try:
            cached = self.redis.get(cache_key)
            if cached:
                logger.info(f"🎯 Cache HIT: Redis [{lat:.4f}, {lon:.4f}]")
                return json.loads(cached)
        except redis.RedisError as e:
            logger.warning(f"Redis error (continuando): {e}")
        
        # CAMADA 2: PostgreSQL (busca por proximidade)
        logger.debug(f"🔍 Buscando cidade próxima no BD: [{lat:.4f}, {lon:.4f}]")
        
        try:
            # Usar índice geográfico: bbox de 0.1 graus (~11km)
            cities = self.db.query(CityElevation).filter(
                and_(
                    CityElevation.latitude.between(lat - 0.1, lat + 0.1),
                    CityElevation.longitude.between(lon - 0.1, lon + 0.1)
                )
            ).all()
            
            if cities:
                # Encontrar cidade mais próxima
                nearest = min(
                    cities,
                    key=lambda c: self._distance_km(lat, lon, c.latitude, c.longitude)
                )
                
                distance = self._distance_km(lat, lon, nearest.latitude, nearest.longitude)
                
                # Validar se está dentro do limite
                if distance <= max_distance_km:
                    result = {
                        "elevation": nearest.elevation_m,
                        "city": nearest.city_name,
                        "country": nearest.country,
                        "latitude": nearest.latitude,
                        "longitude": nearest.longitude,
                        "source": "database",
                        "distance_km": round(distance, 2),
                        "timestamp": self._now_iso()
                    }
                    
                    # Cachear em Redis
                    self._cache_result(cache_key, result)
                    
                    logger.info(
                        f"✅ BD HIT: {nearest.city_name} "
                        f"({distance:.1f}km, {nearest.elevation_m}m)"
                    )
                    return result
                else:
                    logger.debug(
                        f"⚠️ Cidade encontrada mas > max_distance "
                        f"({distance:.1f}km > {max_distance_km}km)"
                    )
        
        except Exception as e:
            logger.warning(f"PostgreSQL query error: {e}")
        
        # CAMADA 3: Open-Meteo API (fallback)
        logger.debug(f"📡 Fallback para API: [{lat:.4f}, {lon:.4f}]")
        return await self._fetch_from_openmeteo(lat, lon, cache_key)
    
    async def _fetch_from_openmeteo(
        self,
        lat: float,
        lon: float,
        cache_key: str
    ) -> Dict:
        """
        Busca elevação da API Open-Meteo (fallback).
        
        Args:
            lat: Latitude
            lon: Longitude
            cache_key: Chave para cachear resultado
            
        Returns:
            Dict com elevação
            
        Raises:
            httpx.HTTPError: Se requisição falhar
        """
        if not self.elevation_client:
            # Se não houver cliente configurado, usar httpx diretamente
            logger.warning(
                "elevation_client não configurado, "
                "usando httpx direto"
            )
            return await self._fetch_direct(lat, lon, cache_key)
        
        try:
            logger.info(f"🌐 Buscando API Open-Meteo: [{lat:.4f}, {lon:.4f}]")
            
            result_data = await self.elevation_client.get_elevation(lat, lon)
            
            result = {
                "elevation": result_data.elevation_meters,
                "city": None,
                "country": None,
                "latitude": lat,
                "longitude": lon,
                "source": "api",
                "distance_km": 0,
                "timestamp": self._now_iso()
            }
            
            # Cachear resultado
            self._cache_result(cache_key, result)
            
            logger.info(
                f"✅ API HIT: {result_data.elevation_meters}m "
                f"(lat={lat:.4f}, lon={lon:.4f})"
            )
            return result
            
        except Exception as e:
            logger.error(f"❌ Elevation API error: {e}")
            raise
    
    async def _fetch_direct(
        self,
        lat: float,
        lon: float,
        cache_key: str
    ) -> Dict:
        """
        Busca elevação usando httpx direto (sem ElevationClient).
        
        Fallback quando elevation_client não está configurado.
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "https://api.open-meteo.com/v1/elevation",
                    params={"latitude": lat, "longitude": lon}
                )
                response.raise_for_status()
                data = response.json()
            
            elevation = data.get("elevation", [None])[0]
            
            if elevation is None:
                raise ValueError("API retornou elevação inválida")
            
            result = {
                "elevation": float(elevation),
                "city": None,
                "country": None,
                "latitude": lat,
                "longitude": lon,
                "source": "api",
                "distance_km": 0,
                "timestamp": self._now_iso()
            }
            
            # Cachear resultado
            self._cache_result(cache_key, result)
            
            logger.info(f"✅ API Direct: {elevation}m")
            return result
            
        except Exception as e:
            logger.error(f"❌ Direct API fetch failed: {e}")
            raise
    
    def _cache_result(self, cache_key: str, result: Dict) -> None:
        """
        Salva resultado em Redis com TTL.
        
        Args:
            cache_key: Chave de cache
            result: Resultado a cachear
        """
        try:
            self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(result)
            )
            logger.debug(f"💾 Cache saved: {cache_key}")
        except redis.RedisError as e:
            logger.warning(f"Failed to cache result: {e}")
    
    @staticmethod
    def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distância entre dois pontos em km.
        
        Usa fórmula de Haversine (acurada para pequenas distâncias).
        
        Args:
            lat1, lon1: Ponto 1 (graus)
            lat2, lon2: Ponto 2 (graus)
            
        Returns:
            Distância em km
        """
        R = 6371  # Raio da Terra em km
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(dlon / 2) ** 2
        )
        
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    @staticmethod
    def _now_iso() -> str:
        """Retorna timestamp ISO 8601."""
        return datetime.utcnow().isoformat()
    
    async def bulk_load_cities(
        self,
        csv_path: str,
        batch_size: int = 1000
    ) -> Dict:
        """
        Carrega cidades de CSV para PostgreSQL com batch insert.
        
        Formato esperado do CSV:
            city,country,latitude,longitude,elevation_m
            Brasília,Brazil,-15.7939,-47.8828,1050
            
        Args:
            csv_path: Caminho para arquivo CSV
            batch_size: Tamanho do batch para insert (default 1000)
            
        Returns:
            Dict com estatísticas:
            {
                "total_loaded": 48000,
                "total_errors": 5,
                "csv_rows": 48005,
                "success_rate": "99.9%"
            }
            
        Raises:
            FileNotFoundError: Se CSV não existe
            ValueError: Se CSV mal formatado
        """
        csv_file = Path(csv_path)
        
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV não encontrado: {csv_path}")
        
        logger.info(f"📥 Carregando cidades de {csv_path}")
        
        loaded = 0
        errors = 0
        batch = []
        row_num = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if not reader.fieldnames:
                    raise ValueError("CSV vazio ou sem header")
                
                required_fields = ['city', 'country', 'latitude', 'longitude', 'elevation_m']
                missing = [f for f in required_fields if f not in reader.fieldnames]
                
                if missing:
                    raise ValueError(f"CSV faltando colunas: {missing}")
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Parsear coordenadas e elevação
                        lat = float(row['latitude'])
                        lon = float(row['longitude'])
                        elev = float(row['elevation_m'])
                        
                        # Validar
                        if not -90 <= lat <= 90:
                            raise ValueError(f"Latitude inválida: {lat}")
                        if not -180 <= lon <= 180:
                            raise ValueError(f"Longitude inválida: {lon}")
                        
                        # Criar objeto
                        city = CityElevation(
                            city_name=row['city'],
                            country=row['country'],
                            latitude=lat,
                            longitude=lon,
                            elevation_m=int(elev)
                        )
                        
                        batch.append(city)
                        
                        # Flush batch
                        if len(batch) >= batch_size:
                            self.db.add_all(batch)
                            self.db.commit()
                            loaded += len(batch)
                            logger.debug(f"✅ Batch {loaded // batch_size}: {loaded} cidades")
                            batch = []
                    
                    except (ValueError, KeyError) as e:
                        errors += 1
                        logger.warning(f"Erro linha {row_num}: {e}")
                        continue
                
                # Flush último batch
                if batch:
                    self.db.add_all(batch)
                    self.db.commit()
                    loaded += len(batch)
            
            result = {
                "status": "success",
                "total_loaded": loaded,
                "total_errors": errors,
                "csv_rows": row_num,
                "success_rate": f"{(loaded / row_num * 100):.1f}%" if row_num > 0 else "0%"
            }
            
            logger.info(
                f"✅ Carregamento concluído: "
                f"{loaded} cidades, {errors} erros"
            )
            
            return result
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erro no bulk load: {e}")
            raise
    
    def clear_cache(self, pattern: str = "elevation:*") -> int:
        """
        Limpa cache Redis com padrão.
        
        Args:
            pattern: Padrão de chaves (default "elevation:*")
            
        Returns:
            Número de chaves deletadas
        """
        try:
            keys = self.redis.keys(pattern)
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"🗑️ Cache limpo: {deleted} chaves")
                return deleted
            return 0
        except redis.RedisError as e:
            logger.error(f"❌ Failed to clear cache: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Health check das 3 camadas.
        
        Returns:
            Dict com status:
            {
                "redis": True,
                "postgres": True,
                "api": True,
                "healthy": True
            }
        """
        result = {
            "redis": False,
            "postgres": False,
            "api": False
        }
        
        # Check Redis
        try:
            self.redis.ping()
            result["redis"] = True
            logger.debug("✅ Redis OK")
        except Exception as e:
            logger.warning(f"❌ Redis failed: {e}")
        
        # Check PostgreSQL
        try:
            self.db.execute("SELECT 1")
            result["postgres"] = True
            logger.debug("✅ PostgreSQL OK")
        except Exception as e:
            logger.warning(f"❌ PostgreSQL failed: {e}")
        
        # Check API (se cliente disponível)
        if self.elevation_client:
            try:
                await self.elevation_client.health_check()
                result["api"] = True
                logger.debug("✅ Elevation API OK")
            except Exception as e:
                logger.warning(f"❌ API failed: {e}")
        else:
            logger.debug("⚠️ Elevation client não configurado")
        
        result["healthy"] = result["redis"] and result["postgres"]
        
        return result


# Factory function
def create_elevation_service(
    redis_client: redis.Redis,
    db_session: Session,
    elevation_client: Optional[any] = None
) -> ElevationService:
    """
    Factory para criar serviço de elevação.
    
    Args:
        redis_client: Cliente Redis
        db_session: Session SQLAlchemy
        elevation_client: ElevationClient (opcional)
        
    Returns:
        ElevationService configurado
    """
    return ElevationService(
        redis_client=redis_client,
        db_session=db_session,
        elevation_api_client=elevation_client
    )
