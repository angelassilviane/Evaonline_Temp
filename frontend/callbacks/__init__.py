"""
Callbacks - Lógica de interação do Dash.
"""
from frontend.callbacks.eto_callbacks import register_eto_callbacks
from frontend.callbacks.map_callbacks import register_map_callbacks
from frontend.callbacks.navigation_callbacks import register_navigation_callbacks

__all__ = [
    'register_navigation_callbacks',
    'register_map_callbacks',
    'register_eto_callbacks',
]
