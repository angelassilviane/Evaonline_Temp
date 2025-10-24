"""
CONFTEST INTEGRATION TESTS - Fixtures para testes de integracao
Localizacao: tests/integration/conftest.py

Integration tests REAIS - banco de dados REAL, Redis REAL
- Com banco de dados PostgreSQL REAL
- Com Redis REAL
- Sem APIs externas (mockadas)
- Testes mais lentos (segundos)
- Cleanup automático (rollback)
"""

import asyncio
from datetime import datetime
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import Settings
from backend.database.connection import Base

# DATABASE FIXTURES

@pytest.fixture(scope="session")
def integration_db_engine(test_settings):
    """Engine para testes de integracao - REAL PostgreSQL."""
    engine = create_engine(
        test_settings.database.database_url,
        echo=False,
        pool_pre_ping=True,
    )

    # Criar schema
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def integration_db_session(integration_db_engine) -> Generator[Session, None, None]:
    """Session de BD para cada teste - com rollback automatico."""
    connection = integration_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()


# REDIS FIXTURES

@pytest.fixture(scope="function")
async def redis_client(test_settings):
    """Cliente Redis REAL para testes de integracao."""
    import redis.asyncio as redis

    client = await redis.from_url(test_settings.redis.redis_url)
    yield client

    # Cleanup - limpar tudo
    await client.flushdb()
    await client.close()


@pytest.fixture(scope="function")
def redis_sync_client(test_settings):
    """Cliente Redis REAL síncrono para testes."""
    import redis

    client = redis.from_url(test_settings.redis.redis_url)
    yield client

    # Cleanup
    client.flushdb()
    client.close()


# DATABASE DATA FIXTURES

@pytest.fixture
def sample_location_dict():
    """Dados de locacao para fixtures de integracao."""
    return {
        "name": "Sao Paulo",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "country": "Brazil",
        "state": "SP",
        "elevation": 760.0,
        "timezone": "America/Sao_Paulo",
    }


@pytest.fixture
def sample_user_dict():
    """Dados de usuario para fixtures de integracao."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_climate_dict():
    """Dados de clima para fixtures de integracao."""
    return {
        "temperature": 25.5,
        "humidity": 65.0,
        "wind_speed": 10.2,
        "precipitation": 0.0,
        "pressure": 1013.25,
        "timestamp": datetime.utcnow(),
    }


# CACHE FIXTURES

@pytest.fixture
async def cache_populated(redis_client):
    """Populatr cache Redis com dados de teste."""
    # Cache de clima
    await redis_client.set(
        "climate:1:2025-10-22",
        '{"temperature": 25.5, "humidity": 65}',
        ex=3600,
    )

    # Cache de locacoes
    await redis_client.set(
        "locations:all",
        '[{"id": 1, "name": "Sao Paulo"}]',
        ex=86400,
    )

    yield redis_client

    # Cleanup automático (fixture acima faz flushdb)


# SERVICE FIXTURES

@pytest.fixture
def climate_service_mock():
    """Mock de ClimateService para testes de integracao."""
    from unittest.mock import Mock
    mock = Mock()
    mock.get_latest = Mock(return_value={
        "temperature": 25.5,
        "humidity": 65.0,
    })
    return mock


@pytest.fixture
def cache_service_mock(redis_sync_client):
    """Mock simples de CacheService."""
    from unittest.mock import Mock
    mock = Mock()
    mock.get = Mock(return_value=None)
    mock.set = Mock(return_value=True)
    return mock


@pytest.fixture
def favorites_service_mock():
    """Mock de FavoritesService para testes de integracao."""
    from unittest.mock import Mock
    mock = Mock()
    mock.add_favorite = Mock(return_value=True)
    mock.is_favorite = Mock(return_value=False)
    return mock


# HELPERS

@pytest.fixture
def execute_sql_query(integration_db_session):
    """Helper para executar queries SQL diretas."""
    def _execute(query_string):
        result = integration_db_session.execute(text(query_string))
        return result.fetchall()
    return _execute


@pytest.fixture
async def verify_cache_data(redis_client):
    """Helper para verificar dados no cache."""
    async def _verify(key, expected_value=None):
        cached = await redis_client.get(key)
        assert cached is not None, f"Cache key '{key}' nao encontrado"
        if expected_value:
            if isinstance(expected_value, dict):
                import json
                actual = json.loads(cached)
                assert actual == expected_value
        return cached
    return _verify


@pytest.fixture
def transaction_context(integration_db_session):
    """Context manager para testar transacoes."""
    class TransactionContext:
        def __init__(self, session):
            self.session = session

        def __enter__(self):
            self.session.begin_nested()
            return self.session

        def __exit__(self, *args):
            if args[0] is None:  # Sem exception
                self.session.commit()
            else:
                self.session.rollback()

    return TransactionContext(integration_db_session)
