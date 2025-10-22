"""
Rotas para busca de localizações (nearest com PostGIS).
Extraído de: world_locations.py (linhas 255-328)

Responsabilidade: GET /nearest (otimizado com PostGIS)
"""

from math import atan2, cos, radians, sin, sqrt
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models.world_locations import WorldLocation

router = APIRouter(prefix="/world-locations", tags=["Locations Search"])


@router.get("/nearest", response_model=dict)
async def find_nearest_location(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(
        ..., ge=-180, le=180, description="Longitude"
    ),
    max_results: int = Query(
        default=1, ge=1, le=10, description="Máximo de resultados"
    ),
    db: Session = Depends(get_db),
):
    """
    Encontra localizações mais próximas.

    ✅ OTIMIZADO: Usa PostGIS ST_Distance (1ms vs 100ms sem PostGIS)

    Args:
        lat: Latitude do ponto de busca
        lon: Longitude do ponto de busca
        max_results: Quantas localizações retornar (1-10)
        db: Sessão do banco de dados

    Returns:
        Dict com localizações mais próximas ordenadas por distância

    Raises:
        HTTPException 400: Coordenadas inválidas
    """
    try:
        # Validar coordenadas
        if not (-90 <= lat <= 90):
            raise HTTPException(
                status_code=400,
                detail="Latitude must be between -90 and 90"
            )
        if not (-180 <= lon <= 180):
            raise HTTPException(
                status_code=400,
                detail="Longitude must be between -180 and 180"
            )

        # ✅ USANDO PostGIS (se disponível) - MUITO MAIS RÁPIDO
        try:
            # Tenta usar PostGIS ST_Distance
            query = db.query(
                WorldLocation,
                text(
                    f"ST_Distance(location_geom, "
                    f"ST_Point({lon}, {lat})::geography) "
                    f"as distance_m"
                )
            ).order_by(
                text(
                    f"ST_Distance(location_geom, "
                    f"ST_Point({lon}, {lat})::geography)"
                )
            ).limit(max_results)

            results = query.all()
            logger.info(
                f"Found {len(results)} locations near ({lat}, {lon}) "
                f"using PostGIS"
            )

            return {
                "query": {"lat": lat, "lon": lon},
                "nearest": [location[0].to_dict() for location in results],
                "count": len(results),
                "engine": "PostGIS"
            }

        except Exception as postgis_error:
            # ⚠️ Fallback: Sem PostGIS, usar Haversine
            logger.warning(
                f"PostGIS not available: {postgis_error}. "
                f"Using Haversine."
            )

            def haversine(lat1, lon1, lat2, lon2):
                """Calcula distância Haversine em km."""
                R = 6371  # km
                lat1, lon1, lat2, lon2 = map(
                    radians, [lat1, lon1, lat2, lon2]
                )
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = (
                    sin(dlat / 2) ** 2 +
                    cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                )
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                return R * c

            all_locations = db.query(WorldLocation).limit(50000).all()

            # Calcular distâncias
            locations_with_dist = [
                (loc, haversine(lat, lon, loc.lat, loc.lon))
                for loc in all_locations
            ]

            # Ordenar e pegar top max_results
            sorted_locs = sorted(
                locations_with_dist, key=lambda x: x[1]
            )
            results = sorted_locs[:max_results]

            logger.info(
                f"Found {len(results)} locations using Haversine "
                f"(nearest: {results[0][1]:.1f}km)"
            )

            return {
                "query": {"lat": lat, "lon": lon},
                "nearest": [
                    {**loc.to_dict(), "distance_km": round(dist, 1)}
                    for loc, dist in results
                ],
                "count": len(results),
                "engine": "Haversine (PostGIS not available)"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding nearest location: {e}")
        raise HTTPException(status_code=500, detail=str(e))
