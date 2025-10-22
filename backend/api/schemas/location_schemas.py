"""
Pydantic schemas para localizações mundiais.
Extraído de: backend/api/routes/world_locations.py
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LocationResponse(BaseModel):
    """Resposta básica com informações de localização."""
    
    id: int
    name: str
    country: str
    country_code: str
    lat: float
    lon: float
    elevation_m: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Piracicaba",
                "country": "Brazil",
                "country_code": "BR",
                "lat": -22.5,
                "lon": -48.0,
                "elevation_m": 580.5
            }
        }


class LocationDetailResponse(BaseModel):
    """Resposta detalhada com ETo do dia."""
    
    location: Dict[str, Any]
    eto_data: Optional[Dict[str, Any]] = None
    cached: bool = False
    message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": {
                    "id": 1,
                    "name": "Piracicaba",
                    "country": "Brazil",
                    "country_code": "BR",
                    "lat": -22.5,
                    "lon": -48.0,
                    "elevation_m": 580.5
                },
                "eto_data": {
                    "eto_mm": 5.2,
                    "date": "2024-10-22"
                },
                "cached": True
            }
        }


class NearestLocationResponse(BaseModel):
    """Resposta com localizações mais próximas."""
    
    query: Dict[str, float]
    nearest: List[Dict[str, Any]]
    count: int
    engine: str = "PostGIS"
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": {"lat": -22.5, "lon": -48.0},
                "nearest": [
                    {
                        "id": 1,
                        "name": "Piracicaba",
                        "country": "Brazil",
                        "country_code": "BR",
                        "lat": -22.5,
                        "lon": -48.0,
                        "distance_km": 0.0
                    }
                ],
                "count": 1,
                "engine": "PostGIS"
            }
        }
