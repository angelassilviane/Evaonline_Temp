"""
Configuração e criação do aplicativo Dash.
"""
import os
import sys

# Adicionar o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from config.settings.app_settings import get_settings
from frontend.callbacks.eto_callbacks import register_eto_callbacks
from frontend.callbacks.map_callbacks import register_map_callbacks
from frontend.callbacks.navigation_callbacks import register_navigation_callbacks
from frontend.components.footer import render_footer
from frontend.components.navbar import render_navbar
from frontend.pages.about import about_dash
from frontend.pages.dash_eto import eto_calculator_dash
from frontend.pages.documentation import documentation_layout
from frontend.pages.home import home_layout

settings = get_settings()


def render_page_content(pathname):
    """
    Renderiza o conteúdo da página baseado na URL.
    
    Args:
        pathname: Caminho da URL (ex: '/', '/eto', '/about')
        
    Returns:
        Component Dash correspondente à página solicitada
    """
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
            html.A("Voltar ao início", href="/", className="btn btn-primary")
        ], className="text-center mt-5")


def create_dash_app() -> dash.Dash:
    """
    Cria e configura o aplicativo Dash principal.
    
    Configura:
    - Tema Bootstrap e estilos externos (Leaflet, Font Awesome)
    - Layout principal com navbar, footer e roteamento
    - Stores globais para compartilhamento de dados
    - Registro de todos os callbacks modulares
    
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
            'frontend/assets/styles/styles.css'
        ],
        external_scripts=[
            'https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js',
            'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.min.js',
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
        ],
        suppress_callback_exceptions=True,
        title=settings.PROJECT_NAME
    )
    
    # Layout principal da aplicação
    app.layout = dbc.Container([
        render_navbar(settings),
        dcc.Location(id='url', refresh=False),
        
        # Stores globais para compartilhar dados entre páginas
        dcc.Store(id='selected-location', data=None),
        dcc.Store(id='geolocation-error', data=None),
        
        html.Div(id='page-content'),
        render_footer()
    ])

    # Registrar todos os callbacks modulares
    register_navigation_callbacks(app, render_page_content)
    register_map_callbacks(app)
    register_eto_callbacks(app)

    return app



if __name__ == '__main__':
    app = create_dash_app()
    app.run(
        debug=True,
        host='127.0.0.1',
        port=8050
    )