"""
Componente de barra de navegação para o aplicativo EVAOnline - Otimizado para produção.
"""
from functools import lru_cache
from typing import Dict, Optional

import dash_bootstrap_components as dbc
from dash import html
from loguru import logger


class NavbarManager:
    """Gerencia configurações e estado da navbar com cache."""
    
    def __init__(self):
        self._nav_cache = {}
        self._current_state = {}
    
    @lru_cache(maxsize=10)
    def get_nav_texts(self, lang: str = "en") -> Dict:
        """
        Retorna textos da navbar com cache.
        
        Args:
            lang: Idioma (en/pt)
            
        Returns:
            Dict: Textos traduzidos
        """
        texts = {
            "en": {
                "brand_name": "EVAonline",
                "brand_subtitle": "Reference Evapotranspiration Estimation Tool",
                "calculate_eto": "Calculate ET₀",
                "about": "About", 
                "documentation": "Docs",
                "current_language": "English",
                "switch_language": "Português",
                "home": "Home"
            },
            "pt": {
                "brand_name": "EVAonline", 
                "brand_subtitle": "Ferramenta de Estimativa de Evapotranspiração de Referência",
                "calculate_eto": "Calcular ET₀",
                "about": "Sobre",
                "documentation": "Documentação",
                "current_language": "Português",
                "switch_language": "English",
                "home": "Início"
            }
        }
        return texts.get(lang, texts["en"])
    
    def validate_settings(self, settings) -> bool:
        """
        Valida configurações necessárias para a navbar.
        
        Args:
            settings: Configurações da aplicação
            
        Returns:
            bool: True se configurações são válidas
        """
        required_routes = ["home", "eto_calculator", "about", "documentation"]
        
        if not hasattr(settings, 'DASH_ROUTES'):
            logger.error("Configurações não contém DASH_ROUTES")
            return False
        
        for route in required_routes:
            if route not in settings.DASH_ROUTES:
                logger.error(f"Rota necessária não encontrada: {route}")
                return False
        
        return True


# Instância global do gerenciador
navbar_manager = NavbarManager()


