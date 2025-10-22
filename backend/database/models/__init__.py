"""
Exporta todos os modelos de banco de dados.
"""
from .admin_user import AdminUser
from .climate_data import EToResults
from .user_cache import CacheMetadata, UserSessionCache
from .user_favorites import FavoriteLocation, UserFavorites
from .world_locations import EToWorldCache, WorldLocation

# Adicione outros modelos conforme necessário
__all__ = [
    'AdminUser',
    'EToResults',
    'WorldLocation',
    'EToWorldCache',
    'UserSessionCache',
    'CacheMetadata',
    'UserFavorites',
    'FavoriteLocation'
]
