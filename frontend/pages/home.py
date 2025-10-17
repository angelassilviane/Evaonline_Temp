"""
Página inicial do EVAonline com mapas interativos em abas.

Sistema de tabs seguindo documentação oficial dbc.Tabs:
- Tab 1: Mapa Leaflet (calcular ETo)
- Tab 2: Mapa Plotly com 6.738 cidades (explorar)
"""
import dash_bootstrap_components as dbc
from dash import html

# Importar layout do mapa mundial com tabs
from frontend.components.world_map_tabs import create_world_map_layout


def home_layout() -> html.Div:
    """
    Cria o layout da página inicial com mapa mundial interativo.
    
    Sistema de tabs (padrão oficial dbc.Tabs):
    - Tab 1: Mapa Leaflet interativo (clique para calcular ETo)
    - Tab 2: Mapa Plotly com 6.738 cidades pré-carregadas
    
    Returns:
        html.Div: Layout completo com tabs, geolocalização e favoritos
    """
    return create_world_map_layout()
