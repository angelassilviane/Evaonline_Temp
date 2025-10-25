"""
Configuração e criação do aplicativo Dash para produção.
"""
import os
import sys
from typing import Union

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html
from loguru import logger

from config.settings import get_settings
from frontend.callbacks.eto_callbacks import register_eto_callbacks
from frontend.callbacks.eto_v3_callbacks import register_eto_v3_callbacks
from frontend.callbacks.map_callbacks import register_map_callbacks
from frontend.callbacks.navigation_callbacks import register_navigation_callbacks
from frontend.components.footer import render_footer
from frontend.components.navbar import render_navbar
from frontend.pages.about import about_dash
from frontend.pages.dash_eto import eto_calculator_dash
from frontend.pages.documentation import documentation_layout
from frontend.pages.home import home_layout
from utils.language_manager import register_language_callbacks

# Adicionar o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuração de logging para produção
logger.configure(
    handlers=[
        {"sink": "logs/app.log", "rotation": "500 MB", "retention": "10 days"},
        {"sink": "logs/error.log", "rotation": "500 MB", "level": "ERROR"},
    ]
)

settings = get_settings()


def render_page_content(pathname: str) -> Union[html.Div, dbc.Container]:
    """
    Renderiza o conteúdo da página baseado na URL com tratamento de erro.
    
    Args:
        pathname: Caminho da URL (ex: '/', '/eto', '/about')
        
    Returns:
        Component Dash correspondente à página solicitada
    """
    try:
        if pathname == "/" or pathname == "/home":
            return home_layout()
        
        elif pathname == "/eto":
            return eto_calculator_dash()
        
        elif pathname == "/about":
            return about_dash()
        
        elif pathname == "/documentation":
            return documentation_layout()
        
        else:
            return html.Div([
                html.H1("404", className="display-1 text-muted"),
                html.P("Página não encontrada", className="lead"),
                html.A(
                    "Voltar ao início",
                    href="/",
                    className="btn btn-primary"
                )
            ], className="text-center mt-5")
    
    except Exception as e:
        logger.error(f"Erro ao renderizar página {pathname}: {e}")
        return html.Div([
            html.H1("500", className="display-1 text-danger"),
            html.P("Erro interno do servidor", className="lead"),
            html.A("Voltar ao início", href="/", className="btn btn-primary")
        ], className="text-center mt-5")


def create_dash_app() -> dash.Dash:
    """
    Cria e configura o aplicativo Dash principal para produção.
    
    Configura:
    - Tema Bootstrap e estilos externos (Leaflet, Font Awesome)
    - Layout principal com navbar, footer e roteamento
    - Stores globais para compartilhamento de dados
    - Registro de todos os callbacks modulares
    - Configurações de segurança e performance
    
    Returns:
        dash.Dash: Aplicativo Dash configurado e pronto para execução
    """
    app = dash.Dash(
        __name__,
        requests_pathname_prefix="/",
        assets_folder=settings.DASH_ASSETS_FOLDER,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
            '/assets/css/styles.css'
        ],
        external_scripts=[
            'https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js',
            'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.min.js',
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
        ],
        suppress_callback_exceptions=True,
        title=settings.PROJECT_NAME,
        # Configurações de segurança e performance
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
            {"charset": "utf-8"},
        ],
    )
    
    # Configurações adicionais de segurança
    app.server.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    # Layout principal da aplicação
    app.layout = dbc.Container([
        render_navbar(settings),
        dcc.Location(id='url', refresh=False),
        
        # Stores globais para compartilhar dados entre páginas
        dcc.Store(id='selected-location', data=None),
        dcc.Store(id='geolocation-error', data=None),
        # Session ID para usuário anônimo (persistência por aba)
        dcc.Store(id='app-session-id', data=None, storage_type='session'),
        # Cache store (localStorage) para dados climáticos
        dcc.Store(id='climate-cache-store', data={}, storage_type='local'),
        # Favorites store (localStorage) guarda lista de location_ids
        dcc.Store(id='favorites-store', data=[], storage_type='local'),
        # Estado do cálculo ETo (task_id, status, progress, resultados)
        dcc.Store(id='calculation-state', data=None),
        # Language store (localStorage) para persistir idioma selecionado
        dcc.Store(id='language-store', data='pt', storage_type='local'),
        
        # Intervalo para atualizar WebSocket (2 segundos)
        dcc.Interval(id='websocket-interval', interval=2000, n_intervals=0),
        
        html.Div(id='page-content'),
        render_footer()
    ], fluid=True, className="p-0")  # Remove padding para melhor uso de espaço

    # Registrar todos os callbacks modulares
    try:
        register_navigation_callbacks(app, render_page_content)
        register_map_callbacks(app)
        register_eto_callbacks(app)
        register_eto_v3_callbacks(app)  # V3 smart callbacks
        register_language_callbacks(app)  # Callbacks de idioma/tradução
        logger.info("✅ Todos os callbacks registrados com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar callbacks: {e}")
        raise

    return app


# O app.py é apenas responsável por criar e configurar o Dash
# Ele é importado por backend/main.py que monta o Dash no FastAPI
# Não deve ser executado diretamente como __main__
