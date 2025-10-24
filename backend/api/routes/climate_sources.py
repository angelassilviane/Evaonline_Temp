"""
Rotas para metadados de fontes climáticas.
Extraído de: backend/api/routes/climate_sources_routes.py (linhas 1-100)

Responsabilidade: GET /available, /info, /validation-info
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from backend.api.services.climate_source_manager import ClimateSourceManager

router = APIRouter(
    prefix="/climate/sources",
    tags=["Climate Data Sources"]
)


@router.get(
    "/available",
    summary="Lista fontes disponíveis para localização",
    description="""
    Retorna lista de fontes de dados climáticos disponíveis para uma
    coordenada específica. Detecta automaticamente cobertura regional.
    """
)
async def get_available_sources(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(
        ..., ge=-180, le=180, description="Longitude"
    )
) -> Dict:
    """
    Lista fontes disponíveis para uma localização.
    
    Args:
        lat: Latitude (-90 a 90)
        lon: Longitude (-180 a 180)
    
    Returns:
        Dict com:
        - location: Coordenadas
        - available_sources: Lista de fontes com metadados
        - default_mode: Modo padrão ("fusion")
        - fusion_sources: IDs das fontes para fusão
    """
    try:
        manager = ClimateSourceManager()
        sources = manager.get_available_sources(lat, lon)
        
        # Filtra apenas fontes em tempo real para fusão padrão
        realtime_sources = [
            s["id"] for s in sources if s.get("realtime", False)
        ]
        
        logger.info(
            f"Found {len(sources)} sources for ({lat}, {lon})"
        )
        
        return {
            "location": {"lat": lat, "lon": lon},
            "available_sources": sources,
            "default_mode": "fusion",
            "fusion_sources": realtime_sources
        }
    
    except Exception as e:
        logger.error(f"Error getting available sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/info/{source_id}",
    summary="Detalhes de uma fonte específica",
    description="Retorna metadados completos de uma fonte de dados."
)
async def get_source_info(source_id: str) -> Dict[str, Any]:
    """
    Retorna informações detalhadas de uma fonte.
    
    Args:
        source_id: ID da fonte (openmeteo, nasa_power, met_norway, etc)
    
    Returns:
        Dict com metadados da fonte
    """
    try:
        manager = ClimateSourceManager()
        
        if source_id not in manager.SOURCES_CONFIG:
            raise HTTPException(
                status_code=404,
                detail=f"Source '{source_id}' not found"
            )
        
        logger.info(f"Retrieved source info for {source_id}")
        return manager.SOURCES_CONFIG[source_id]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/validation-info",
    summary="Informações sobre validação científica",
    description="""
    Retorna informações sobre datasets usados para validação
    científica do cálculo de ETo (Xavier, AgERA5, etc.).
    """
)
async def get_validation_info() -> Dict:
    """
    Retorna informações sobre datasets de validação.
    
    Returns:
        Dict com dados de validação científica
    """
    try:
        manager = ClimateSourceManager()
        logger.info("Retrieved validation info")
        return manager.get_validation_info()
    
    except Exception as e:
        logger.error(f"Error getting validation info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
