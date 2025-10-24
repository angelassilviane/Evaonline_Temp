"""
CONFTEST UNIT TESTS - Fixtures para testes unitarios
Localizacao: tests/unit/conftest.py

Unit tests sao ISOLADOS - tudo é mockado
- Sem banco de dados
- Sem Redis
- Sem APIs externas
- Testes rapidos (ms)
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


# Mocks de repositorios
@pytest.fixture
def mock_location_repo():
    """Mock do LocationRepository."""
    mock = Mock()
    mock.get_by_id = Mock(return_value={
        "id": 1,
        "name": "Sao Paulo",
        "latitude": -23.5505,
        "longitude": -46.6333,
    })
    mock.list_all = Mock(return_value=[
        {"id": 1, "name": "Sao Paulo"},
        {"id": 2, "name": "Rio de Janeiro"},
    ])
    mock.create = Mock(return_value={"id": 3, "name": "Brasilia"})
    return mock


@pytest.fixture
def mock_climate_repo():
    """Mock do ClimateRepository."""
    mock = Mock()
    mock.get_latest = Mock(return_value={
        "location_id": 1,
        "temperature": 25.5,
        "humidity": 65,
        "timestamp": datetime.utcnow().isoformat(),
    })
    mock.save = Mock(return_value=True)
    return mock


@pytest.fixture
def mock_cache_service():
    """Mock do CacheService."""
    mock = Mock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    return mock


@pytest.fixture
def mock_external_api():
    """Mock para chamadas HTTP externas."""
    mock = Mock()
    mock.get = Mock(return_value=Mock(
        status_code=200,
        json=lambda: {
            "properties": [{"time": "2025-10-22", "values": [25.5, 65]}]
        }
    ))
    mock.post = Mock(return_value=Mock(status_code=201))
    return mock


# Mocks de dependencias
@pytest.fixture
def mock_celery_task():
    """Mock para Celery tasks."""
    with patch('backend.api.routes.climate_download.download_climate_data.delay') as mock:
        mock.return_value = MagicMock(id="task-123")
        yield mock


@pytest.fixture
def mock_env_vars():
    """Mock de variaveis de ambiente."""
    with patch.dict('os.environ', {
        'ENVIRONMENT': 'test',
        'DEBUG': 'True',
        'API_TITLE': 'EVAonline Tests',
    }):
        yield


# Fixtures de dados
@pytest.fixture
def location_data():
    """Dados de locacao para unit tests."""
    return {
        "id": 1,
        "name": "Sao Paulo",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "country": "Brazil",
        "state": "SP",
        "elevation": 760.0,
        "timezone": "America/Sao_Paulo",
    }


@pytest.fixture
def climate_data():
    """Dados de clima para unit tests."""
    return {
        "location_id": 1,
        "temperature": 25.5,
        "humidity": 65.0,
        "wind_speed": 10.2,
        "precipitation": 0.0,
        "pressure": 1013.25,
        "timestamp": datetime.utcnow(),
    }


@pytest.fixture
def user_data():
    """Dados de usuario para unit tests."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
    }


@pytest.fixture
def favorite_data():
    """Dados de favorito para unit tests."""
    return {
        "id": 1,
        "user_id": 1,
        "location_id": 1,
        "created_at": datetime.utcnow(),
    }


# Fixtures de assertions
@pytest.fixture
def assert_valid_location():
    """Helper para validar estrutura de locacao."""
    def _validate(data):
        required_fields = ["id", "name", "latitude", "longitude"]
        assert all(field in data for field in required_fields), \
            f"Location faltam campos: {required_fields}"
        assert isinstance(data["latitude"], (int, float)), \
            "latitude deve ser numero"
        assert isinstance(data["longitude"], (int, float)), \
            "longitude deve ser numero"
    return _validate


@pytest.fixture
def assert_valid_climate():
    """Helper para validar estrutura de clima."""
    def _validate(data):
        required_fields = ["location_id", "temperature", "humidity"]
        assert all(field in data for field in required_fields), \
            f"Climate faltam campos: {required_fields}"
        assert isinstance(data["temperature"], (int, float)), \
            "temperature deve ser numero"
    return _validate


# Fixtures de comparacao
@pytest.fixture
def tolerance():
    """Tolerancia para comparacoes de floats."""
    return {
        "temperature": 0.1,  # ±0.1°C
        "humidity": 1.0,      # ±1%
        "pressure": 0.5,      # ±0.5 hPa
    }


