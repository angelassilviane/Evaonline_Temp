"""
Factory para carregar configurações baseado no ambiente.

Ordem de carregamento:
1. ENVIRONMENT env var (.env)
2. Seleciona a classe correta (DevelopmentSettings ou ProductionSettings)
3. Retorna configurações do ambiente apropriado
"""

import os
from functools import lru_cache

from .app_settings import Settings
from .development import DevelopmentSettings
from .production import ProductionSettings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retorna as configurações apropriadas para o ambiente.
    
    Lê a variável ENVIRONMENT do arquivo .env ou variáveis de ambiente
    e retorna a classe de configurações correspondente.
    
    Precedência:
    1. Variável de ambiente do SO (ENVIRONMENT)
    2. Arquivo .env (ENVIRONMENT)
    3. Padrão: development (segurança)
    
    Returns:
        Settings: Instância das configurações do ambiente apropriado
        - DevelopmentSettings se ENVIRONMENT=development
        - ProductionSettings se ENVIRONMENT=production
        - DevelopmentSettings caso contrário (segurança)
    """
    environment = os.getenv("ENVIRONMENT", "development").lower().strip()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "staging":
        # Staging usa production settings
        return ProductionSettings()
    else:
        # development ou qualquer outro = development (segurança)
        return DevelopmentSettings()


def get_database_url() -> str:
    """Retorna a URL do banco de dados do ambiente atual."""
    settings = get_settings()
    return settings.SQLALCHEMY_DATABASE_URI


def get_redis_url() -> str:
    """Retorna a URL do Redis do ambiente atual."""
    settings = get_settings()
    return settings.REDIS_URL


__all__ = [
    "Settings",
    "DevelopmentSettings",
    "ProductionSettings",
    "get_settings",
    "get_database_url",
    "get_redis_url",
]
