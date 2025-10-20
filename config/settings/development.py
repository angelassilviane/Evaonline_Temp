"""
Configurações específicas para ambiente de desenvolvimento.
"""
from typing import List

from .app_settings import Settings


class DevelopmentSettings(Settings):
    """Configurações específicas para desenvolvimento."""
    
    # Sobrescrever configurações para desenvolvimento
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Segurança relaxada para desenvolvimento
    ALLOWED_HOSTS: List[str] = ["*"]
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Performance ajustada para desenvolvimento
    CELERY_WORKER_CONCURRENCY: int = 2  # Menos workers em dev
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Cache menos agressivo
    CACHE_TTL: int = 60 * 30  # 30 minutos em desenvolvimento
    CACHE_ENABLED: bool = True  # Manter cache ativo para testar
    
    # Rate limiting relaxado
    RATE_LIMIT_REQUESTS: int = 1000  # 1000 requests por minuto
    RATE_LIMIT_ENABLED: bool = False  # Desativar rate limiting em dev
    
    # Logging mais verboso
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "console"
    
    # Monitoramento básico
    PROMETHEUS_ENABLED: bool = True
    
    # Recarregamento automático
    FASTAPI_RELOAD: bool = True
    DASH_DEBUG: bool = True
    
    class Config(Settings.Config):
        env_file = ".env.development"


def get_development_settings() -> DevelopmentSettings:
    """Retorna configurações de desenvolvimento."""
    return DevelopmentSettings()
