import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from backend.core.config import Settings


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope='session')
def test_settings():
    # Use the new nested Settings structure
    return Settings(
        APP_NAME='EVAonline Tests',
        DEBUG=True,
        ENVIRONMENT='development',
        LOG_LEVEL='DEBUG',
    )

@pytest.fixture
def mock_redis():
    mock = Mock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    return mock

def pytest_configure(config):
    config.addinivalue_line('markers', 'unit: Unit tests')
    config.addinivalue_line('markers', 'integration: Integration tests')
    config.addinivalue_line('markers', 'api: API tests')
    config.addinivalue_line('markers', 'e2e: End-to-end tests')
    config.addinivalue_line('markers', 'slow: Slow running tests')


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and naming."""
    for item in items:
        # Mark API tests
        if "api" in item.nodeid.lower():
            item.add_marker(pytest.mark.api)

        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Mark slow tests
        if "slow" in item.keywords or "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
