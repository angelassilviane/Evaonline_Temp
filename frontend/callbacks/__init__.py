"""
Callbacks - Lógica de interação do Dash.
"""
import frontend.callbacks.cache_callbacks  # noqa: F401  (registers cache callbacks via decorators)
import frontend.callbacks.favorites_callbacks  # noqa: F401  (registers favorites callbacks via decorators)
import frontend.callbacks.language_callbacks  # noqa: F401  (registers language callbacks via decorators)
from frontend.callbacks.eto_callbacks import register_eto_callbacks
from frontend.callbacks.map_callbacks import register_map_callbacks
from frontend.callbacks.navigation_callbacks import register_navigation_callbacks

__all__ = [
    'register_navigation_callbacks',
    'register_map_callbacks',
    'register_eto_callbacks',
    # cache, favorites and language callbacks are registered by importing their modules
]
