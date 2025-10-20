"""
Configurações específicas para ambiente de produção.
"""
import os
from typing import List

from .app_settings import Settings


class ProductionSettings(Settings):
    """Configurações específicas para produção."""
    
    # Sobrescrever configurações para produção
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Segurança reforçada
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production-with-strong-key")
    ALLOWED_HOSTS: List[str] = [
        "evaonline.example.com",  # Substituir pelo domínio real
        "api.evaonline.example.com",
    ]
    
    # CORS restrito em produção
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://evaonline.example.com",  # Substituir pelo domínio real
    ]
    
    # Database com SSL
    POSTGRES_SSL_MODE: str = "require"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """URL de conexão com SSL em produção."""
        base_url = super().SQLALCHEMY_DATABASE_URI
        return f"{base_url}&sslmode={self.POSTGRES_SSL_MODE}"
    
    # Redis com SSL se disponível
    REDIS_SSL: bool = True
    REDIS_SSL_CERT_REQS: str = "required"
    
    # Performance otimizada
    CELERY_WORKER_CONCURRENCY: int = 8  # Mais workers em produção
    DB_POOL_SIZE: int = 25
    DB_MAX_OVERFLOW: int = 50
    
    # Cache mais agressivo
    CACHE_TTL: int = 60 * 60 * 24 * 3  # 3 dias em produção
    CACHE_ENABLED: bool = True
    
    # Rate limiting mais restritivo
    RATE_LIMIT_REQUESTS: int = 200  # 200 requests por minuto
    EXTERNAL_API_RATE_LIMIT: int = 500  # 500 requests por hora
    
    # Logging estruturado
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoramento ativo
    PROMETHEUS_ENABLED: bool = True
    
    class Config(Settings.Config):
        env_file = ".env.production"


def get_production_settings() -> ProductionSettings:
    """Retorna configurações de produção."""
    return ProductionSettings()
