"""
===========================================
PYTEST CONFIGURATION - EVAonline
===========================================
Configuração compartilhada de fixtures para todos os testes.
"""

import os
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Configurar variáveis de ambiente para testes
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "eva online_test")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "1")  # Database separado para testes


# ===========================================
# Fixtures Globais
# ===========================================


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Retorna o diretório de dados de teste."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def test_output_dir() -> Path:
    """Retorna o diretório de saída de testes."""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture(autouse=True)
def reset_test_environment():
    """
    Reseta o ambiente de teste antes de cada teste.
    autouse=True significa que roda automaticamente.
    """
    # Limpar variáveis de ambiente de teste se necessário
    yield
    # Cleanup após o teste se necessário


# ===========================================
# Markers Customizados
# ===========================================


def pytest_configure(config):
    """Registra marcadores customizados."""
    config.addinivalue_line(
        "markers", "unit: Testes unitários rápidos"
    )
    config.addinivalue_line(
        "markers", "integration: Testes de integração com serviços externos"
    )
    config.addinivalue_line(
        "markers", "api: Testes de API/endpoints"
    )
    config.addinivalue_line(
        "markers", "slow: Testes lentos"
    )
    config.addinivalue_line(
        "markers", "database: Testes que requerem banco de dados"
    )
    config.addinivalue_line(
        "markers", "redis: Testes que requerem Redis"
    )
    config.addinivalue_line(
        "markers", "celery: Testes que requerem Celery"
    )
    config.addinivalue_line(
        "markers", "docker: Testes que requerem Docker"
    )
    config.addinivalue_line(
        "markers", "e2e: Testes end-to-end"
    )
    config.addinivalue_line(
        "markers", "smoke: Testes de smoke (quick sanity checks)"
    )


# ===========================================
# Fixtures de Mock/Fake Data
# ===========================================


@pytest.fixture
def sample_coordinates():
    """Retorna coordenadas de exemplo para testes."""
    return {
        "latitude": -15.7801,
        "longitude": -47.9292,
        "name": "Brasília, DF"
    }


@pytest.fixture
def sample_weather_data():
    """Retorna dados meteorológicos de exemplo para testes."""
    return {
        "temperature": 25.0,
        "humidity": 60.0,
        "wind_speed": 2.5,
        "solar_radiation": 20.0,
        "pressure": 1013.25,
        "precipitation": 0.0
    }


@pytest.fixture
def sample_eto_input():
    """Retorna dados de entrada para cálculo ETo."""
    return {
        "date": "2025-01-14",
        "latitude": -15.7801,
        "altitude": 1000.0,
        "tmax": 30.0,
        "tmin": 20.0,
        "radiation": 20.0,
        "wind_speed": 2.0,
        "humidity_max": 80.0,
        "humidity_min": 40.0
    }


# ===========================================
# Hooks para Relatórios
# ===========================================


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook para capturar resultados de testes e adicionar informações extras.
    """
    outcome = yield
    report = outcome.get_result()
    
    # Adicionar informações extras em caso de falha
    if report.when == "call" and report.failed:
        # Capturar informações do ambiente
        report.sections.append(("Environment", f"""
            Python: {os.sys.version}
            Working Directory: {os.getcwd()}
            Test: {item.nodeid}
        """))


def pytest_collection_modifyitems(config, items):
    """
    Modifica itens coletados para adicionar marcadores automáticos.
    """
    for item in items:
        # Adicionar marcador 'slow' automaticamente para testes > 1s
        if "slow" not in item.keywords:
            # Marcar testes de integração como slow por padrão
            if "integration" in item.keywords:
                item.add_marker(pytest.mark.slow)
