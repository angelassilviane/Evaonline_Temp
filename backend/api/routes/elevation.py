import redis
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.services.elevation_service import ElevationService
from backend.database.connection import get_db

router = APIRouter(prefix="/api/v1/elevation", tags=["elevation"])

@router.get("/nearest")
async def find_nearest_elevation(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    max_distance_km: float = Query(default=5.0),
    db: Session = Depends(get_db)
):
    """
    Encontra cidade mais próxima com elevação.
    
    Query: GET /api/v1/elevation/nearest?lat=-15.7801&lon=-47.9292&max_distance_km=5
    
    Response:
    {
        "city": "Brasília",
        "country": "Brazil",
        "elevation": 1064,
        "latitude": -15.7801,
        "longitude": -47.9292,
        "source": "database",
        "distance_km": 0.0
    }
    
    Performance:
    - Primeira vez: ~5-10ms (DB) vs 200ms (API)
    - Próximas vezes: <1ms (Redis)
    """
    redis_client = redis.from_url("redis://redis:6379")
    service = ElevationService(redis_client, db)
    
    return await service.get_nearest_city(
        lat, 
        lon, 
        max_distance_km
    )