@pytest.fixture
def timestamps():
    """Timestamps para unit tests."""
    now = datetime.utcnow()
    return {
        "now": now,
        "yesterday": now - timedelta(days=1),
        "tomorrow": now + timedelta(days=1),
        "week_ago": now - timedelta(days=7),
    }


# ============================================================================
# FIXTURES DO BACKEND/TESTS/CONFTEST.PY - CONSOLIDADAS
# ============================================================================

@pytest.fixture(scope="session")
def sample_coordinates():
    """Session-scoped fixture providing sample coordinates for testing."""
    return {
        "jaú_sp": (-22.2964, -48.5578),
        "são_paulo_sp": (-23.5505, -46.6333),
        "rio_de_janeiro_rj": (-22.9068, -43.1729),
        "brasília_df": (-15.7942, -47.8822)
    }


@pytest.fixture(scope="session")
def sample_date_ranges():
    """Session-scoped fixture providing common date ranges for testing."""
    today = datetime.utcnow()
    return {
        "today": (today, today + timedelta(days=1)),
        "yesterday": (today - timedelta(days=1), today),
        "last_week": (today - timedelta(days=7), today),
        "last_month": (today - timedelta(days=30), today),
        "forecast_range": (today - timedelta(days=2), today + timedelta(days=5))
    }


@pytest.fixture
def mock_api_response_success(sample_date_ranges):
    """Fixture providing a successful API response with dynamic dates."""
    start, end = sample_date_ranges["forecast_range"]

    timestamps = []
    current = start
    while current <= end:
        timestamps.append(current.strftime("%Y-%m-%dT%H:%M:%S"))
        current += timedelta(hours=1)
        if len(timestamps) >= 4:
            break

    return {
        "latitude": -22.2964,
        "longitude": -48.5578,
        "generationtime_ms": 0.5,
        "utc_offset_seconds": -10800,
        "timezone": "America/Sao_Paulo",
        "timezone_abbreviation": "BRT",
        "hourly": {
            "time": timestamps,
            "temperature_2m": [20.5, 19.8, 18.9, 18.2],
            "relative_humidity_2m": [65, 70, 75, 80],
            "et0_fao_evapotranspiration": [0.15, 0.12, 0.08, 0.05],
            "wind_speed_10m": [15.2, 12.8, 18.5, 14.3],
            "shortwave_radiation": [0, 0, 120, 250],
            "precipitation_probability": [10, 15, 20, 25]
        }
    }


@pytest.fixture
def mock_api_response_incomplete(sample_date_ranges):
    """Fixture providing an API response with missing fields and dynamic dates."""
    start, _ = sample_date_ranges["forecast_range"]

    return {
        "hourly": {
            "time": [start.strftime("%Y-%m-%dT%H:%M:%S")],
            "temperature_2m": [20.5],
        }
    }


@pytest.fixture
def mock_api_response_empty():
    """Fixture providing an empty API response."""
    return {}


@pytest.fixture
def mock_redis_client():
    """Fixture providing a mock Redis client."""
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    return mock_client


@pytest.fixture
def sample_dataframe():
    """Fixture providing a sample DataFrame similar to API output."""
    import pandas as pd
    dates = pd.date_range("2025-09-01", periods=4, freq="H")
    return pd.DataFrame({
        "T2M": [20.5, 19.8, 18.9, 18.2],
        "RH2M": [65, 70, 75, 80],
        "ETO": [0.15, 0.12, 0.08, 0.05],
        "WS2M": [54.7, 46.1, 66.6, 51.5],
        "ALLSKY_SFC_SW_DWN": [0, 0, 120, 250],
        "PRECIP_PROB": [10, 15, 20, 25]
    }, index=dates)


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    """Automatically disable network calls for all tests."""
    def mock_get(*args, **kwargs):
        raise RuntimeError("Network call not mocked! Use @patch or fixtures.")

    monkeypatch.setattr("requests.get", mock_get)


@pytest.fixture(autouse=True)
def mock_redis_for_all_tests(monkeypatch):
    """Mock Redis for all tests to avoid connection errors."""
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.setex.return_value = True

    def mock_from_url(*args, **kwargs):
        return mock_client

    monkeypatch.setattr(
        "backend.api.services.openmeteo.Redis.from_url",
        mock_from_url
    )
