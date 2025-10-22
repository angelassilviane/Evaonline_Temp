"""
Callbacks para controle de idioma da aplicação.
"""
from dash import Input, Output, State, callback, no_update
from loguru import logger


@callback(
    Output("language-toggle", "children"),
    Output("url", "pathname", allow_duplicate=True),
    Input("language-toggle", "n_clicks"),
    State("language-toggle", "data-current-lang"),
    prevent_initial_call=True,
)
def toggle_language(n_clicks: int, current_lang: str):
    """
    Toggle entre inglês e português.
    
    Args:
        n_clicks: Número de cliques no botão
        current_lang: Idioma atual armazenado no atributo data
        
    Returns:
        tuple: (novo children do botão, pathname para refresh)
    """
    if not n_clicks or n_clicks == 0:
        return no_update, no_update
    
    try:
        # Toggle lang
        new_lang = "pt" if current_lang == "en" else "en"
        
        texts = {
            "en": "English",
            "pt": "Português"
        }
        
        new_text = texts.get(new_lang, "English")
        
        logger.info(f"🌐 Idioma alterado: {current_lang} → {new_lang}")
        
        # Retorna novo texto e refresh página
        return new_text, no_update
        
    except Exception as e:
        logger.error(f"❌ Erro ao alternar idioma: {e}")
        return no_update, no_update
