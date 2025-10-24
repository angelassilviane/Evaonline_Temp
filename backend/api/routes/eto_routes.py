"""
Rotas internas para cálculo de ETo.
Estas rotas são consumidas pelo frontend Dash e não são expostas diretamente 
ao usuário.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException
from loguru import logger

from backend.api.services.openmeteo_smart_client import OpenMeteoSmartClient
from backend.core.eto_calculation.eto_calculation import calculate_eto_pipeline
from utils.logging import configure_logging

configure_logging()

# Router interno para funções de ETo, consumido pelo Dash
eto_router = APIRouter(
    prefix="/internal/eto", 
    tags=["ETo Calculator Internal"]
)


@eto_router.post("/eto_calculate")
async def calculate_eto_endpoint(
    lat: float,
    lng: float,
    elevation: float,
    database: str,
    start_date: str,
    end_date: str,
    estado: Optional[str] = None,
    cidade: Optional[str] = None
) -> Dict[str, Union[Dict[str, float], List[str], str, None]]:
    """
    Endpoint interno para cálculo de ETo.
    Chamado pelo frontend quando o usuário solicita o cálculo na página de ETo.

    Args:
        lat (float): Latitude (-90 a 90)
        lng (float): Longitude (-180 a 180)
        elevation (float): Elevação em metros
        database (str): Fonte de dados ('nasa_power')
        start_date (str): Data inicial (YYYY-MM-DD)
        end_date (str): Data final (YYYY-MM-DD)

    Returns:
        Dict com resultado do cálculo de ETo e possíveis avisos
    """
    try:
        # Validação de coordenadas
        if not (-90 <= lat <= 90):
            raise HTTPException(
                status_code=400, 
                detail="A latitude deve estar entre -90 e 90 graus."
            )
        if not (-180 <= lng <= 180):
            raise HTTPException(
                status_code=400, 
                detail="A longitude deve estar entre -180 e 180 graus."
            )

        # Validação de database
        valid_databases = ["nasa_power"]
        if database not in valid_databases:
            raise HTTPException(
                status_code=400,
                detail=f"Base de dados inválida. Use: {valid_databases}"
            )

        # Validação de datas
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            hoje = datetime.now()

            # Verifica limite de 1 ano para trás e 1 dia para frente
            um_ano_atras = hoje - timedelta(days=365)
            amanha = hoje + timedelta(days=1)

            if start < um_ano_atras:
                raise HTTPException(
                    status_code=400,
                    detail="A data inicial não pode ser anterior a 1 ano atrás."
                )
            if end > amanha:
                raise HTTPException(
                    status_code=400,
                    detail="A data final não pode ser posterior a amanhã."
                )
            if end < start:
                raise HTTPException(
                    status_code=400,
                    detail="A data final deve ser posterior à data inicial."
                )
            
            period_days = (end - start).days + 1
            if period_days < 7 or period_days > 15:
                raise HTTPException(
                    status_code=400,
                    detail="O período deve ser entre 7 e 15 dias."
                )

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de data inválido. Use YYYY-MM-DD."
            )

        task = calculate_eto_pipeline.apply_async(kwargs={
            "lat": lat,
            "lng": lng,
            "elevation": float(elevation),
            "database": database,
            "d_inicial": start_date,
            "d_final": end_date,
            "estado": estado if estado else "",
            "cidade": cidade if cidade else ""
        })
        
        # Return task_id immediately for WebSocket real-time updates
        logger.info(f"✅ ETo calculation task initiated: task_id={task.id}")
        return {
            "task_id": task.id,
            "status": "queued",
            "message": f"Cálculo de ETo iniciado. ID da tarefa: {task.id}"
        }

    except HTTPException as e:
        logger.error(f"Erro de validação: {e.detail}")
        return {"data": None, "warnings": [], "error": e.detail}
    except Exception as e:
        logger.error(f"Erro no endpoint calculate_eto: {str(e)}")
        return {"data": None, "warnings": [], "error": str(e)}


@eto_router.post("/eto_calculate_v3")
async def calculate_eto_smart(
    lat: float,
    lng: float,
    start_date: str,
    end_date: str,
    database: str = "open_meteo",
    estado: Optional[str] = None,
    cidade: Optional[str] = None
) -> Dict[str, Any]:
    """
    🚀 V3 ENDPOINT - Smart Open-Meteo Integration
    
    Auto-selects best API based on date range:
    - Archive API: 1940-2025 (85+ years history)
    - Forecast API: Recent + 16 days future
    - Hybrid: Both APIs merged seamlessly
    
    Returns elevation + timezone + climate data in 1 call (50% fewer API calls).
    
    Args:
        lat (float): Latitude (-90 to 90)
        lng (float): Longitude (-180 to 180)
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        database (str): "open_meteo" (default)
        estado (str): Optional state/region
        cidade (str): Optional city
    
    Returns:
        {
            "location": {
                "latitude": float,
                "longitude": float,
                "elevation": float,
                "timezone": str,
                "utc_offset_seconds": int
            },
            "climate_data": {
                "dates": [...],
                "et0_fao_evapotranspiration": [...],
                "temperature_2m_max": [...],
                ...
            },
            "metadata": {
                "api_used": "archive" | "forecast" | "hybrid",
                "api_calls": int,
                "data_points": int,
                "total_latency_ms": float
            }
        }
    """
    try:
        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise HTTPException(
                status_code=400,
                detail="Latitude must be between -90 and 90"
            )
        if not (-180 <= lng <= 180):
            raise HTTPException(
                status_code=400,
                detail="Longitude must be between -180 and 180"
            )
        
        # Validate date format
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Dates must be in YYYY-MM-DD format"
            )
        
        # Validate date logic
        if start > end:
            raise HTTPException(
                status_code=400,
                detail="start_date must be <= end_date"
            )
        
        # Validate range (7-30 days)
        range_days = (end - start).days + 1
        if range_days < 7:
            raise HTTPException(
                status_code=400,
                detail="Date range must be at least 7 days"
            )
        if range_days > 30:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 30 days"
            )
        
        # Fetch data using smart client
        logger.info(
            f"🚀 Smart ETo calculation: lat={lat}, lng={lng}, "
            f"{start_date} to {end_date}"
        )
        
        client = OpenMeteoSmartClient()
        try:
            response = await client.get_climate_data(
                lat=lat,
                lng=lng,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(
                f"✅ Success: API={response['metadata']['api_used']}, "
                f"Points={response['metadata']['data_points']}, "
                f"Latency={response['metadata']['total_latency_ms']}ms"
            )
            
            return response
        
        finally:
            await client.close()
    
    except HTTPException as e:
        logger.error(f"Validation error: {e.detail}")
        return {
            "error": e.detail,
            "location": None,
            "climate_data": None,
            "metadata": {"api_used": None, "error": True}
        }
    
    except Exception as e:
        logger.error(f"Error in calculate_eto_v3: {str(e)}")
        return {
            "error": str(e),
            "location": None,
            "climate_data": None,
            "metadata": {"api_used": None, "error": True}
        }