def render_navbar(settings, current_lang: str = 'en', enable_analytics: bool = True) -> dbc.Navbar:
    """
    Cria uma barra de navegação responsiva otimizada para produção.
    
    Args:
        settings: Configurações da aplicação
        current_lang: Código do idioma atual (en/pt)
        enable_analytics: Habilita atributos para analytics
        
    Returns:
        dbc.Navbar: Componente da barra de navegação otimizado
        
    Raises:
        ValueError: Se configurações forem inválidas
    """
    logger.debug(f"🔄 Renderizando navbar (idioma: {current_lang})")
    
    # Validar configurações
    if not navbar_manager.validate_settings(settings):
        raise ValueError("Configurações inválidas fornecidas para navbar")
    
    try:
        texts = navbar_manager.get_nav_texts(current_lang)
        
        return dbc.Navbar(
            dbc.Container([
                # Brand/Logo
                _create_brand_section(settings, texts, enable_analytics),
                
                # Navbar toggler para mobile
                dbc.NavbarToggler(
                    id="navbar-toggler", 
                    n_clicks=0,
                    className="border-0",
                    **{"data-toggle": "collapse", "data-target": "#navbar-collapse"}
                ),
                
                # Itens de navegação (colapsável)
                dbc.Collapse(
                    _create_nav_items(settings, texts, current_lang, enable_analytics),
                    id="navbar-collapse",
                    is_open=False,
                    navbar=True,
                    className="justify-content-end"
                ),
                
            ], fluid=True, className="px-3"),  # Padding lateral reduzido
            
            color="#2d5016",
            dark=True,
            className="mb-3 py-2 shadow-sm navbar-expand-lg",
            style={
                "minHeight": "70px",
                "transition": "all 0.3s ease",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
            },
            id="main-navbar",
            **{"data-version": "2.0", "data-role": "navigation"} if enable_analytics else {}
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao renderizar navbar: {e}")
        return _create_fallback_navbar(settings, current_lang)


def _create_brand_section(settings, texts: Dict, enable_analytics: bool) -> html.A:
    """Cria seção de brand/logo da navbar."""
    analytics_attrs = {
        "data-track": "brand-click",
        "data-category": "navigation"
    } if enable_analytics else {}
    
    return html.A(
        dbc.Row([
            # Logo (visível apenas em desktop)
            dbc.Col(
                html.Img(
                    src="assets/images/logo_esalq_2.png",
                    height="45px",
                    width="auto",
                    className="d-none d-md-block",
                    style={
                        "objectFit": "contain",
                        "maxHeight": "45px",
                        "transition": "transform 0.2s ease"
                    },
                    alt="ESALQ/USP Logo",
                    id="navbar-logo",
                    **{"data-role": "navbar-logo"}
                ),
                width="auto",
                className="pe-2"
            ),
            
            # Texto da marca
            dbc.Col(
                html.Div([
                    html.Span(
                        texts["brand_name"],
                        className="navbar-brand-text fw-bold",
                        style={
                            "fontSize": "22px",
                            "color": "white",
                            "lineHeight": "1.2",
                            "display": "block"
                        },
                        id="navbar-brand-text"
                    ),
                    html.Small(
                        texts["brand_subtitle"],
                        className="text-white-50 d-none d-sm-block",
                        style={
                            "fontSize": "11px",
                            "lineHeight": "1.1",
                            "display": "block",
                            "marginTop": "2px"
                        },
                        id="navbar-brand-subtitle"
                    )
                ], className="brand-text-container"),
                width="auto",
                className="d-flex align-items-center"
            )
        ], align="center", className="g-2 m-0"),
        
        href=settings.DASH_ROUTES["home"],
        className="navbar-brand p-0 me-0 me-lg-3",
        style={
            "textDecoration": "none",
            "flexShrink": 0
        },
        id="navbar-brand-link",
        **analytics_attrs
    )


def _create_nav_items(settings, texts: Dict, current_lang: str, enable_analytics: bool) -> dbc.Row:
    """Cria itens de navegação e controles."""
    analytics_attrs = {
        "data-track": "nav-click",
        "data-category": "navigation"
    } if enable_analytics else {}
    
    return dbc.Row([
        # Link: Calcular ETo
        dbc.Col(
            dbc.NavLink(
                html.Span([
                    html.I(
                        className="fas fa-calculator me-2",
                        style={"fontSize": "0.9em"}
                    ),
                    texts["calculate_eto"],
                    html.Sub("0", className="ms-1 opacity-75")
                ]),
                href=settings.DASH_ROUTES["eto_calculator"],
                className="nav-link-custom px-3 py-2",
                style={
                    "color": "white",
                    "borderRadius": "6px",
                    "transition": "all 0.2s ease",
                    "fontWeight": "500"
                },
                id="nav-eto-calculator",
                **analytics_attrs
            ),
            width="auto",
            className="pe-1"
        ),
        
        # Link: Sobre
        dbc.Col(
            dbc.NavLink(
                html.Span([
                    html.I(
                        className="fas fa-info-circle me-2", 
                        style={"fontSize": "0.9em"}
                    ),
                    texts["about"]
                ]),
                href=settings.DASH_ROUTES["about"],
                className="nav-link-custom px-3 py-2",
                style={
                    "color": "white",
                    "borderRadius": "6px", 
                    "transition": "all 0.2s ease",
                    "fontWeight": "500"
                },
                id="nav-about",
                **analytics_attrs
            ),
            width="auto", 
            className="pe-1"
        ),
        
        # Link: Documentação
        dbc.Col(
            dbc.NavLink(
                html.Span([
                    html.I(
                        className="fas fa-book me-2",
                        style={"fontSize": "0.9em"}
                    ),
                    texts["documentation"]
                ]),
                href=settings.DASH_ROUTES["documentation"],
                className="nav-link-custom px-3 py-2",
                style={
                    "color": "white",
                    "borderRadius": "6px",
                    "transition": "all 0.2s ease", 
                    "fontWeight": "500"
                },
                id="nav-documentation",
                **analytics_attrs
            ),
            width="auto",
            className="pe-3"
        ),
        
        # Seletor de idioma
        dbc.Col(
            dbc.Button(
                html.Span([
                    html.I(className="fas fa-globe me-2"),
                    texts["current_language"]
                ]),
                id="language-toggle",
                color="light",
                outline=True,
                size="sm",
                className="language-toggle-btn",
                style={
                    "color": "white",
                    "borderColor": "rgba(255,255,255,0.5)",
                    "backgroundColor": "transparent",
                    "transition": "all 0.2s ease",
                    "fontWeight": "500",
                    "fontSize": "14px"
                },
                **{"data-current-lang": current_lang}
            ),
            width="auto",
            className="d-flex align-items-center"
        )
        
    ], className="g-2 align-items-center", justify="end")


def _create_fallback_navbar(settings, current_lang: str) -> dbc.Navbar:
    """Cria navbar de fallback em caso de erro."""
    return dbc.Navbar(
        dbc.Container([
            html.A(
                html.Span("EVAonline", className="navbar-brand fw-bold"),
                href=settings.DASH_ROUTES.get("home", "/"),
                className="navbar-brand"
            ),
            dbc.NavbarToggler(id="navbar-toggler-fallback"),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavLink("Calculate ET₀", href=settings.DASH_ROUTES.get("eto_calculator", "/eto")),
                    dbc.NavLink("About", href=settings.DASH_ROUTES.get("about", "/about")),
                    dbc.NavLink("Docs", href=settings.DASH_ROUTES.get("documentation", "/documentation")),
                ], className="ms-auto"),
                id="navbar-collapse-fallback",
                navbar=True,
                is_open=False
            )
        ], fluid=True),
        color="#2d5016",
        dark=True,
        className="mb-3"
    )


