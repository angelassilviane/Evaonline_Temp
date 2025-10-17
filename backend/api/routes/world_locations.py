"""
Endpoints da API para localizações mundiais.

Fornece acesso aos marcadores pré-carregados do mapa mundial
e cache de cálculos diários de ETo.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models.world_locations import EToWorldCache, WorldLocation

router = APIRouter(prefix="/world-locations", tags=["World Locations"])


@router.get("/", response_model=List[dict])
async def get_all_locations(
    limit: int = Query(default=1000, le=10000, description="Máximo de localizações"),
    offset: int = Query(default=0, ge=0, description="Offset para paginação"),
    country_code: Optional[str] = Query(
        default=None, description="Filtro por código do país (ex: USA, BRA)"
    ),
    db: Session = Depends(get_db),
):
    """
    Retorna todas as localizações mundiais pré-carregadas.

    Args:
        limit: Número máximo de resultados (default: 1000, max: 10000)
        offset: Offset para paginação (default: 0)
        country_code: Filtro opcional por código do país
        db: Sessão do banco de dados

    Returns:
        List[dict]: Lista de localizações com coordenadas e elevação
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
        description="Bounding box: 'west,south,east,north' (ex: '-180,-90,180,90')",
    ),
    db: Session = Depends(get_db),
):
    """
    Retorna marcadores para exibição no mapa mundial.

    Otimizado para retornar apenas dados essenciais (lat, lon, name, id)
    para renderização rápida no frontend.

    Args:
        bbox: Bounding box opcional para filtrar marcadores visíveis
        db: Sessão do banco de dados

    Returns:
        List[dict]: Lista de marcadores simplificados
    """
    try:
        query = db.query(
            WorldLocation.id,
            WorldLocation.location_name,
            WorldLocation.country_code,
            WorldLocation.lat,
            WorldLocation.lon,
        )

        # Filtrar por bounding box se fornecido
        if bbox:
            try:
                west, south, east, north = map(float, bbox.split(","))
                query = query.filter(
                    WorldLocation.lon >= west,
                    WorldLocation.lon <= east,
                    WorldLocation.lat >= south,
                    WorldLocation.lat <= north,
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid bbox format. Use 'west,south,east,north'",
                )

        locations = query.all()

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


@router.get("/{location_id}", response_model=dict)
async def get_location_details(
    location_id: int,
    db: Session = Depends(get_db),
):
    """
    Retorna detalhes completos de uma localização específica.

    Args:
        location_id: ID da localização
        db: Sessão do banco de dados

    Returns:
        dict: Detalhes completos da localização
    """
    try:
        location = (
            db.query(WorldLocation)
            .filter(WorldLocation.id == location_id)
            .first()
        )

        if not location:
            raise HTTPException(
                status_code=404, detail=f"Location {location_id} not found"
            )

        return location.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving location {location_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{location_id}/eto-today", response_model=dict)
async def get_location_eto_today(
    location_id: int,
    db: Session = Depends(get_db),
):
    """
    Retorna cálculo de ETo do dia atual para uma localização.

    Se o cálculo já existe no cache (tabela eto_world_cache),
    retorna o valor armazenado. Caso contrário, dispara cálculo
    em tempo real.

    Args:
        location_id: ID da localização
        db: Sessão do banco de dados

    Returns:
        dict: Dados de ETo do dia com variáveis meteorológicas
    """
    try:
        # Buscar localização
        location = (
            db.query(WorldLocation)
            .filter(WorldLocation.id == location_id)
            .first()
        )

        if not location:
            raise HTTPException(
                status_code=404, detail=f"Location {location_id} not found"
            )

        # Buscar cache do dia atual
        today = datetime.now().date()
        cache_entry = (
            db.query(EToWorldCache)
            .filter(
                EToWorldCache.location_id == location_id,
                func.date(EToWorldCache.calculation_date) == today,
            )
            .first()
        )

        if cache_entry:
            logger.info(
                f"Cache hit for location {location_id} on {today}"
            )
            return {
                "location": location.to_dict(),
                "eto_data": cache_entry.to_dict(),
                "cached": True,
            }
        else:
            logger.warning(
                f"No ETo cache found for location {location_id} on {today}. "
                f"Real-time calculation not yet implemented."
            )
            return {
                "location": location.to_dict(),
                "eto_data": None,
                "cached": False,
                "message": (
                    "ETo calculation for this location is not yet available. "
                    "Daily cache will be populated by scheduled job."
                ),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving ETo for location {location_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nearest", response_model=dict)
async def find_nearest_location(
    lat: float = Query(..., description="Latitude (-90 a 90)"),
    lon: float = Query(..., description="Longitude (-180 a 180)"),
    db: Session = Depends(get_db),
):
    """
    Encontra a localização mais próxima de uma coordenada.

    Usa cálculo de distância Euclidiana simples (aproximação).
    Para precisão maior, considere usar PostGIS ST_Distance.

    Args:
        lat: Latitude do ponto de busca
        lon: Longitude do ponto de busca
        db: Sessão do banco de dados

    Returns:
        dict: Localização mais próxima com distância aproximada
    """
    try:
        # Validar coordenadas
        if not (-90 <= lat <= 90):
            raise HTTPException(
                status_code=400, detail="Latitude must be between -90 and 90"
            )
        if not (-180 <= lon <= 180):
            raise HTTPException(
                status_code=400,
                detail="Longitude must be between -180 and 180",
            )

        # Buscar localização mais próxima (distância Euclidiana)
        # NOTA: Para precisão geodésica, usar PostGIS ST_Distance
        nearest = (
            db.query(
                WorldLocation,
                (
                    func.pow(WorldLocation.lat - lat, 2)
                    + func.pow(WorldLocation.lon - lon, 2)
                ).label("distance_sq"),
            )
            .order_by("distance_sq")
            .first()
        )

        if not nearest:
            raise HTTPException(
                status_code=404, detail="No locations found in database"
            )

        location, distance_sq = nearest

        # Converter distância para km (aproximação simples)
        distance_km = (distance_sq**0.5) * 111  # 1° ≈ 111 km

        logger.info(
            f"Nearest location to ({lat}, {lon}): "
            f"{location.location_name} ({distance_km:.1f} km)"
        )

        return {
            "query": {"lat": lat, "lon": lon},
            "nearest": location.to_dict(),
            "distance_km": round(distance_km, 1),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding nearest location: {e}")
        raise HTTPException(status_code=500, detail=str(e))
