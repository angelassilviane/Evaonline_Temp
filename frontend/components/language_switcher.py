"""
Componente de seletor de idioma para o aplicativo EVAOnline.

Este componente fornece uma interface para mudar entre idiomas (Português e Inglês),
sincronizando com o store global 'language-store'.
"""
from typing import Optional

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
from loguru import logger

from utils.get_translations import get_translations


class LanguageSwitcherConfig:
    """Configuração e constantes para o seletor de idioma."""
    
    DEFAULT_LANGUAGE = "pt"
    SUPPORTED_LANGUAGES = {
        "pt": {"name": "Português", "flag": "🇧🇷"},
        "en": {"name": "English", "flag": "🇺🇸"}
    }
    COLORS = {
        "primary": "#2d5016",
        "success": "#28a745",
        "light": "#f8f9fa"
    }


def create_language_switcher() -> dbc.Row:
    """
    Cria o componente seletor de idioma com dropdown.
    
    O componente é sincronizado com 'language-store' que é gerenciado
    pela função register_language_callbacks() em language_manager.py
    
    Returns:
        dbc.Row: Componente de seletor de idioma pronto para integração
        
    Example:
        >>> switcher = create_language_switcher()
        >>> app.layout = dbc.Container([switcher, ...])
    """
    config = LanguageSwitcherConfig()
    
    options = [
        {
            "label": html.Span([
                html.Span(
                    config.SUPPORTED_LANGUAGES[lang]["flag"],
                    className="me-2",
                    style={"fontSize": "1.2em"}
                ),
                config.SUPPORTED_LANGUAGES[lang]["name"]
            ]),
            "value": lang
        }
        for lang in config.SUPPORTED_LANGUAGES.keys()
    ]
    
    return dbc.Col(
        dcc.Dropdown(
            id="language-dropdown",
            options=options,
            value=config.DEFAULT_LANGUAGE,
            clearable=False,
            searchable=False,
            className="language-dropdown-select",
            style={
                "minWidth": "140px",
                "maxWidth": "200px",
                "fontSize": "14px",
                "backgroundColor": "#f8f9fa",
                "borderRadius": "6px",
                "borderColor": "rgba(0,0,0,0.1)",
                "color": "black"
            },
            # Customizar o dropdown aberto
            menuclassName="language-dropdown-menu"
        ),
        width="auto",
        className="d-flex align-items-center ms-2",
        id="language-switcher-container"
    )


def create_language_button(current_lang: str = "pt") -> dbc.Button:
    """
    Cria um botão simples para exibir/alternar idioma.
    
    Alternativa mais compacta ao dropdown - útil para navbars compactas.
    
    Args:
        current_lang: Idioma atual (pt/en)
        
    Returns:
        dbc.Button: Botão de idioma com ícone e texto
    """
    config = LanguageSwitcherConfig()
    lang_info = config.SUPPORTED_LANGUAGES[current_lang]
    
    return dbc.Button(
        html.Span([
            html.Span(lang_info["flag"], className="me-2", style={"fontSize": "1.1em"}),
            html.Span(
                lang_info["name"],
                className="d-none d-sm-inline",
                style={"fontSize": "14px", "fontWeight": "500"}
            )
        ]),
        id="language-button",
        color="light",
        outline=True,
        size="sm",
        className="language-button-custom",
        style={
            "color": "white",
            "borderColor": "rgba(255,255,255,0.5)",
            "backgroundColor": "transparent",
            "transition": "all 0.2s ease",
            "fontWeight": "500",
            "whiteSpace": "nowrap"
        },
        **{"data-current-lang": current_lang}
    )


