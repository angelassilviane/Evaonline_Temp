"""
Modelo de banco de dados para localizações mundiais pré-carregadas.

Este modelo armazena cidades do mundo com elevação para exibição
de marcadores no mapa mundial com cálculo diário de ETo.
"""
from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from sqlalchemy.sql import func

from ..connection import Base


class WorldLocation(Base):
    """
    Modelo para armazenamento de localizações mundiais.

    Esta tabela armazena cidades pré-carregadas do CSV worldcities_with_elevation.csv
    para exibição de marcadores no mapa mundial. Cada localização tem coordenadas
    e elevação pré-calculadas, permitindo cálculo rápido de ETo diário.

    Attributes:
        id: Chave primária auto-incrementada
        location_name: Nome da cidade (ex: "Paris")
        country: Nome do país (ex: "France")
        country_code: Código ISO do país (ex: "FRA")
        lat: Latitude (-90 a 90)
        lon: Longitude (-180 a 180)
        elevation_m: Elevação em metros (pode ser negativa para locais abaixo do mar)
        created_at: Data/hora de criação do registro
        updated_at: Data/hora da última atualização

    Indexes:
        - idx_world_locations_coords: Índice espacial (lat, lon) para queries rápidas
        - idx_world_locations_country: Índice por país para filtragem
    """

    __tablename__ = "world_locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_name = Column(String(255), nullable=False, index=True)
    country = Column(String(255), nullable=False)
    country_code = Column(String(3), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    elevation_m = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return (
            f"<WorldLocation(id={self.id}, "
            f"name='{self.location_name}', "
            f"country='{self.country}', "
            f"lat={self.lat:.4f}, lon={self.lon:.4f}, "
            f"elevation={self.elevation_m:.1f}m)>"
        )

    def to_dict(self) -> dict:
        """
        Converte objeto para dicionário.

        Returns:
            dict: Dicionário com dados da localização
        """
        return {
            "id": self.id,
            "location_name": self.location_name,
            "country": self.country,
            "country_code": self.country_code,
            "lat": self.lat,
            "lon": self.lon,
            "elevation_m": self.elevation_m,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Índices para performance
Index(
    'idx_world_locations_coords',
    WorldLocation.lat,
    WorldLocation.lon,
    postgresql_using='btree'
)

Index(
    'idx_world_locations_country',
    WorldLocation.country_code,
    postgresql_using='btree'
)


class EToWorldCache(Base):
    """
    Cache de cálculos diários de ETo para localizações mundiais.

    Esta tabela armazena os cálculos de ETo para o dia atual de cada
    localização mundial. É atualizada diariamente via job agendado.

    Attributes:
        id: Chave primária auto-incrementada
        location_id: Referência à WorldLocation
        calculation_date: Data do cálculo (apenas data, sem hora)
        data_source: Fonte de dados climáticos (nasa_power, met_norway, nws_usa, data_fusion)
        eto_mm: Evapotranspiração de referência em mm/dia
        precipitation_mm: Precipitação em mm/dia
        temp_max_c: Temperatura máxima em °C
        temp_min_c: Temperatura mínima em °C
        temp_avg_c: Temperatura média em °C
        humidity_avg: Umidade relativa média em %
        wind_speed_ms: Velocidade do vento em m/s
        solar_radiation_mjm2: Radiação solar em MJ/m²/dia
        calculated_at: Data/hora do cálculo
        expires_at: Data/hora de expiração (midnight + 1 dia)

    Indexes:
        - idx_eto_world_cache_location_date: Índice único (location_id, calculation_date)
        - idx_eto_world_cache_expires: Índice para limpeza de cache expirado
    """

    __tablename__ = "eto_world_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(Integer, nullable=False, index=True)
    calculation_date = Column(DateTime, nullable=False)
    data_source = Column(String(50), nullable=False)
    
    # Resultado ETo
    eto_mm = Column(Float, nullable=False)
    precipitation_mm = Column(Float, nullable=True)
    
    # Variáveis meteorológicas
    temp_max_c = Column(Float, nullable=True)
    temp_min_c = Column(Float, nullable=True)
    temp_avg_c = Column(Float, nullable=True)
    humidity_avg = Column(Float, nullable=True)
    wind_speed_ms = Column(Float, nullable=True)
    solar_radiation_mjm2 = Column(Float, nullable=True)
    
    # Metadados
    calculated_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<EToWorldCache(id={self.id}, "
            f"location_id={self.location_id}, "
            f"date={self.calculation_date.date()}, "
            f"source='{self.data_source}', "
            f"eto={self.eto_mm:.2f}mm)>"
        )

    def to_dict(self) -> dict:
        """
        Converte objeto para dicionário.

        Returns:
            dict: Dicionário com dados do cache
        """
        return {
            "id": self.id,
            "location_id": self.location_id,
            "calculation_date": self.calculation_date.date().isoformat(),
            "data_source": self.data_source,
            "eto_mm": round(self.eto_mm, 2),
            "precipitation_mm": round(self.precipitation_mm, 2) if self.precipitation_mm else None,
            "temp_max_c": round(self.temp_max_c, 1) if self.temp_max_c else None,
            "temp_min_c": round(self.temp_min_c, 1) if self.temp_min_c else None,
            "temp_avg_c": round(self.temp_avg_c, 1) if self.temp_avg_c else None,
            "humidity_avg": round(self.humidity_avg, 1) if self.humidity_avg else None,
            "wind_speed_ms": round(self.wind_speed_ms, 2) if self.wind_speed_ms else None,
            "solar_radiation_mjm2": round(self.solar_radiation_mjm2, 2) if self.solar_radiation_mjm2 else None,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


# Índices para performance
Index(
    'idx_eto_world_cache_location_date',
    EToWorldCache.location_id,
    EToWorldCache.calculation_date,
    unique=True,
    postgresql_using='btree'
)

Index(
    'idx_eto_world_cache_expires',
    EToWorldCache.expires_at,
    postgresql_using='btree'
)
