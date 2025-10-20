"""
Configurações gerais da aplicação EVAonline - Otimizado para produção.
"""
import os
import secrets
from functools import lru_cache
from typing import Any, Dict, List

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação com validação rigorosa."""
    
    # =========================================================================
    # CONFIGURAÇÕES GERAIS
    # =========================================================================
    PROJECT_NAME: str = "EVAonline"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Segurança
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # =========================================================================
    # CONFIGURAÇÕES FASTAPI
    # =========================================================================
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:8050",
        "http://127.0.0.1:8050",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # Performance API
    API_MAX_CONNECTIONS: int = 100
    API_TIMEOUT: int = 30
    
    # =========================================================================
    # CONFIGURAÇÕES DASH
    # =========================================================================
    DASH_URL_BASE_PATHNAME: str = "/"
    DASH_ROUTES: Dict[str, str] = {
        "home": "/",
        "eto_calculator": "/eto", 
        "about": "/about",
        "documentation": "/documentation"
    }
    DASH_ASSETS_FOLDER: str = "frontend/assets"
    
    # Performance Dash
    DASH_COMPRESS_ASSETS: bool = True
    DASH_INCLUDE_ASSETS_FILES: bool = True
    
    # =========================================================================
    # CONFIGURAÇÕES BANCO DE DADOS (POSTGRESQL + POSTGIS)
    # =========================================================================
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "postgres")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "evaonline")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "123456")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "evaonline")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    
    # Connection Pooling
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600  # 1 hora
    DB_POOL_TIMEOUT: int = 30
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """URL de conexão do banco com connection pooling."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            f"?application_name=evaonline_api"
        )
    
    @property 
    def SQLALCHEMY_DATABASE_URI_ASYNC(self) -> str:
        """URL de conexão async para FastAPI."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            f"?application_name=evaonline_api_async"
        )
    
    # =========================================================================
    # CONFIGURAÇÕES REDIS (CACHE + CELERY)
    # =========================================================================
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "evaonline")
    
    # Redis Connection Pool
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 10
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    
    @property
    def REDIS_URL(self) -> str:
        """URL do Redis com configurações otimizadas."""
        return (
            f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            f"?socket_timeout={self.REDIS_SOCKET_TIMEOUT}"
            f"&socket_connect_timeout={self.REDIS_SOCKET_CONNECT_TIMEOUT}"
        )
    
    # =========================================================================
    # CONFIGURAÇÕES CELERY
    # =========================================================================
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    def __init__(self, **data):
        super().__init__(**data)
        self.CELERY_BROKER_URL = self.REDIS_URL
        self.CELERY_RESULT_BACKEND = self.REDIS_URL
    
    # Performance Celery
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300  # 5 minutos
    CELERY_TASK_TIME_LIMIT: int = 600  # 10 minutos
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_WORKER_SEND_TASK_EVENTS: bool = True
    CELERY_TASK_SEND_SENT_EVENT: bool = True
    
    # =========================================================================
    # CONFIGURAÇÕES CACHE
    # =========================================================================
    CACHE_TTL: int = 60 * 60 * 24  # 24 horas padrão
    CACHE_SHORT_TTL: int = 60 * 15  # 15 minutos para dados voláteis
    CACHE_LONG_TTL: int = 60 * 60 * 24 * 7  # 7 dias para dados estáticos
    
    # Cache strategies
    CACHE_ENABLED: bool = True
    CACHE_COMPRESSION: bool = True
    CACHE_KEY_PREFIX: str = "evaonline"
    
    # =========================================================================
    # CONFIGURAÇÕES EXTERNAS (APIs)
    # =========================================================================
    # Open-Meteo Elevation API
    OPEN_METEO_ELEVATION_URL: str = "https://api.open-meteo.com/v1/elevation"
    OPEN_METEO_TIMEOUT: int = 10
    OPEN_METEO_MAX_RETRIES: int = 3
    
    # NASA POWER API
    NASA_POWER_URL: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    NASA_POWER_TIMEOUT: int = 15
    
    # Rate Limiting para APIs externas
    EXTERNAL_API_RATE_LIMIT: int = 100  # requests por hora
    
    # =========================================================================
    # CONFIGURAÇÕES MONITORAMENTO
    # =========================================================================
    # Prometheus
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 8001
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json" if not DEBUG else "console"
    
    # Health Checks
    HEALTH_CHECK_ENDPOINT: str = "/health"
    READINESS_ENDPOINT: str = "/ready"
    
    # =========================================================================
    # CONFIGURAÇÕES SEGURANÇA
    # =========================================================================
    # CORS
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rate Limiting interno
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # requests por minuto
    RATE_LIMIT_WINDOW: int = 60  # 1 minuto
    
    # Validações
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """Valida e formata origens CORS."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        validate_assignment = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retorna configurações com cache para evitar múltiplas leituras.
    
    Returns:
        Settings: Instância das configurações
    """
    return Settings()


# Configurações específicas por ambiente
def get_database_config(settings: Settings) -> Dict[str, Any]:
    """Retorna configurações otimizadas para database."""
    return {
        "url": settings.SQLALCHEMY_DATABASE_URI,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "echo": settings.DEBUG,
        "echo_pool": settings.DEBUG,
    }


def get_redis_config(settings: Settings) -> Dict[str, Any]:
    """Retorna configurações otimizadas para Redis."""
    return {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "db": settings.REDIS_DB,
        "password": settings.REDIS_PASSWORD,
        "max_connections": settings.REDIS_MAX_CONNECTIONS,
        "socket_timeout": settings.REDIS_SOCKET_TIMEOUT,
        "socket_connect_timeout": settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        "retry_on_timeout": True,
        "health_check_interval": 30,
    }


def get_celery_config(settings: Settings) -> Dict[str, Any]:
    """Retorna configurações otimizadas para Celery."""
    return {
        "broker_url": settings.CELERY_BROKER_URL,
        "result_backend": settings.CELERY_RESULT_BACKEND,
        "worker_concurrency": settings.CELERY_WORKER_CONCURRENCY,
        "worker_prefetch_multiplier": (
            settings.CELERY_WORKER_PREFETCH_MULTIPLIER
        ),
        "task_soft_time_limit": settings.CELERY_TASK_SOFT_TIME_LIMIT,
        "task_time_limit": settings.CELERY_TASK_TIME_LIMIT,
        "task_acks_late": settings.CELERY_TASK_ACKS_LATE,
        "worker_send_task_events": settings.CELERY_WORKER_SEND_TASK_EVENTS,
        "task_send_sent_event": settings.CELERY_TASK_SEND_SENT_EVENT,
        "broker_connection_retry_on_startup": True,
    }
