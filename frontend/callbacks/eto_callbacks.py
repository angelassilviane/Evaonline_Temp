"""
Callbacks da página ETo - Cálculos e interações com modais.
"""
import dash
import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output, State

from frontend.utils.coordinates import format_coordinates


def register_eto_callbacks(app: dash.Dash):
    """
    Registra todos os callbacks relacionados à página ETo.
    
    Inclui:
    - Cálculo de ETo do dia atual (abre modal)
    - Cálculo de ETo do período (redireciona para página ETo)
    
    Args:
        app: Instância do aplicativo Dash
    """
    
    # =========================================================================
    # CALLBACK: Calcular ETo do dia atual (abre modal)
    # =========================================================================
    @app.callback(
        [Output('result-modal', 'is_open'),
         Output('modal-title', 'children'),
         Output('modal-body', 'children')],
        [Input('calc-eto-today-btn', 'n_clicks'),
         Input('close-modal', 'n_clicks')],
        [State('selected-location', 'data'),
         State('result-modal', 'is_open')],
        prevent_initial_call=True
    )
    def calc_eto_today(calc_clicks, close_clicks, location_data, is_open):
        """
        Abre modal com cálculo de ETo do dia atual para a localização selecionada.
        
        Args:
            calc_clicks: Número de cliques no botão de calcular
            close_clicks: Número de cliques no botão de fechar
            location_data: Dados da localização selecionada (lat, lng)
            is_open: Estado atual do modal
            
        Returns:
            Tupla (is_open, title, body) para o modal
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # DEBUG: Imprimir para ver o que está disparando
        print(f"DEBUG calc_eto_today - button_id: {button_id}, "
              f"calc_clicks: {calc_clicks}, close_clicks: {close_clicks}")
        
        # Se clicou em fechar
        if button_id == 'close-modal':
            return False, dash.no_update, dash.no_update
        
        # Se clicou em calcular - VERIFICAR SE É CLIQUE REAL (não None ou 0)
        if (button_id == 'calc-eto-today-btn' and 
            calc_clicks and calc_clicks > 0 and location_data):
            lat = location_data['lat']
            lng = location_data['lng']
            lat_fmt, lng_fmt = format_coordinates(lat, lng)
            
            title = [
                html.I(className="fas fa-calculator me-2"),
                "Cálculo de ETo - Hoje"
            ]
            
            body = html.Div([
                dbc.Alert([
                    html.H5([
                        html.I(className="fas fa-map-marker-alt me-2"),
                        "Localização Selecionada"
                    ], className="alert-heading"),
                    html.Hr(),
                    html.P([
                        html.Strong("Latitude: "), lat_fmt, html.Br(),
                        html.Strong("Longitude: "), lng_fmt
                    ], className="mb-0")
                ], color="info"),
                
                html.Div([
                    html.H6([
                        html.I(className="fas fa-spinner fa-spin me-2"),
                        "Processando..."
                    ], className="text-primary"),
                    html.P("Buscando dados meteorológicos do dia atual..."),
                    html.Hr(),
                    dbc.Alert(
                        "⚠️ Funcionalidade em desenvolvimento. "
                        "Em breve você poderá visualizar os resultados "
                        "completos do cálculo de ETo.",
                        color="warning"
                    )
                ], className="mt-3")
            ])
            
            return True, title, body
        
        return dash.no_update, dash.no_update, dash.no_update

    # =========================================================================
    # CALLBACK: Calcular ETo do período (redireciona para página ETo)
    # =========================================================================
    @app.callback(
        [Output('url', 'pathname', allow_duplicate=True),
         Output('selected-location', 'data', allow_duplicate=True)],
        [Input('calc-eto-period-btn', 'n_clicks')],
        [State('selected-location', 'data')],
        prevent_initial_call=True
    )
    def calc_eto_period(n_clicks, location_data):
        """
        Redireciona para a página ETo com os dados da localização selecionada.
        
        Args:
            n_clicks: Número de cliques no botão
            location_data: Dados da localização selecionada
            
        Returns:
            Tupla (pathname, location_data) para redirecionamento
        """
        if not n_clicks or not location_data:
            return dash.no_update, dash.no_update
        
        # Adicionar flag indicando que veio do mapa
        location_data['from_map'] = True
        
        # Redirecionar para a página ETo
        return '/eto', location_data
