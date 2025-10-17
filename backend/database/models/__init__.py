"""
Exporta todos os modelos de banco de dados.
"""
from .climate_data import EToResults
from .world_locations import EToWorldCache, WorldLocation

# Adicione outros modelos conforme necessário
__all__ = ['EToResults', 'WorldLocation', 'EToWorldCache']
