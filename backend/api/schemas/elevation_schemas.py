"""
Pydantic schemas para elevação.
Extraído de: backend/api/routes/elevation.py
"""

from typing import Optional

from pydantic import BaseModel, Field, validator


class ElevationRequest(BaseModel):
    """Requisição para obter elevação."""
    
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    
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
            raise ValueError(
                f"Latitude must be between -90 and 90, got {lat}"
            )
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
            "example": {"lat": -22.5, "lon": -48.0}
        }


class ElevationResponse(BaseModel):
    """Resposta com elevação."""
    
    lat: float
    lon: float
    elevation_m: float
    source: str = "SRTM"
    cached: bool = False
    timestamp: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": -22.5,
                "lon": -48.0,
                "elevation_m": 580.5,
                "source": "SRTM",
                "cached": False,
                "timestamp": "2024-10-22T10:00:00Z"
            }
        }
