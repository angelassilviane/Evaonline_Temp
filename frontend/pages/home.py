"""
Página inicial do EVAonline com mapa mundial interativo.

Features:
- Mapa Leaflet interativo com camadas GeoJSON (Brasil, MATOPIBA)
- Marcador especial: Piracicaba - ESALQ/USP
- LocateControl para geolocalização
- LayersControl para gerenciar camadas
"""
import dash_bootstrap_components as dbc
from dash import html

# Importar layout do mapa mundial com tabs
from frontend.components.world_map_tabs import create_world_map_layout


def home_layout() -> html.Div:
    """
    Cria o layout da página inicial com mapa mundial interativo.
    
    Inclui:
    - Mapa Leaflet interativo (clique para calcular ETo)
    - Camadas GeoJSON (Brasil verde, MATOPIBA azul)
    - Marcador especial: Piracicaba/ESALQ
    - LocateControl (geolocalização)
    - LayersControl (gerenciar camadas)
    
    Returns:
        html.Div: Layout completo com mapa interativo e funcionalidades
    """
    return create_world_map_layout()
