import json

import redis
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from backend.database.models import CityElevation


class ElevationService:
    """
    Busca elevação com cache inteligente.
    
    Estratégia:
    1. Redis: Cache hot (últimas 1000 consultadas)
    2. PostgreSQL: Busca por proximidade
    3. Open-Meteo API: Fallback (novo ponto)
    """
    
    def __init__(self, redis_client: redis.Redis, db: Session):
        self.redis = redis_client
        self.db = db
        self.cache_ttl = 86400 * 7  # 7 dias
        self.cache_prefix = "elevation:"
    
    async def get_nearest_city(
        self,
        lat: float,
        lon: float,
        max_distance_km: float = 5.0
    ) -> dict:
        """
        Busca cidade mais próxima e retorna elevação.
        
        Strategy:
        1. Redis: Verificar cache exato
        2. PostgreSQL: Busca por proximidade (índice)
        3. Open-Meteo API: Se não encontrar
        """
        
        # Step 1: Verificar Redis
        cache_key = f"{self.cache_prefix}{lat:.4f}:{lon:.4f}"
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Step 2: Buscar próximo no PostgreSQL
        # Usar índice lat/lon para query rápida
        cities = self.db.query(CityElevation).filter(
            and_(
                CityElevation.latitude.between(lat - 0.1, lat + 0.1),
                CityElevation.longitude.between(lon - 0.1, lon + 0.1)
            )
        ).all()
        
        if cities:
            # Encontrar o mais próximo
            nearest = min(
                cities,
                key=lambda c: c.distance_to(lat, lon)
            )
            
            result = {
                "city": nearest.city_name,
                "country": nearest.country,
                "elevation": nearest.elevation_m,
                "latitude": nearest.latitude,
                "longitude": nearest.longitude,
                "source": "database",
                "distance_km": nearest.distance_to(lat, lon) * 111  # Aprox. conversão
            }
            
            # Cachear no Redis
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(result))
            return result
        
        # Step 3: Usar API Open-Meteo (fallback)
        return await self._fetch_from_openmeteo(lat, lon, cache_key)
    
    async def _fetch_from_openmeteo(
        self,
        lat: float,
        lon: float,
        cache_key: str
    ) -> dict:
        """Busca elevação da API Open-Meteo"""
        # ... implementação
        pass
    
    async def bulk_load_cities(self, csv_path: str):
        """Carrega 48k cidades de CSV para PostgreSQL"""
        import pandas as pd
        
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            city = CityElevation(
                city_name=row['city'],
                country=row['country'],
                latitude=row['lat'],
                longitude=row['lon'],
                elevation_m=row['elevation']
            )
            self.db.add(city)
        
        self.db.commit()
        print(f"✅ {len(df)} cidades carregadas")
