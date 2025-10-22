"""
Schemas (Pydantic models) para validação de requisições/respostas da API.
Centraliza todos os DTOs em um único lugar.
"""

from .climate_schemas import (
    ClimateDataResponse,
    ClimateDownloadRequest,
    ClimateSourceResponse,
    ClimateValidationRequest,
)
from .elevation_schemas import ElevationRequest, ElevationResponse
from .location_schemas import LocationDetailResponse, LocationResponse, NearestLocationResponse

__all__ = [
    # Climate schemas
    "ClimateSourceResponse",
    "ClimateValidationRequest",
    "ClimateDownloadRequest",
    "ClimateDataResponse",
    # Elevation schemas
    "ElevationRequest",
    "ElevationResponse",
    # Location schemas
    "LocationResponse",
    "LocationDetailResponse",
    "NearestLocationResponse",
]
