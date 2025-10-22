"""
Rotas para detalhes de localizações.
Extraído de: world_locations.py (linhas 138-250)

Responsabilidade: GET /{id} e /eto-today
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models.world_locations import EToWorldCache, WorldLocation

router = APIRouter(prefix="/world-locations", tags=["Locations Detail"])


@router.get("/{location_id}", response_model=dict)
async def get_location_details(
    location_id: int,
    db: Session = Depends(get_db),
):
    """
    Retorna detalhes completos de uma localização.

    Args:
        location_id: ID da localização
        db: Sessão do banco de dados

    Returns:
        Dict com informações completas da localização

    Raises:
        HTTPException 404: Se localização não encontrada
    """
    try:
        location = (
            db.query(WorldLocation)
            .filter(WorldLocation.id == location_id)
            .first()
        )

        if not location:
            raise HTTPException(
                status_code=404,
                detail=f"Location {location_id} not found"
            )

        logger.info(f"Retrieved location details: {location_id}")
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

    Com cache Redis + BD fallback.

    Args:
        location_id: ID da localização
        db: Sessão do banco de dados

    Returns:
        Dict com localização e dados de ETo (se disponível)

    Raises:
        HTTPException 404: Se localização não encontrada
    """
    try:
        location = (
            db.query(WorldLocation)
            .filter(WorldLocation.id == location_id)
            .first()
        )

        if not location:
            raise HTTPException(
                status_code=404,
                detail=f"Location {location_id} not found"
            )

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
                f"No cache for location {location_id} on {today}"
            )
            return {
                "location": location.to_dict(),
                "eto_data": None,
                "cached": False,
                "message": (
                    "ETo calculation not yet available."
                ),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ETo for {location_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
