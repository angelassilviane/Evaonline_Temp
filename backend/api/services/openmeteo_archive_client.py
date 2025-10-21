"""
Cliente para Open-Meteo Archive (dados históricos desde 1950).
Integrado com biblioteca oficial openmeteo-requests.

Variáveis para cálculo de ETo FAO-56:
- Temperatura máxima/mínima/média
- Radiação solar de ondas curtas
- Umidade relativa (máx/média/mín)
- Velocidade do vento (máx/média)
- Duração do dia
- Duração de sol
- ET0 FAO pré-calculado

Documentação: https://open-meteo.com/
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

logger = logging.getLogger(__name__)


class OpenMeteoArchiveConfig:
    """Configuração para Open-Meteo Archive."""
    
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
    TIMEOUT = 30
    RETRY_ATTEMPTS = 5
    CACHE_EXPIRE_AFTER = 3600 * 24  # 24 horas local
    
    # Variáveis essenciais para cálculo de ETo (ordem importa!)
    DAILY_VARIABLES = [
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_max",
        "wind_speed_10m_mean",
        "shortwave_radiation_sum",
        "relative_humidity_2m_max",
        "relative_humidity_2m_mean",
        "relative_humidity_2m_min",
        "daylight_duration",
        "sunshine_duration",
        "et0_fao_evapotranspiration",  # ET0 pré-calculado
    ]

class OpenMeteoArchiveClient:
    """
    Cliente para Open-Meteo Archive.
    
    Características:
    - Dados históricos desde 1950
    - Cache automático com requests_cache
    - Retry automático com backoff
    - Variáveis para ETo FAO-56
    - Sem autenticação (CC0)
    """
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Inicializa cliente com cache e retry.
        
        Args:
            cache_dir: Diretório para cache local
        """
        self.config = OpenMeteoArchiveConfig()
        
        # Setup cache + retry
        cache_session = requests_cache.CachedSession(
            cache_dir,
            expire_after=self.config.CACHE_EXPIRE_AFTER
        )
        retry_session = retry(
            cache_session,
            retries=self.config.RETRY_ATTEMPTS,
            backoff_factor=0.2
        )
        self.client = openmeteo_requests.Client(session=retry_session)
    
    def get_daily_data(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Busca dados históricos diários (com cache).
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            start_date: Data inicial (desde 1950-01-01)
            end_date: Data final
            
        Returns:
            DataFrame com colunas para ETo
            
        Raises:
            ValueError: Se coordenadas/datas inválidas
        """
        # Validar entrada
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude inválida: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude inválida: {lon}")
        if start_date > end_date:
            raise ValueError("start_date deve ser <= end_date")
        
        # Limitar a 1950 (limite da API)
        min_date = datetime(1950, 1, 1)
        if start_date < min_date:
            logger.warning(f"start_date anterior a 1950, ajustando para {min_date}")
            start_date = min_date
        
        logger.info(f"📡 Open-Meteo Archive: {lat:.4f}, {lon:.4f} ({start_date.date()} a {end_date.date()})")
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": self.config.DAILY_VARIABLES,
            "temperature_unit": "celsius",
            "wind_speed_unit": "ms",
            "precipitation_unit": "mm",
            "timezone": "UTC"
        }
        
        try:
            responses = self.client.weather_api(self.config.BASE_URL, params=params)
            response = responses[0]
            
            # Parsear resposta
            df = self._parse_response(response)
            logger.info(f"✅ Open-Meteo Archive: {len(df)} dias obtidos")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro Open-Meteo Archive: {e}")
            raise
    
    def _parse_response(self, response: Any) -> pd.DataFrame:
        """
        Parseia resposta da API em DataFrame.
        
        A ordem das variáveis DEVE CORRESPONDER à configuração DAILY_VARIABLES.
        """
        daily = response.Daily()
        
        # Criar índice de datas
        start_timestamp = daily.Time()
        end_timestamp = daily.TimeEnd()
        interval = daily.Interval()
        
        dates = pd.date_range(
            start=pd.to_datetime(start_timestamp, unit="s", utc=True),
            end=pd.to_datetime(end_timestamp, unit="s", utc=True),
            freq=pd.Timedelta(seconds=interval),
            inclusive="left"
        )
        
        # Extrair variáveis em ordem (ORDEM IMPORTA!)
        daily_data = {
            "date": dates,
            "temperature_2m_max": daily.Variables(0).ValuesAsNumpy(),
            "temperature_2m_min": daily.Variables(1).ValuesAsNumpy(),
            "temperature_2m_mean": daily.Variables(2).ValuesAsNumpy(),
            "precipitation_sum": daily.Variables(3).ValuesAsNumpy(),
            "wind_speed_10m_max": daily.Variables(4).ValuesAsNumpy(),
            "wind_speed_10m_mean": daily.Variables(5).ValuesAsNumpy(),
            "shortwave_radiation_sum": daily.Variables(6).ValuesAsNumpy(),
            "relative_humidity_2m_max": daily.Variables(7).ValuesAsNumpy(),
            "relative_humidity_2m_mean": daily.Variables(8).ValuesAsNumpy(),
            "relative_humidity_2m_min": daily.Variables(9).ValuesAsNumpy(),
            "daylight_duration": daily.Variables(10).ValuesAsNumpy(),
            "sunshine_duration": daily.Variables(11).ValuesAsNumpy(),
            "et0_fao_evapotranspiration": daily.Variables(12).ValuesAsNumpy(),
        }
        
        df = pd.DataFrame(daily_data)
        df.set_index("date", inplace=True)
        
        # Adicionar metadados
        df.attrs = {
            "latitude": response.Latitude(),
            "longitude": response.Longitude(),
            "elevation": response.Elevation(),
            "timezone": response.Timezone(),
        }
        
        return df
    
    async def health_check(self) -> bool:
        """Verifica se API está acessível."""
        try:
            self.get_daily_data(
                lat=0.0,
                lon=0.0,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now()
            )
            return True
        except Exception as e:
            logger.error(f"❌ Health check falhou: {e}")
            return False


# Exemplo de uso
if __name__ == "__main__":
    import asyncio
    
    client = OpenMeteoArchiveClient()
    
    # Brasília
    df = client.get_daily_data(
        lat=-15.7939,
        lon=-47.8828,
        start_date=datetime(2024, 9, 1),
        end_date=datetime(2024, 9, 30)
    )
    
    print(f"\n📊 Dados obtidos:")
    print(df.head())
    print(f"\n📍 Metadados: {df.attrs}")