def render_navbar_simple(settings, current_lang: str = 'en') -> dbc.NavbarSimple:
    """
    Versão simplificada da navbar para páginas específicas.
    
    Args:
        settings: Configurações da aplicação
        current_lang: Idioma atual
        
    Returns:
        dbc.NavbarSimple: Navbar simplificada
    """
    texts = navbar_manager.get_nav_texts(current_lang)
    
    nav_items = [
        dbc.NavItem(
            dbc.NavLink(
                texts["calculate_eto"],
                href=settings.DASH_ROUTES["eto_calculator"],
                id="simple-nav-eto"
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                texts["about"],
                href=settings.DASH_ROUTES["about"],
                id="simple-nav-about"
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                texts["documentation"], 
                href=settings.DASH_ROUTES["documentation"],
                id="simple-nav-docs"
            )
        ),
    ]
    
    language_menu = dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem(
                "English",
                id={'type': 'lang-select', 'lang': 'en'},
                **{"data-action": "language-switch"}
            ),
            dbc.DropdownMenuItem(
                "Português", 
                id={'type': 'lang-select', 'lang': 'pt'},
                **{"data-action": "language-switch"}
            ),
        ],
        nav=True,
        in_navbar=True,
        label=current_lang.upper(),
        className="language-dropdown",
        id="language-dropdown"
    )
    
    return dbc.NavbarSimple(
        children=nav_items + [language_menu],
        brand=html.Div([
            html.Span("EVAonline", className="fw-bold"),
            html.Small(
                " ET₀ Tool",
                className="text-white-50 d-none d-sm-inline"
            )
        ]),
        brand_href=settings.DASH_ROUTES["home"],
        color="#2d5016",
        dark=True,
        className="mb-3 shadow-sm",
        id="simple-navbar",
        **{"data-role": "simple-navigation"}
    )


def render_navbar_minimal(settings, current_lang: str = 'en') -> dbc.Navbar:
    """
    Versão minimalista da navbar para páginas de erro ou loading.
    
    Args:
        settings: Configurações da aplicação
        current_lang: Idioma atual
        
    Returns:
        dbc.Navbar: Navbar minimalista
    """
    return dbc.Navbar(
        dbc.Container([
            html.A(
                html.Span("EVAonline", className="navbar-brand fw-bold"),
                href=settings.DASH_ROUTES["home"],
                className="navbar-brand"
            ),
            dbc.NavbarToggler(id="minimal-navbar-toggler"),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavLink("Home", href=settings.DASH_ROUTES["home"]),
                ], className="ms-auto"),
                id="minimal-navbar-collapse",
                navbar=True
            )
        ]),
        color="#2d5016",
        dark=True,
        className="mb-3",
        id="minimal-navbar"
    )


# Funções de utilidade para callbacks e estado
def get_navbar_metadata() -> Dict:
    """Retorna metadados da navbar para analytics e debugging."""
    return {
        "manager_stats": {
            "cache_size": len(navbar_manager._nav_cache),
            "current_state": navbar_manager._current_state
        },
        "available_languages": ["en", "pt"],
        "version": "2.0"
    }


def update_navbar_state(state_key: str, state_value: any):
    """
    Atualiza estado interno da navbar.
    
    Args:
        state_key: Chave do estado
        state_value: Valor do estado
    """
    navbar_manager._current_state[state_key] = state_value
    logger.debug(f"Navbar state updated: {state_key} = {state_value}")


def clear_navbar_cache():
    """Limpa cache da navbar (útil para desenvolvimento)."""
    navbar_manager._nav_cache.clear()
    navbar_manager.get_nav_texts.cache_clear()
    logger.info("🗑️ Cache da navbar limpo")
