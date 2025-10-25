"""
Callbacks da página ETo - Cálculos e integração com WebSocket em tempo real.

NOTA: A maioria dos callbacks antigos foram removidos.
Use eto_v3_callbacks.py para callbacks da calculadora ETo.
Use map_callbacks.py para callbacks de ações do mapa.
Este arquivo está aqui para compatibilidade futura.
"""
import dash
from loguru import logger

# Configurar logging
logger.enable("frontend.callbacks.eto_callbacks")


def register_eto_callbacks(app: dash.Dash):
    """
    Registra callbacks relacionados à página ETo.
    
    NOTA: Callbacks foram movidos para:
    - map_callbacks.py: Ações rápidas do mapa (navegação)
    - eto_v3_callbacks.py: Callbacks da calculadora ETo
    
    Args:
        app: Instância do aplicativo Dash
    """
    logger.info("✅ Callbacks da página ETo registrados (vazio - lógica em outros módulos)")
