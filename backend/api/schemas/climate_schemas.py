"""
Pydantic schemas para validação de dados de clima.
Extraído de: backend/api/routes/climate_sources_routes.py
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ClimateSourceResponse(BaseModel):
    """Resposta com informações sobre fontes de clima disponíveis."""
    
    id: int
    name: str
    description: Optional[str] = None
    available: bool
    coverage: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "OpenMeteo",
                "description": "Open-Meteo API",
                "available": True,
                "coverage": {"global": True}
            }
        }


class ClimateValidationRequest(BaseModel):
    """Requisição para validar coordenadas e dados de clima."""
    
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    start_date: Optional[str] = Field(
        None, description="Data inicial (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None, description="Data final (YYYY-MM-DD)"
    )
    
    @validator("lat", pre=True)
    def validate_latitude(cls, v):
        """Valida latitude."""
        if v is None:
            raise ValueError("Latitude is required")
        try:
            lat = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid latitude: {v}")
        if not -90 <= lat <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        return lat
    
    @validator("lon", pre=True)
    def validate_longitude(cls, v):
        """Valida longitude."""
        if v is None:
            raise ValueError("Longitude is required")
        try:
            lon = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid longitude: {v}")
        if not -180 <= lon <= 180:
            raise ValueError(
                f"Longitude must be between -180 and 180, got {lon}"
            )
        return lon
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": -22.5,
                "lon": -48.0,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        }


class ClimateDownloadRequest(BaseModel):
    """Requisição para download de dados climáticos."""
    
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    variables: List[str] = Field(
        ..., description="Variáveis climáticas desejadas"
    )
    start_date: str = Field(..., description="Data inicial (YYYY-MM-DD)")
    end_date: str = Field(..., description="Data final (YYYY-MM-DD)")
    source: str = Field(default="openmeteo", description="Fonte de dados")
    
    @validator("variables")
    def validate_variables(cls, v):
        """Valida lista de variáveis."""
        if not v:
            raise ValueError("At least one variable is required")
        valid_vars = {
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "solar_radiation"
        }
        invalid = set(v) - valid_vars
        if invalid:
            raise ValueError(f"Invalid variables: {invalid}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": -22.5,
                "lon": -48.0,
                "variables": ["temperature_2m", "precipitation"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "source": "openmeteo"
            }
        }


class ClimateDataResponse(BaseModel):
    """Resposta com dados climáticos."""
    
    location: Dict[str, Any]
    period: Dict[str, str]
    data: List[Dict[str, Any]]
    source: str
    timestamp: str
    quality: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": {"lat": -22.5, "lon": -48.0, "name": "Piracicaba"},
                "period": {"start": "2024-01-01", "end": "2024-12-31"},
                "data": [
                    {"date": "2024-01-01", "temp_mean": 25.3, "precip": 0.0}
                ],
                "source": "openmeteo",
                "timestamp": "2024-10-22T10:00:00Z",
                "quality": "good"
            }
        }
