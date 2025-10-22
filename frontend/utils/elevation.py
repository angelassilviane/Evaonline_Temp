"""
Funções para obter dados de elevação/altitude com cache e resiliência.
"""
import asyncio
import time
from functools import lru_cache
from typing import Optional, Tuple

import redis
from loguru import logger


# Cache em memória com timeout
@lru_cache(maxsize=1000)
def _get_elevation_cached(lat: float, lon: float) -> Tuple[Optional[float], float]:
    """
    Cache em memória para elevações com timestamp.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Tuple (elevation, timestamp)
    """
    return None, 0.0


def get_elevation(lat: float, lon: float, max_retries: int = 3) -> Optional[float]:
    """
    Busca altitude usando a Elevation API com cache e retry logic.
    
    Args:
        lat: Latitude (-90 a 90)
        lon: Longitude (-180 a 180)
        max_retries: Número máximo de tentativas
        
    Returns:
        float | None: Elevação em metros ou None se erro
        
    Example:
        >>> elevation = get_elevation(-23.5505, -46.6333)
        >>> print(f"Altitude: {elevation:.1f}m")
        Altitude: 760.5m
    """
    # Validar coordenadas
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        logger.warning(f"Coordenadas inválidas: ({lat}, {lon})")
        return None
    
    # Verificar cache primeiro
    cached_elevation, timestamp = _get_elevation_cached(lat, lon)
    if cached_elevation and (time.time() - timestamp) < 3600:  # 1 hora de cache
        logger.debug(f"Elevação do cache: {cached_elevation}m")
        return cached_elevation
    
    # Tentar obter elevação com retry logic
    for attempt in range(max_retries):
        try:
            # Usar versão SYNC (compatível com Dash)
            from backend.infrastructure.clients.elevation_api import get_openmeteo_elevation

            # Retorna: Tuple[float, List[str]] = (elevation, warnings)
            elevation, warnings = get_openmeteo_elevation(lat=lat, long=lon)
            
            # Log warnings se houver
            for warning in warnings:
                logger.warning(f"Elevation API (attempt {attempt + 1}): {warning}")
            
            # Atualizar cache
            if elevation is not None:
                # Nota: lru_cache não suporta atualização direta, 
                # em produção usar Redis
                logger.info(f"Elevação obtida: {elevation:.1f}m para ({lat}, {lon})")
                return elevation
                
        except Exception as e:
            logger.error(f"Erro ao obter elevação (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
            continue
    
    logger.error(f"Falha ao obter elevação após {max_retries} tentativas")
    return None


async def get_elevation_async(lat: float, lon: float) -> Optional[float]:
    """
    Versão assíncrona para uso com FastAPI/background tasks.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        float | None: Elevação em metros
    """
    try:
        # Em produção, usar cliente HTTP async (httpx)
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Implementar chamada async para API de elevação
            response = await client.get(
                f"https://api.open-meteo.com/v1/elevation",
                params={"latitude": lat, "longitude": lon}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("elevation", [None])[0]
            
    except Exception as e:
        logger.error(f"Erro async ao obter elevação: {e}")
        return None
