"""
Cliente para API de Elevação Open-Meteo.
Licença: CC-BY 4.0 - Atribuição requerida.

Open-Meteo Elevation API (Oficial):
- Endpoint: https://api.open-meteo.com/v1/elevation
- Coverage: Global (90m Copernicus DEM)
- Resolução: 90 metros (Copernicus Digital Elevation Model)
- Precisão: ±5-10 metros (típico)
- Sem autenticação
- Rate limit: 10,000 requests/dia por IP (gratuito)
- Cache altamente recomendado (dados estáticos)

Fonte dos Dados:
- Copernicus DEM 90m (EU Space Programme)
- Cobertura: -90° a 90° latitude (global)

Atribuição Requerida:
"Elevation data from Open-Meteo (CC BY 4.0) - Copernicus DEM 90m"

Documentação Oficial:
https://open-meteo.com/en/docs/elevation-api

Features:
- GET request simples (latitude, longitude)
- Retorna array de elevações
- Suporta múltiplas coordenadas (batch)
- CORS habilitado
"""

import asyncio
import logging
import os
from typing import List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Redis Configuration (Docker-compatible)
# Suporta REDIS_URL ou REDIS_HOST (Docker) + REDIS_PASSWORD
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Montar URL completa
if REDIS_PASSWORD:
    REDIS_URL = (
        f"redis://:{REDIS_PASSWORD}@"
        f"{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )
else:
    REDIS_URL = os.getenv(
        "REDIS_URL",
        f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )

# Open-Meteo Elevation API URL
OPENMETEO_ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"


class ElevationConfig(BaseModel):
    """Configuração da API de Elevação."""
    base_url: str = "https://api.open-meteo.com/v1/elevation"
    timeout: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0
    cache_ttl_hours: int = 720  # 30 dias (elevação não muda)


class ElevationData(BaseModel):
    """Dados de elevação retornados pela API."""
    latitude: float = Field(..., description="Latitude da consulta")
    longitude: float = Field(..., description="Longitude da consulta")
    elevation_meters: float = Field(..., description="Elevação em metros")


class ElevationClient:
    """
    Cliente assíncrono para API de Elevação Open-Meteo.
    
    Features:
    - Cobertura global
    - Cache de longa duração (elevação é estática)
    - Async/await non-blocking
    - Retry automático
    - Validação de coordenadas
    
    Limites razoáveis:
    - Elevação: -1000m (Oceanos/Fossa) a 9000m (Everest)
    
    Usage:
        >>> client = ElevationClient()
        >>> elevation = await client.get_elevation(lat=-15.7939, lon=-47.8828)
        >>> print(f"Brasília: {elevation.elevation_meters}m")
        >>> await client.close()
    """
    
    def __init__(
        self,
        config: Optional[ElevationConfig] = None,
        cache: Optional[any] = None
    ):
        """
        Inicializa cliente de elevação.
        
        Args:
            config: Configuração customizada (opcional)
            cache: Cache service (opcional, injetado via DI)
        """
        self.config = config or ElevationConfig()
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
        self.cache = cache  # Cache service opcional
    
    async def close(self):
        """Fecha conexão HTTP."""
        await self.client.aclose()
    
    async def get_elevation(
        self,
        lat: float,
        lon: float
    ) -> ElevationData:
        """
        Busca elevação para coordenadas com cache inteligente.
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            
        Returns:
            ElevationData: Dados de elevação
            
        Raises:
            ValueError: Se coordenadas inválidas
            httpx.HTTPError: Se requisição falhar
        """
        # Validações
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude inválida: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude inválida: {lon}")
        
        # 1. Tenta buscar do cache (se disponível)
        if self.cache:
            cache_key = f"elevation:{lat}:{lon}"
            cached_value = await self.cache.get(cache_key)
            
            if cached_value is not None:
                logger.info(
                    f"🎯 Cache HIT: Elevation lat={lat}, lon={lon}"
                )
                return ElevationData(
                    latitude=lat,
                    longitude=lon,
                    elevation_meters=float(cached_value)
                )
        
        # 2. Cache MISS - busca da API
        logger.info(f"🌐 Buscando Elevation API: lat={lat}, lon={lon}")
        
        params = {
            "latitude": lat,
            "longitude": lon
        }
        
        # Requisição com retry
        for attempt in range(self.config.retry_attempts):
            try:
                logger.debug(
                    f"Elevation request: lat={lat}, lon={lon} "
                    f"(attempt {attempt + 1})"
                )
                
                response = await self.client.get(
                    self.config.base_url,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                elevation_meters = self._parse_response(data)
                
                # Valida range razoável
                if not (-1000 <= elevation_meters <= 9000):
                    raise ValueError(
                        f"Elevação fora do range esperado: {elevation_meters}m"
                    )
                
                result = ElevationData(
                    latitude=lat,
                    longitude=lon,
                    elevation_meters=elevation_meters
                )
                
                # 3. Salva no cache (se disponível)
                if self.cache:
                    cache_key = f"elevation:{lat}:{lon}"
                    await self.cache.set(
                        cache_key,
                        str(elevation_meters),
                        ttl_hours=self.config.cache_ttl_hours
                    )
                    logger.info(
                        f"💾 Cache SAVE: Elevation {elevation_meters}m"
                    )
                
                return result
                
            except httpx.HTTPError as e:
                logger.warning(
                    f"Elevation request failed (attempt {attempt + 1}): {e}"
                )
                if attempt == self.config.retry_attempts - 1:
                    raise
                await self._delay_retry()
        
        raise httpx.HTTPError("Elevation API: Todos os attempts falharam")
    
    def _parse_response(self, data: dict) -> float:
        """
        Processa resposta JSON da API de Elevação.
        
        Estrutura esperada:
        {
            "elevation": [1050.5]
        }
        
        Args:
            data: JSON response
            
        Returns:
            float: Elevação em metros
        """
        if "elevation" not in data:
            raise ValueError("Resposta da API não contém 'elevation'")
        
        elevations = data["elevation"]
        
        if not isinstance(elevations, list) or len(elevations) == 0:
            raise ValueError("Campo 'elevation' inválido na resposta")
        
        elevation = elevations[0]
        
        if not isinstance(elevation, (int, float)):
            raise ValueError(
                f"Elevação não é numérica: {type(elevation)}"
            )
        
        logger.info(f"✅ Elevation parsed: {elevation}m")
        return float(elevation)
    
    async def _delay_retry(self):
        """Aguarda antes de retry."""
        import asyncio
        await asyncio.sleep(self.config.retry_delay)
    
    async def health_check(self) -> bool:
        """
        Verifica se API de Elevação está acessível.
        
        Testa com coordenadas de Brasília.
        
        Returns:
            bool: True se API está respondendo
        """
        try:
            # Brasília, Brasil
            await self.get_elevation(lat=-15.7939, lon=-47.8828)
            logger.info("✅ Elevation API health check: OK")
            return True
            
        except Exception as e:
            logger.error(f"❌ Elevation API health check failed: {e}")
            return False
    
    def get_attribution(self) -> str:
        """
        Retorna texto de atribuição obrigatório CC-BY 4.0.
        
        Returns:
            str: Texto de atribuição
        """
        return "Elevation data from Open-Meteo (CC BY 4.0)"


# Função síncrona wrapper para compatibilidade (temporária)
async def get_elevation_async(
    lat: float,
    lon: float,
    cache: Optional[any] = None
) -> Tuple[float, List[str]]:
    """
    Busca elevação de forma assíncrona (wrapper simplificado).
    
    Args:
        lat: Latitude (-90 a 90)
        lon: Longitude (-180 a 180)
        cache: Cache service opcional
        
    Returns:
        Tuple[float, List[str]]: Elevação em metros e lista de warnings
        
    Example:
        >>> elevation, warnings = await get_elevation_async(-15.7939, -47.8828)
        >>> print(f"Elevation: {elevation}m")
    """
    warnings = []
    
    client = ElevationClient(cache=cache)
    
    try:
        result = await client.get_elevation(lat=lat, lon=lon)
        return result.elevation_meters, warnings
        
    except ValueError as e:
        msg = f"Erro de validação: {str(e)}"
        logger.error(msg)
        warnings.append(msg)
        return 0.0, warnings
        
    except httpx.HTTPError as e:
        msg = f"Erro HTTP ao buscar elevação: {str(e)}"
        logger.error(msg)
        warnings.append(msg)
        return 0.0, warnings
        
    except Exception as e:
        msg = f"Erro inesperado: {str(e)}"
        logger.error(msg)
        warnings.append(msg)
        return 0.0, warnings
        
    finally:
        await client.close()


# Wrapper síncrono (TEMPORÁRIO - para compatibilidade com código legado)
def get_openmeteo_elevation(
    lat: float,
    long: float
) -> Tuple[float, List[str]]:
    """
    Busca elevação de forma SÍNCRONA (wrapper temporário).
    
    ⚠️ DEPRECATED: Use get_elevation_async() para código novo.
    Este wrapper existe apenas para compatibilidade com código legado
    que ainda não foi migrado para async/await.
    
    IMPORTANTE: Usa httpx.Client (síncrono) para evitar conflito com
    event loops existentes (ex: Dash/FastAPI).
    
    Args:
        lat: Latitude (-90 a 90)
        long: Longitude (-180 a 180)
        
    Returns:
        Tuple[float, List[str]]: Elevação em metros e lista de warnings
        
    Example:
        >>> elevation, warnings = get_openmeteo_elevation(-15.7939, -47.8828)
        >>> print(f"Elevation: {elevation}m")
    """
    import httpx
    from loguru import logger
    
    warnings = []
    
    # Validar coordenadas
    if not -90 <= lat <= 90:
        raise ValueError(
            f"Latitude inválida: {lat}. Deve estar entre -90 e 90."
        )
    if not -180 <= long <= 180:
        raise ValueError(
            f"Longitude inválida: {long}. Deve estar entre -180 e 180."
        )
    
    # Verificar cache Redis (se disponível)
    cache_key = f"elevation:{lat:.4f}:{long:.4f}"
    try:
        import redis
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
            decode_responses=True
        )
        
        # Rate Limiting - Open-Meteo Terms (Non-Commercial):
        # ✅ 10,000 calls/day
        # ✅ 5,000 calls/hour
        # ✅ 600 calls/minute
        # Implementamos com margem de segurança (95% dos limites)
        
        # Verificar limite por MINUTO (600/min → 570 com margem)
        minute_key = "elevation:rate_limit:minute"
        minute_count = redis_client.get(minute_key)
        if minute_count and int(minute_count) >= 570:
            logger.error(
                "⛔ Rate limit MINUTE exceeded: 570/600 requests/min"
            )
            warnings.append(
                "Too many requests. Please wait 1 minute."
            )
            raise ValueError(
                "Rate limit exceeded (600 requests/minute). "
                "Please slow down."
            )
        
        # Verificar limite por HORA (5000/hour → 4750 com margem)
        hour_key = "elevation:rate_limit:hour"
        hour_count = redis_client.get(hour_key)
        if hour_count and int(hour_count) >= 4750:
            logger.error(
                "⛔ Rate limit HOUR exceeded: 4750/5000 requests/hour"
            )
            warnings.append(
                "Hourly limit reached. Try again in 1 hour."
            )
            raise ValueError(
                "Rate limit exceeded (5000 requests/hour). "
                "Please try again later."
            )
        
        # Verificar limite por DIA (10000/day → 9500 com margem)
        day_key = "elevation:rate_limit:day"
        day_count = redis_client.get(day_key)
        if day_count and int(day_count) >= 9500:
            logger.error(
                "⛔ Rate limit DAY exceeded: 9500/10000 requests/day"
            )
            warnings.append(
                "Daily limit reached. Try again tomorrow."
            )
            raise ValueError(
                "Rate limit exceeded (10000 requests/day). "
                "Please try again tomorrow."
            )
        
        # Verificar cache (primeira prioridade)
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(
                f"🎯 Cache HIT: Elevation lat={lat:.4f}, lon={long:.4f}"
            )
            return float(cached), warnings
            
    except redis.RedisError as e:
        logger.warning(f"Redis cache unavailable: {e}")
        redis_client = None
    except ValueError:
        # Re-raise rate limit errors
        raise
    
    # Fazer requisição síncrona à API com retry
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"🔄 Retry {attempt}/{max_retries-1}")
            
            logger.info(
                f"🌐 Buscando Elevation API: lat={lat:.4f}, lon={long:.4f}"
            )
            
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    OPENMETEO_ELEVATION_URL,
                    params={"latitude": lat, "longitude": long}
                )
                response.raise_for_status()
                data = response.json()
            
            elevation = data.get("elevation", [None])[0]
            
            if elevation is None:
                raise ValueError(
                    "Elevação não disponível para esta localização"
                )
            
            # Salvar no cache (30 dias) e incrementar contadores
            if redis_client:
                try:
                    # Salvar elevação em cache
                    redis_client.setex(cache_key, 2592000, str(elevation))
                    logger.info(f"💾 Cache SAVE: Elevation {elevation}m")
                    
                    # Incrementar contadores de rate limit (3 janelas)
                    pipe = redis_client.pipeline()
                    
                    # Minuto: 600/min (TTL: 60s)
                    minute_key = "elevation:rate_limit:minute"
                    pipe.incr(minute_key)
                    pipe.expire(minute_key, 60)
                    
                    # Hora: 5000/hour (TTL: 3600s)
                    hour_key = "elevation:rate_limit:hour"
                    pipe.incr(hour_key)
                    pipe.expire(hour_key, 3600)
                    
                    # Dia: 10000/day (TTL: 86400s)
                    day_key = "elevation:rate_limit:day"
                    pipe.incr(day_key)
                    pipe.expire(day_key, 86400)
                    
                    results = pipe.execute()
                    minute_count = results[0]
                    hour_count = results[2]
                    day_count = results[4]
                    
                    logger.info(
                        f"📊 Rate limit - "
                        f"Min: {minute_count}/600, "
                        f"Hour: {hour_count}/5000, "
                        f"Day: {day_count}/10000"
                    )
                    
                except Exception as cache_error:
                    logger.warning(f"Failed to save cache: {cache_error}")
            
            return float(elevation), warnings
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code}: {e.response.text}"
            )
            last_error = e
            break  # Não retry em erros HTTP (404, 500, etc)
            
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning(f"Network error (attempt {attempt+1}): {e}")
            last_error = e
            if attempt < max_retries - 1:
                import time
                time.sleep(1)  # Wait 1s before retry
            continue
            
        except Exception as e:
            logger.error(f"Elevation API error: {e}")
            last_error = e
            if attempt < max_retries - 1:
                import time
                time.sleep(0.5)  # Wait 0.5s before retry
            continue
    
    # Se chegou aqui, todas as tentativas falharam
    if last_error:
        raise last_error
    raise RuntimeError("Failed to get elevation after all retries")


# Factory function
def create_elevation_client(
    cache: Optional[any] = None
) -> ElevationClient:
    """
    Factory function para criar cliente de elevação.
    
    Args:
        cache: Cache service opcional
    
    Returns:
        ElevationClient configurado
    """
    return ElevationClient(cache=cache)


# Exemplo de uso
async def example_usage():
    """Demonstra uso do cliente de elevação."""
    client = ElevationClient()
    
    try:
        # Brasília, Brasil
        brasilia = await client.get_elevation(lat=-15.7939, lon=-47.8828)
        print(f"Brasília: {brasilia.elevation_meters}m")
        
        # Monte Everest (aproximado)
        everest = await client.get_elevation(lat=27.9881, lon=86.9250)
        print(f"Everest: {everest.elevation_meters}m")
        
        # Vale da Morte (baixo nível)
        death_valley = await client.get_elevation(lat=36.2547, lon=-116.8170)
        print(f"Death Valley: {death_valley.elevation_meters}m")
        
    finally:
        await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
