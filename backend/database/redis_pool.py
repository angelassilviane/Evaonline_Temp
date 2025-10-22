"""
Pool centralizado de conexões Redis com gerenciamento de ciclo de vida.

Benefício: Reutiliza conexões, evita esgotamento de recursos.
"""

import os
from typing import Optional

import redis
from loguru import logger

_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


def initialize_redis_pool() -> redis.Redis:
    """
    Inicializa pool de conexões Redis.

    Usa REDIS_URL da variável de ambiente ou padrão.

    Returns:
        Cliente Redis com pool
    """
    global _redis_pool, _redis_client

    if _redis_client is not None:
        return _redis_client

    redis_url = os.getenv(
        "REDIS_URL",
        "redis://:evaonline@redis:6379/0"
    )

    try:
        _redis_pool = redis.from_url(redis_url)
        _redis_client = _redis_pool

        # Teste de conexão
        _redis_client.ping()
        logger.info("✅ Redis pool initialized and connected")

        return _redis_client

    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise


def get_redis_client() -> redis.Redis:
    """
    Obtém cliente Redis com pool compartilhado.

    Inicializa se ainda não foi inicializado.

    Returns:
        Cliente Redis

    Raises:
        Exception: Se conexão falhar
    """
    global _redis_client

    if _redis_client is None:
        return initialize_redis_pool()

    return _redis_client


def close_redis() -> None:
    """Fecha pool de Redis e libera recursos."""
    global _redis_pool, _redis_client

    if _redis_client:
        try:
            _redis_client.close()
            logger.info("✅ Redis pool closed")
        except Exception as e:
            logger.warning(f"Error closing Redis: {e}")

    _redis_pool = None
    _redis_client = None
