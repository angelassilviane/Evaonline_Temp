"""
Rotas para listar localizações e obter marcadores do mapa.
Extraído de: world_locations.py (linhas 22-133)

Responsabilidade: GET / e /markers
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models.world_locations import WorldLocation

router = APIRouter(prefix="/world-locations", tags=["Locations"])


@router.get("/", response_model=List[dict])
async def get_all_locations(
    limit: int = Query(
        default=100, le=1000, description="Máximo de localizações"
    ),
    offset: int = Query(
        default=0, ge=0, description="Offset para paginação"
    ),
    country_code: Optional[str] = Query(
        default=None, description="Filtro por país"
    ),
    db: Session = Depends(get_db),
):
    """
    Retorna todas as localizações mundiais com paginação.

    Args:
        limit: Máximo de resultados (default: 100, max: 1000)
        offset: Offset para paginação
        country_code: Filtro opcional por código do país
        db: Sessão do banco de dados

    Returns:
        Lista de localizações com coordenadas e elevação
    """
    try:
        query = db.query(WorldLocation)

        if country_code:
            query = query.filter(
                WorldLocation.country_code == country_code.upper()
            )

        total = query.count()
        locations = query.offset(offset).limit(limit).all()

        logger.info(
            f"Retrieved {len(locations)} locations "
            f"(total: {total}, offset: {offset})"
        )

        return [
            {
                "id": loc.id,
                "name": loc.location_name,
                "country": loc.country,
                "country_code": loc.country_code,
                "lat": round(loc.lat, 4),
                "lon": round(loc.lon, 4),
                "elevation_m": round(loc.elevation_m, 1),
            }
            for loc in locations
        ]

    except Exception as e:
        logger.error(f"Error retrieving locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/markers", response_model=List[dict])
async def get_map_markers(
    bbox: Optional[str] = Query(
        default=None,
        description="Bounding box: 'west,south,east,north'",
    ),
    db: Session = Depends(get_db),
):
    """
    Retorna marcadores otimizados para exibição no mapa.

    Args:
        bbox: Bounding box opcional para filtrar por viewport

    Returns:
        Lista de marcadores com coordenadas
    """
    try:
        query = db.query(
            WorldLocation.id,
            WorldLocation.location_name,
            WorldLocation.country_code,
            WorldLocation.lat,
            WorldLocation.lon,
        )

        if bbox:
            try:
                west, south, east, north = map(float, bbox.split(","))
                # Validar bounding box
                if not (west < east and south < north):
                    raise ValueError(
                        "Invalid bbox: west must be < east, "
                        "south < north"
                    )
                if not (-180 <= west <= 180 and -180 <= east <= 180):
                    raise ValueError(
                        "Invalid bbox: longitude out of range"
                    )
                if not (-90 <= south <= 90 and -90 <= north <= 90):
                    raise ValueError(
                        "Invalid bbox: latitude out of range"
                    )

                query = query.filter(
                    WorldLocation.lon >= west,
                    WorldLocation.lon <= east,
                    WorldLocation.lat >= south,
                    WorldLocation.lat <= north,
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid bbox format. Error: {str(e)}",
                )

        locations = query.limit(10000).all()
        logger.info(f"Retrieved {len(locations)} markers for map")

        return [
            {
                "id": loc.id,
                "name": loc.location_name,
                "country_code": loc.country_code,
                "lat": round(loc.lat, 4),
                "lon": round(loc.lon, 4),
            }
            for loc in locations
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving markers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
