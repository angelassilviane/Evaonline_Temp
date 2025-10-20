from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped

from backend.database.connection import Base


class CityElevation(Base):
    """
    Cache persistente de elevações e coordenadas.
    
    Strategy:
    1. Cache local: 48k+ cidades mundiais
    2. Busca por proximidade: PostgreSQL
    3. Índices: lat/lon para query rápida
    4. Redis: últimas consultadas (hot cache)
    
    Economiza:
    - 48k requisições/dia à API Open-Meteo
    - ~2 minutos por milhar de requisições
    """
    __tablename__ = "city_elevations"
    
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    city_name: Mapped[str] = Column(String(255), nullable=False)
    country: Mapped[str] = Column(String(100))
    latitude: Mapped[float] = Column(Float, nullable=False, index=True)
    longitude: Mapped[float] = Column(Float, nullable=False, index=True)
    elevation_m: Mapped[float] = Column(Float, nullable=False)
    
    # Índices para busca rápida
    __table_args__ = (
        Index('idx_lat_lon', 'latitude', 'longitude'),
        Index('idx_city_name', 'city_name'),
    )
    
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    
    def distance_to(self, lat: float, lon: float) -> float:
        """Calcula distância Euclidiana até ponto"""
        import math
        return math.sqrt(
            (self.latitude - lat) ** 2 + 
            (self.longitude - lon) ** 2
        )
    
    def __repr__(self):
        return f"<CityElevation({self.city_name}, {self.elevation_m}m)>"
