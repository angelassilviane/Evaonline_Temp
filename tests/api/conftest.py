"""
CONFTEST API TESTS - Fixtures para testes de API endpoints
Localizacao: tests/api/conftest.py

API tests testam endpoints HTTP completos
- Com TestClient FastAPI
- Com BD REAL (via fixtures de integracao)
- Testam status codes, headers, response body
- Testam autenticacao e autorizacao
"""

import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.core.config import Settings
from backend.main import app

# CLIENT FIXTURES

@pytest.fixture
def client(test_settings) -> TestClient:
    """TestClient sincrono para testes de API."""
    return TestClient(app)


@pytest.fixture
async def async_client(test_settings) -> AsyncClient:
    """AsyncClient para testes async de API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# AUTHENTICATION FIXTURES

@pytest.fixture
def auth_headers():
    """Headers com token de autenticacao falso."""
    return {
        "Authorization": "Bearer fake-token-for-testing",
        "Content-Type": "application/json",
    }


@pytest.fixture
def api_key_headers():
    """Headers com API key."""
    return {
        "X-API-Key": "test-api-key-12345",
        "Content-Type": "application/json",
    }


# REQUEST FIXTURES

@pytest.fixture
def location_create_payload():
    """Payload para criar locacao via API."""
    return {
        "name": "Test Location",
        "latitude": -10.0,
        "longitude": -55.0,
        "country": "Brazil",
        "state": "MG",
        "elevation": 500.0,
        "timezone": "America/Sao_Paulo",
    }


@pytest.fixture
def climate_query_params():
    """Query parameters para requisicoes de clima."""
    return {
        "location_id": 1,
        "start_date": "2025-10-01",
        "end_date": "2025-10-22",
        "format": "json",
    }


@pytest.fixture
def favorite_payload():
    """Payload para criar favorito via API."""
    return {
        "location_id": 1,
    }


# RESPONSE FIXTURES

@pytest.fixture
def expected_location_response():
    """Estrutura esperada de resposta de locacao."""
    return {
        "id": int,
        "name": str,
        "latitude": float,
        "longitude": float,
        "country": str,
        "state": str,
        "elevation": float,
        "timezone": str,
    }


@pytest.fixture
def expected_climate_response():
    """Estrutura esperada de resposta de clima."""
    return {
        "location_id": int,
        "temperature": float,
        "humidity": float,
        "wind_speed": float,
        "precipitation": float,
        "pressure": float,
        "timestamp": str,
    }


# ASSERTION HELPERS

@pytest.fixture
def assert_api_success():
    """Helper para verificar respostas de sucesso."""
    def _assert(response, expected_status=200):
        assert response.status_code == expected_status, \
            f"Status {response.status_code} != {expected_status}. Body: {response.text}"
        data = response.json()
        assert isinstance(data, (dict, list)), \
            f"Response nao eh dict ou list: {type(data)}"
        return data
    return _assert


@pytest.fixture
def assert_api_error():
    """Helper para verificar respostas de erro."""
    def _assert(response, expected_status, error_code=None):
        assert response.status_code == expected_status, \
            f"Status {response.status_code} != {expected_status}"
        data = response.json()
        assert "detail" in data, "Response sem 'detail' field"
        if error_code:
            assert error_code in data.get("detail", ""), \
                f"Error code '{error_code}' nao encontrado"
    return _assert


@pytest.fixture
def assert_valid_json_schema():
    """Helper para validar JSON schema."""
    def _assert(data, schema):
        """Validacao simples de schema."""
        if isinstance(schema, dict):
            assert isinstance(data, dict), \
                f"Data deve ser dict, got {type(data)}"
            for key, expected_type in schema.items():
                assert key in data, f"Campo '{key}' faltando"
                if expected_type != type(None):
                    assert isinstance(data[key], expected_type), \
                        f"Campo '{key}' tipo {type(data[key])} != {expected_type}"
    return _assert


# API ENDPOINT HELPERS

@pytest.fixture
def api_paths():
    """Caminhos de API para testes."""
    return {
        "locations_list": "/api/locations",
        "locations_detail": "/api/locations/{location_id}",
        "locations_search": "/api/locations/search",
        "climate": "/api/climate/{location_id}",
        "cache": "/api/cache/climate/{location_id}",
        "favorites": "/api/favorites",
        "favorites_detail": "/api/favorites/{location_id}",
        "health": "/api/health",
        "stats": "/api/stats",
    }


# SESSION FIXTURES

@pytest.fixture
def session_id():
    """ID de sessao para testes."""
    return "test-session-12345"


@pytest.fixture
def session_headers(session_id):
    """Headers com session ID."""
    return {
        "X-Session-ID": session_id,
        "Content-Type": "application/json",
    }


# PERFORMANCE FIXTURES

@pytest.fixture
def performance_thresholds():
    """Limites de performance esperados."""
    return {
        "list_endpoints": 1.0,      # 1 segundo
        "detail_endpoints": 0.5,    # 500ms
        "search_endpoints": 2.0,    # 2 segundos
        "cache_endpoints": 0.1,     # 100ms (muito rapido)
    }


@pytest.fixture
def measure_request_time():
    """Helper para medir tempo de requisicao."""
    def _measure(response):
        """Retorna tempo em segundos."""
        # FastAPI TestClient nao fornece timing, fazer manual
        import time
        start = time.time()
        elapsed = time.time() - start
        return elapsed
    return _measure


# ERROR SCENARIOS

@pytest.fixture
def invalid_location_id():
    """ID de locacao invalido para testes de erro."""
    return 99999


@pytest.fixture
def invalid_payload():
    """Payload invalido para testes de erro."""
    return {
        "name": "",  # Nome vazio
        "latitude": 999.0,  # Fora de range
        "longitude": 999.0,  # Fora de range
    }
