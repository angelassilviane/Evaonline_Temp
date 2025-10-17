"""
Funções para obter dados de elevação/altitude.
"""
from loguru import logger


def get_elevation(lat: float, lon: float) -> float | None:
    """
    Busca altitude usando a Elevation API (Copernicus DEM 90m).
    
    TEMPORARIAMENTE usa versão SYNC (get_openmeteo_elevation) porque
    Dash roda em event loop e asyncio.run() não funciona.
    
    TODO: Migrar para versão totalmente async quando integrar com
          httpx async client do backend.
    
    Args:
        lat: Latitude (-90 a 90)
        lon: Longitude (-180 a 180)
        
    Returns:
        float | None: Elevação em metros ou None se erro
        
    Example:
        >>> elevation = get_elevation(-23.5505, -46.6333)
        >>> print(f"Altitude: {elevation:.1f}m")
        Altitude: 760.5m
    """
    try:
        # Usar versão SYNC (deprecated mas funcional)
        from backend.api.services.elevation_api import get_openmeteo_elevation

        # Retorna: Tuple[float, List[str]] = (elevation, warnings)
        elevation, warnings = get_openmeteo_elevation(lat=lat, long=lon)
        
        # Log warnings se houver
        for warning in warnings:
            logger.warning(f"Elevation API: {warning}")
        
        return elevation
    except Exception as e:
        logger.error(f"Erro ao obter elevação para ({lat}, {lon}): {e}")
        return None
