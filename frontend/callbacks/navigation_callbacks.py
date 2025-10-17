"""
Callbacks de navegação - Roteamento, navbar e controles gerais de navegação.
"""
import dash
from dash import html
from dash.dependencies import Input, Output, State

from frontend.utils.coordinates import format_coordinates


def register_navigation_callbacks(app: dash.Dash, render_page_content_func):
    """
    Registra todos os callbacks relacionados a navegação.
    
    Args:
        app: Instância do aplicativo Dash
        render_page_content_func: Função para renderizar conteúdo das páginas
    """
    
    # Callback para roteamento de páginas
    @app.callback(
        Output('page-content', 'children'),
        [Input('url', 'pathname')]
    )
    def display_page(pathname):
        """Renderiza página baseado na URL."""
        return render_page_content_func(pathname)

    # Callback para alternar idioma
    @app.callback(
        Output('language-toggle', 'children'),
        [Input('language-toggle', 'n_clicks')]
    )
    def toggle_language(n_clicks):
        """Alterna entre idiomas (Inglês/Português)."""
        if n_clicks is None:
            return "English"
        if n_clicks % 2 == 1:
            return "Portuguese"
        return "English"

    # Callback para exibir localização selecionada na página ETo
    @app.callback(
        Output('selected-location-display', 'children'),
        [Input('url', 'pathname'),
         Input('selected-location', 'data')]
    )
    def display_selected_location_eto(pathname, location_data):
        """Exibe informações da localização selecionada na página ETo."""
        # Só atualizar se estiver na página ETo
        if pathname != '/eto':
            return dash.no_update
        
        if not location_data:
            return html.Div([
                html.I(className="fas fa-info-circle me-2"),
                html.Span(
                    "Nenhuma localização selecionada. "
                    "Volte para o mapa e clique em um local."
                )
            ], className="text-muted")
        
        lat_fmt, lng_fmt = format_coordinates(
            location_data['lat'], location_data['lng'])
        
        return html.Div([
            html.H6([
                html.I(className="fas fa-map-marker-alt me-2"),
                location_data.get('name', 'Local Selecionado')
            ], className="mb-2"),
            html.P([
                html.Strong("Latitude: "),
                lat_fmt,
                html.Br(),
                html.Strong("Longitude: "),
                lng_fmt
            ], className="mb-0"),
            html.Small([
                html.I(className="fas fa-check-circle text-success me-1"),
                "Pronto para calcular ETo"
            ], className="text-muted")
        ])

    # Callback para navbar toggler (mobile)
    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
    def toggle_navbar_collapse(n, is_open):
        """Toggle do menu de navegação em dispositivos móveis."""
        if n:
            return not is_open
        return is_open
