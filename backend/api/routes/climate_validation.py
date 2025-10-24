"""
Rotas para validação de dados climáticos.
Extraído de: backend/api/routes/climate_sources_routes.py (linhas 100-150)

Responsabilidade: GET /validate-period, POST /fusion-weights
"""

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from backend.api.services.climate_fusion import climate_fusion_service
from backend.api.services.climate_source_manager import ClimateSourceManager

router = APIRouter(
    prefix="/climate",
    tags=["Climate Validation"]
)


class ValidationResponse(BaseModel):
    """Resposta de validação de período."""
    valid: bool = Field(..., description="Se o período é válido")
    message: str = Field(
        default="", description="Mensagem (erro ou sucesso)"
    )


class FusionWeightsResponse(BaseModel):
    """Resposta com pesos de fusão."""
    sources: List[str] = Field(..., description="IDs das fontes")
    weights: Dict[str, float] = Field(
        ..., description="Pesos normalizados"
    )
    total: float = Field(default=1.0, description="Soma dos pesos")


@router.get(
    "/sources/validate-period",
    response_model=ValidationResponse,
    summary="Valida período de datas",
    description="""
    Valida se o período selecionado está dentro das especificações:
    - Mínimo 7 dias, máximo 15 dias
    - Máximo 1 ano no passado
    - Máximo 1 dia no futuro
    """
)
async def validate_period(
    start_date: str = Query(
        ..., description="Data inicial (YYYY-MM-DD)"
    ),
    end_date: str = Query(
        ..., description="Data final (YYYY-MM-DD)"
    )
) -> Dict:
    """
    Valida período de datas.
    
    Args:
        start_date: Data inicial em formato ISO
        end_date: Data final em formato ISO
    
    Returns:
        Dict com status de validação e mensagem
    """
    try:
        # Parse datas
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            return {
                "valid": False,
                "message": f"Invalid date format: {e}"
            }
        
        manager = ClimateSourceManager()
        valid, message = manager.validate_period(start, end)
        
        logger.info(
            f"Period validation: {valid} "
            f"({start_date} to {end_date})"
        )
        
        return {
            "valid": valid,
            "message": message if not valid else "Period valid ✓"
        }
    
    except Exception as e:
        logger.error(f"Error validating period: {e}")
        return {"valid": False, "message": str(e)}


@router.post(
    "/sources/fusion-weights",
    response_model=FusionWeightsResponse,
    summary="Calcula pesos para fusão de dados",
    description="""
    Calcula pesos normalizados para fusão de dados baseado em
    prioridades das fontes selecionadas.
    
    ⚠️ IMPORTANTE: Fontes com licença não-comercial (ex: Open-Meteo)
    são automaticamente rejeitadas para download.
    """
)
async def calculate_fusion_weights(
    sources: List[str] = Query(
        ..., description="IDs das fontes"
    ),
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(
        ..., ge=-180, le=180, description="Longitude"
    )
) -> Dict:
    """
    Calcula pesos de fusão para fontes selecionadas.
    
    Args:
        sources: Lista de IDs de fontes
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dict com fontes e pesos normalizados
    
    Raises:
        HTTPException 400: Fontes indisponíveis
        HTTPException 403: Violação de licença
    """
    try:
        manager = ClimateSourceManager()
        
        # Valida que fontes existem e estão disponíveis
        available = manager.get_available_sources(lat, lon)
        available_ids = [s["id"] for s in available]
        
        invalid_sources = [
            s for s in sources if s not in available_ids
        ]
        if invalid_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Unavailable sources: {invalid_sources}"
            )
        
        # Calcula pesos
        try:
            weights = manager.get_fusion_weights(sources, (lat, lon))
        except ValueError as e:
            # Violação de licença
            logger.warning(f"License violation: {e}")
            raise HTTPException(
                status_code=403,
                detail=str(e)
            )
        
        logger.info(f"Fusion weights calculated for {sources}")
        
        return {
            "sources": sources,
            "weights": weights,
            "total": sum(weights.values())
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating fusion weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