def create_language_selector_modal() -> dbc.Modal:
    """
    Cria um modal para seleção visual de idioma.
    
    Fornece uma interface modal com opções de idioma apresentadas
    de forma visual (com bandeiras e nomes).
    
    Returns:
        dbc.Modal: Modal de seleção de idioma
    """
    config = LanguageSwitcherConfig()
    
    return dbc.Modal(
        [
            dbc.ModalHeader(
                html.Span([
                    html.I(className="fas fa-language me-2"),
                    "Select Language"
                ]),
                close_button=True,
                className="bg-light"
            ),
            dbc.ModalBody(
                dbc.Row([
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody([
                                html.Div(
                                    config.SUPPORTED_LANGUAGES[lang]["flag"],
                                    style={
                                        "fontSize": "48px",
                                        "textAlign": "center",
                                        "marginBottom": "10px"
                                    }
                                ),
                                html.H5(
                                    config.SUPPORTED_LANGUAGES[lang]["name"],
                                    className="text-center fw-bold",
                                    style={"color": "#2d5016"}
                                ),
                                dbc.Button(
                                    "Select",
                                    id={"type": "lang-modal-select", "lang": lang},
                                    color="primary",
                                    className="w-100 mt-2",
                                    size="sm"
                                )
                            ]),
                            className="border-0 shadow-sm",
                            style={
                                "cursor": "pointer",
                                "transition": "all 0.2s ease",
                                "border": f"2px solid {config.COLORS['light']}"
                            },
                            id={"type": "lang-card", "lang": lang}
                        ),
                        md=6,
                        className="mb-3"
                    )
                    for lang in config.SUPPORTED_LANGUAGES.keys()
                ], className="g-3")
            )
        ],
        id="language-selector-modal",
        size="lg",
        centered=True,
        is_open=False,
        className="language-modal"
    )


def get_language_display_text(lang: str = "pt") -> str:
    """
    Obtém o texto de exibição para o idioma.
    
    Args:
        lang: Código do idioma (pt/en)
        
    Returns:
        str: Nome do idioma em seu próprio idioma
    """
    config = LanguageSwitcherConfig()
    return config.SUPPORTED_LANGUAGES.get(
        lang,
        config.SUPPORTED_LANGUAGES[config.DEFAULT_LANGUAGE]
    )["name"]


def register_language_display_callbacks(app):
    """
    Registra callbacks para atualizar a exibição de idioma na UI.
    
    Este callback complementa o callback principal de language_manager.py,
    atualizando elementos visuais que mostram o idioma atual.
    
    Args:
        app: Instância Dash do aplicativo
    """
    
    @callback(
        Output("language-dropdown", "value"),
        Input("language-store", "data"),
        State("language-dropdown", "value"),
        prevent_initial_call=True
    )
    def sync_dropdown_with_store(stored_lang, current_dropdown):
        """Sincroniza dropdown com language-store."""
        if stored_lang:
            return stored_lang
        return current_dropdown or LanguageSwitcherConfig.DEFAULT_LANGUAGE
    
    logger.info("✅ Language display callbacks registered")


def create_language_badge(lang: str = "pt") -> dbc.Badge:
    """
    Cria um badge visual para exibir o idioma atual.
    
    Útil para mostrar em sidebars ou outras áreas compactas.
    
    Args:
        lang: Código do idioma (pt/en)
        
    Returns:
        dbc.Badge: Badge com informação do idioma
    """
    config = LanguageSwitcherConfig()
    lang_info = config.SUPPORTED_LANGUAGES[lang]
    
    return dbc.Badge(
        html.Span([
            html.Span(lang_info["flag"], className="me-2"),
            lang_info["name"]
        ]),
        color="info",
        className="language-badge",
        pill=True,
        style={
            "fontSize": "12px",
            "fontWeight": "600",
            "cursor": "pointer",
            "transition": "all 0.2s ease"
        },
        id="language-badge"
    )


def get_language_selector_info() -> dict:
    """
    Retorna informações sobre o seletor de idioma.
    
    Útil para debugging e documentação.
    
    Returns:
        dict: Metadados do seletor de idioma
    """
    config = LanguageSwitcherConfig()
    
    return {
        "default_language": config.DEFAULT_LANGUAGE,
        "supported_languages": list(config.SUPPORTED_LANGUAGES.keys()),
        "languages_info": config.SUPPORTED_LANGUAGES,
        "component_ids": [
            "language-dropdown",
            "language-button",
            "language-store",
            "language-selector-modal",
            "language-badge"
        ],
        "version": "1.0"
    }


# Estilos CSS inline para o seletor de idioma (podem ser movidos para arquivo CSS)
LANGUAGE_SWITCHER_STYLES = """
/* Dropdown de idioma */
#language-dropdown {
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
    font-weight: 500 !important;
}

#language-dropdown:hover {
    background-color: #e9ecef !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
}

.language-dropdown-menu {
    border-radius: 6px !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
}

/* Botão de idioma */
.language-button-custom:hover {
    background-color: rgba(255,255,255,0.2) !important;
    border-color: rgba(255,255,255,0.8) !important;
}

/* Badge de idioma */
.language-badge {
    cursor: pointer;
    transition: all 0.2s ease;
}

.language-badge:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* Container do seletor */
#language-switcher-container {
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(-5px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
"""
