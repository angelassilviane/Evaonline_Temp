"""
Cliente para Open-Meteo usando biblioteca oficial (openmeteo-requests).

Mantém compatibilidade com cache Redis e oferece suporte a:
- Dados históricos (Archive) - desde 1950
- Previsão (Forecast) - até 16 dias
- Dados atuais com ET0 FAO-56

Variáveis para cálculo de ETo:
- Temperatura máxima/mínima/média
- Radiação solar de ondas curtas
- Umidade relativa (máx/média/mín)
- Velocidade do vento (máx/média)
- Duração do dia
- Duração de sol
- ET0 FAO pré-calculado

Open-Meteo: https://open-meteo.com/
Biblioteca: https://pypi.org/project/openmeteo-requests/
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

logger = logging.getLogger(__name__)


class OpenMeteoConfig:
    """Configuração para Open-Meteo (Archive + Forecast)."""
    
    # URLs das APIs
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Cache e Retry
    TIMEOUT = 30
    RETRY_ATTEMPTS = 5
    CACHE_EXPIRE_AFTER = 3600 * 24  # 24h local
    
    # Variáveis essenciais para ETo FAO-56 (ORDEM IMPORTA!)
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
    
    # Cache TTL específico por tipo
    ARCHIVE_CACHE_TTL = 86400 * 30  # 30 dias (dados históricos não mudam)
    FORECAST_CACHE_TTL = 3600 * 6    # 6 horas (previsão muda frequentemente)


class OpenMeteoArchiveClient:
    """
    Cliente para Open-Meteo Archive (dados históricos).
    
    Features:
    - Dados desde 1950
    - Cache automático (requests_cache)
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
        self.config = OpenMeteoConfig()
        
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
        
        logger.info(f"📡 Archive: {lat:.4f}, {lon:.4f} ({start_date.date()} a {end_date.date()})")
        
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
            responses = self.client.weather_api(self.config.ARCHIVE_URL, params=params)
            response = responses[0]
            
            # Parsear resposta
            df = self._parse_response(response)
            logger.info(f"✅ Archive: {len(df)} dias obtidos")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro Archive: {e}")
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


class OpenMeteoForecastClient:
    """
    Cliente para Open-Meteo Forecast (previsão).
    
    Features:
    - Previsão até 16 dias
    - Cache TTL curto (6 horas)
    - Variáveis para ETo FAO-56
    - Sem autenticação (CC0)
    """
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Inicializa cliente com cache e retry.
        
        Args:
            cache_dir: Diretório para cache local
        """
        self.config = OpenMeteoConfig()
        
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
    
    def get_daily_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 7
    ) -> pd.DataFrame:
        """
        Busca previsão diária (com cache curto).
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            days: Dias de previsão (1-16, default 7)
            
        Returns:
            DataFrame com previsão
            
        Raises:
            ValueError: Se parâmetros inválidos
        """
        if not (1 <= days <= 16):
            raise ValueError(f"Days deve ser 1-16 (recebido: {days})")
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude inválida: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude inválida: {lon}")
        
        logger.info(f"📡 Forecast: {lat:.4f}, {lon:.4f} ({days} dias)")
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": self.config.DAILY_VARIABLES,
            "temperature_unit": "celsius",
            "wind_speed_unit": "ms",
            "precipitation_unit": "mm",
            "timezone": "UTC",
            "forecast_days": days,
            "models": "best_match"
        }
        
        try:
            responses = self.client.weather_api(self.config.FORECAST_URL, params=params)
            response = responses[0]
            
            # Parsear resposta
            df = self._parse_response(response)
            logger.info(f"✅ Forecast: {len(df)} dias obtidos")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro Forecast: {e}")
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
            self.get_daily_forecast(lat=0.0, lon=0.0, days=1)
            return True
        except Exception as e:
            logger.error(f"❌ Health check falhou: {e}")
            return False


# Exemplo de uso
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Archive (histórico) - Brasília
        archive = OpenMeteoArchiveClient()
        hist_data = archive.get_daily_data(
            lat=-15.7939,
            lon=-47.8828,
            start_date=datetime(2024, 9, 1),
            end_date=datetime(2024, 9, 30)
        )
        print(f"\n📊 Archive ({len(hist_data)} dias):")
        print(hist_data[["temperature_2m_mean", "et0_fao_evapotranspiration"]].head())
        
        # Forecast (previsão) - Brasília
        forecast = OpenMeteoForecastClient()
        pred_data = forecast.get_daily_forecast(
            lat=-15.7939,
            lon=-47.8828,
            days=7
        )
        print(f"\n📊 Forecast ({len(pred_data)} dias):")
        print(pred_data[["temperature_2m_mean", "et0_fao_evapotranspiration"]].head())
    
    asyncio.run(main())
