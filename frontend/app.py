"""
Configuração e criação do aplicativo Dash.
"""
import json
import os
import sys

# Adicionar o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pytz
from dash import dcc, html
from dash.dependencies import ALL, Input, Output, State
from loguru import logger
from timezonefinderL import TimezoneFinder

from config.settings.app_settings import get_settings
from frontend.components.footer import render_footer
from frontend.components.navbar import render_navbar
from frontend.pages.about import about_dash
from frontend.pages.dash_eto import eto_calculator_dash
from frontend.pages.documentation import documentation_layout
from frontend.pages.home import home_layout

settings = get_settings()


def format_coordinates(lat, lng):
    """
    Formata coordenadas no formato geográfico com direções cardeais.
    
    Args:
        lat: Latitude em graus decimais
        lng: Longitude em graus decimais
        
    Returns:
        tuple: (latitude_formatada, longitude_formatada)
    """
    lat_dir = 'N' if lat >= 0 else 'S'
    lng_dir = 'E' if lng >= 0 else 'W'
    
    lat_formatted = f"{abs(lat):.4f}° {lat_dir}"
    lng_formatted = f"{abs(lng):.4f}° {lng_dir}"
    
    return lat_formatted, lng_formatted


def render_page_content(pathname):
    """
    Renderiza o conteúdo da página baseado na URL.
    """
    print(f"🔍 DEBUG RENDER_PAGE_CONTENT: pathname={pathname}")
    if pathname == "/" or pathname == "/home":
        try:
            print("🏠 DEBUG: Calling home_layout()...")
            layout = home_layout()
            print(f"✅ DEBUG: home_layout() returned successfully")
            return layout
        except Exception as e:
            print(f"❌ DEBUG: Error in home_layout(): {e}")
            import traceback
            traceback.print_exc()
            return html.H1(f"Home Page - Error: {e}")
    
    elif pathname == "/eto":
        try:
            return eto_calculator_dash()
        except ImportError:
            return html.H1("ETo Calculator Page - Layout não encontrado")
    
    elif pathname == "/about":
        try:
            return about_dash()
        except ImportError:
            return html.H1("About Page - Layout não encontrado")
    
    elif pathname == "/documentation":
        try:
            return documentation_layout()
        except ImportError:
            return html.H1("Documentation Page - Layout não encontrado")
    
    else:
        return html.H1("404 - Página não encontrada")


def get_elevation(lat: float, lon: float) -> float | None:
    """
    Busca altitude usando a Elevation API (Copernicus DEM 90m).
    
    TEMPORARIAMENTE usa versão SYNC (get_openmeteo_elevation) porque
    Dash roda em event loop e asyncio.run() não funciona.
    
    TODO: Migrar para versão totalmente async quando integrar com
          httpx async client do backend.
    
    Args:
        lat: Latitude (-90 a 90)
        lon: Longitude (-180 a 180)
        
    Returns:
        float | None: Elevação em metros ou None se erro
    """
    try:
        # Usar versão SYNC (deprecated mas funcional)
        from backend.api.services.elevation_api import get_openmeteo_elevation

        # Retorna: Tuple[float, List[str]] = (elevation, warnings)
        elevation, warnings = get_openmeteo_elevation(lat=lat, long=lon)
        
        # Log warnings se houver
        for warning in warnings:
            logger.warning(f"Elevation API: {warning}")
        
        return elevation
    except Exception as e:
        logger.error(f"Erro ao obter elevação para ({lat}, {lon}): {e}")
        return None


def create_dash_app() -> dash.Dash:
    """
    Cria e configura o aplicativo Dash.
    """
    print("\n" + "="*80)
    print("🚀 CRIANDO APLICATIVO DASH...")
    print("="*80 + "\n")
    
    app = dash.Dash(
        __name__,
        requests_pathname_prefix="/",
        assets_folder=settings.DASH_ASSETS_FOLDER,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            # CSS
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
            'frontend/assets/styles/styles.css'
        ],
        external_scripts=[
            # Bootstrap JavaScript
            'https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js',
            'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.min.js',
            # Leaflet para mapas
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
        ],
        suppress_callback_exceptions=True,
        title=settings.PROJECT_NAME
    )
    
    app.layout = dbc.Container([
        # Navbar modularizada
        render_navbar(settings),

        dcc.Location(id='url', refresh=False),
        
        # Stores globais compartilhados entre páginas
        dcc.Store(id='selected-location', data=None),
        dcc.Store(id='geolocation-error', data=None),
        
        html.Div(id='page-content'),
        
        # Footer global (aparece em todas as páginas)
        render_footer()
    ])

    # =========================================================================
    # CALLBACK DAS TABS DO MAPA MUNDIAL (usando dcc.Tabs)
    # =========================================================================
    @app.callback(
        Output('map-tab-content', 'children'),
        Input('map-tabs', 'value')
    )
    def render_map_tab_content(active_tab):
        """
        Renderiza conteúdo das tabs do mapa mundial.
        
        dcc.Tabs usa 'value' em vez de 'active_tab':
        - tab-leaflet = Tab 1 (Mapa Leaflet - PRIMEIRA)
        - tab-plotly = Tab 2 (Mapa Plotly - SEGUNDA)
        """
        print(f"\n{'='*80}")
        print(f"🎯 CALLBACK TABS EXECUTADO! active_tab = {repr(active_tab)}")
        print(f"{'='*80}\n")
        
        logger.info(f"🗺️ Tab ativa: {repr(active_tab)}")
        
        # =========================================================================
        # TAB 1 (PADRÃO): Mapa Mundial Leaflet (interativo, clicável para ETo)
        # =========================================================================
        if active_tab in ['tab-leaflet', 'tab-0', None]:
            print("🌍 Renderizando TAB 1: Mapa Leaflet (interativo)")
            return dl.Map(
                id="map", 
                children=[
                    dl.TileLayer(
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", 
                            attribution='OpenStreetMap',
                            noWrap=True  # Evita repetição do mapa
                        )
                    ], 
                    center=[20, 0], 
                    zoom=2,
                    minZoom=2,  # Zoom mínimo para evitar múltiplos mapas
                    maxZoom=18,  # Zoom máximo
                    maxBounds=[[-90, -180], [90, 180]],  # Limita aos bounds do mundo
                    maxBoundsViscosity=1.0,  # Impede scroll fora dos limites
                    style={
                        'width': '100%',
                        'height': '550px',
                        'cursor': 'pointer',
                        'border-radius': '8px'
                    }, 
                    dragging=True, 
                    scrollWheelZoom=True
                )
        
        # =========================================================================
        # TAB 2: Explorar Cidades (Plotly com 6.738 marcadores do banco)
        # =========================================================================
        elif active_tab in ['tab-plotly', 'tab-1']:
            print("📊 Renderizando TAB 2: Mapa Plotly (6.738 cidades)")
            try:
                import pandas as pd
                import plotly.express as px
                import requests

                # Buscar marcadores da API
                response = requests.get(
                    "http://localhost:8000/api/v1/world-locations/markers",
                    timeout=10
                )
                response.raise_for_status()
                markers_data = response.json()
                
                # Filtrar coordenadas inválidas
                df = pd.DataFrame(markers_data)
                original_count = len(df)
                df = df[
                    (df['lat'] >= -90) & (df['lat'] <= 90) &
                    (df['lon'] >= -180) & (df['lon'] <= 180)
                ]
                filtered_count = len(df)
                
                if original_count != filtered_count:
                    removed = original_count - filtered_count
                    logger.warning(
                        f"⚠️ Filtrados {removed} marcadores "
                        f"com coordenadas inválidas"
                    )
                
                # Criar mapa Plotly
                fig = px.scatter_mapbox(
                    df, 
                    lat="lat", 
                    lon="lon", 
                    hover_name="name",
                    hover_data={
                        "country_code": True,
                        "lat": ":.4f",
                        "lon": ":.4f"
                    },
                    color_discrete_sequence=["#2d5016"],
                    zoom=1,
                    height=600
                )
                fig.update_layout(
                    mapbox_style="open-street-map",
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    showlegend=False,
                    hovermode='closest'
                )
                fig.update_traces(marker={"size": 5, "opacity": 0.7})
                
                return html.Div([
                    dbc.Alert([
                        html.I(className="fas fa-map-marked-alt me-2"),
                        html.Span([
                            html.Strong(f"{filtered_count:,} cidades"),
                            " no banco de dados"
                        ])
                    ], color="success", className="py-2 px-3 mb-3"),
                    dcc.Graph(
                        figure=fig,
                        style={'height': '550px'},
                        config={
                            'displayModeBar': False,  # Remove barra de ferramentas
                            'scrollZoom': True
                        }
                    )
                ])
                
            except Exception as e:
                logger.error(f"❌ Erro ao carregar marcadores: {e}")
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Erro ao carregar marcadores: {e}"
                ], color="danger")
        
        # =========================================================================
        # FALLBACK: Retornar Tab 1 se o ID for desconhecido
        # =========================================================================
        else:
            logger.warning(f"⚠️ Tab desconhecida: {repr(active_tab)} - usando Tab 1")
            print(f"⚠️ Tab desconhecida: {repr(active_tab)} - renderizando Tab 1 (fallback)")
            return dl.Map(
                id="map", 
                children=[
                    dl.TileLayer(
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", 
                        attribution='OpenStreetMap',
                        noWrap=True
                    )
                ], 
                center=[20, 0], 
                zoom=2,
                minZoom=2,
                maxZoom=18,
                maxBounds=[[-90, -180], [90, 180]],
                maxBoundsViscosity=1.0,
                style={
                    'width': '100%',
                    'height': '550px',
                    'cursor': 'pointer',
                    'border-radius': '8px'
                }, 
                dragging=True, 
                scrollWheelZoom=True
            )

    # Callback para roteamento de páginas
    @app.callback(
        Output('page-content', 'children'),
        [Input('url', 'pathname')]
    )
    def display_page(pathname):
        return render_page_content(pathname)

    # Callback para alternar idioma
    @app.callback(
        Output('language-toggle', 'children'),
        [Input('language-toggle', 'n_clicks')]
    )
    def toggle_language(n_clicks):
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
        # Só atualizar se estiver na página ETo
        if pathname != '/eto':
            return dash.no_update
        
        if not location_data:
            return html.Div([
                html.I(className="fas fa-info-circle me-2"),
                html.Span(
                    "Nenhuma localização selecionada. "
                    "Volte para o mapa e clique em um local ou favorito."
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
        if n:
            return not is_open
        return is_open

    # =========================================================================
    # CALLBACKS GERAIS
    # =========================================================================

    # Callback para adicionar marker de geolocalização ao store
    @app.callback(
        Output('markers-store', 'data', allow_duplicate=True),
        [Input('geolocation', 'position')],
        [State('markers-store', 'data')],
        prevent_initial_call=True
    )
    def add_geolocation_marker(position, markers_data):
        if not position:
            return dash.no_update
        
        # Garantir que markers_data é uma lista
        if markers_data is None:
            markers_data = []
            
        lat, lon = position.get('lat', 0), position.get('lon', 0)
        elevation = get_elevation(lat, lon)
        alt = f"{elevation:.1f} m" if elevation is not None else "N/A"
        
        # Criar popup com componentes Dash serializáveis
        lat_fmt, lng_fmt = format_coordinates(lat, lon)
        popup_content = [
            html.H6("📍 Sua localização atual",
                    style={'marginBottom': '8px',
                           'textAlign': 'center'}),
            html.Div([
                html.B("Latitude: "), lat_fmt
            ]),
            html.Div([
                html.B("Longitude: "), lng_fmt
            ]),
            html.Div([
                html.B("Altitude: "), alt
            ])
        ]
        
        new_marker = {
            'id': 'user-location-marker',
            'position': [lat, lon],
            'popup': popup_content,
            'type': 'user'
        }
        # Remove existing user marker if any
        markers_data = [
            m for m in markers_data
            if m['id'] != 'user-location-marker'
        ]
        markers_data.append(new_marker)
        return markers_data

    # Callback para adicionar marker de clique ao store
    @app.callback(
        Output('markers-store', 'data', allow_duplicate=True),
        [Input('map', 'clickData')],
        [State('markers-store', 'data')],
        prevent_initial_call=True
    )
    def add_click_marker(clickData, markers_data):
        print(f"DEBUG: clickData recebido: {clickData}")  # Debug
        
        if not clickData:
            return dash.no_update
        
        # Extrair coordenadas do clickData
        try:
            lat = clickData['latlng']['lat']
            lng = clickData['latlng']['lng']
            print(f"DEBUG: Coordenadas extraídas: {lat}, {lng}")  # Debug
        except (KeyError, TypeError) as e:
            print(f"DEBUG: Erro ao extrair coordenadas: {e}")  # Debug
            return dash.no_update
        
        # Garantir que markers_data é uma lista
        if markers_data is None:
            markers_data = []
        
        print(f"DEBUG: Buscando elevação para {lat}, {lng}")  # Debug
        elevation = get_elevation(lat, lng)
        print(f"DEBUG: Elevação: {elevation}")  # Debug
        alt = f"{elevation:.1f} m" if elevation is not None else "N/A"
        
        # Buscar fuso horário e hora local
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lng, lat=lat)
        
        # Criar popup com componentes Dash serializáveis e mais informações
        lat_fmt, lng_fmt = format_coordinates(lat, lng)
        popup_content = [
            html.H6("📍 Localização selecionada",
                    style={'color': '#2d5016', 'marginBottom': '8px',
                           'textAlign': 'center'}),
            html.Div([
                html.B("Latitude: "), lat_fmt
            ], style={'fontSize': '13px'}),
            html.Div([
                html.B("Longitude: "), lng_fmt
            ], style={'fontSize': '13px'}),
            html.Div([
                html.B("Altitude: "), alt
            ], style={'fontSize': '13px'})
        ]
        
        # Adicionar informações de fuso horário se disponível
        if tz_name:
            tz = pytz.timezone(tz_name)
            current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
            popup_content.extend([
                html.Div([
                    html.B("Fuso horário: "), tz_name
                ], style={'fontSize': '13px'}),
                html.Div([
                    html.B("Hora local: "), current_time
                ], style={'fontSize': '13px'})
            ])
        
        popup_content.extend([
            html.Hr(style={'margin': '8px 0'}),
            html.Div("⚡ Ações rápidas: use os botões acima do mapa",
                    style={'fontSize': '12px', 'fontWeight': 'bold',
                           'marginBottom': '4px', 'color': '#2d5016'})
        ])
        
        new_marker = {
            'id': f'click-marker-{len(markers_data)}',
            'position': [lat, lng],
            'popup': popup_content,
            'type': 'click',
            'lat': lat,
            'lng': lng,
            'elevation': elevation
        }
        markers_data.append(new_marker)
        
        # Limitar a 10 markers (mantém user marker + 9 click markers)
        user_markers = [m for m in markers_data if m.get('type') == 'user']
        click_markers = [m for m in markers_data if m.get('type') == 'click']
        
        # Manter apenas os 9 últimos click markers
        if len(click_markers) > 9:
            click_markers = click_markers[-9:]
        
        markers_data = user_markers + click_markers
        print(f"DEBUG: Total de markers: {len(markers_data)}")  # Debug
        return markers_data

    # Callback para renderizar markers no mapa a partir do store
    @app.callback(
        Output('map', 'children'),
        [Input('markers-store', 'data')],
        prevent_initial_call=False
    )
    def render_markers(markers_data):
        children = [dl.TileLayer()]
        
        # Garantir que markers_data é uma lista
        if markers_data is None:
            markers_data = []
        
        for marker in markers_data:
            children.append(
                dl.Marker(
                    id=marker['id'],
                    position=marker['position'],
                    children=[dl.Popup(children=marker['popup'])]
                )
            )
        return children

    # =========================================================================
    # CALLBACK: Atualizar alerta com coordenadas (geolocalização, erro ou clique)
    # =========================================================================
    @app.callback(
        Output('click-info', 'children'),
        [
            Input('geolocation', 'position'),
            Input('geolocation', 'position_error'),
            Input('map', 'clickData')
        ],
        prevent_initial_call=False
    )
    def update_click_info_unified(geo_position, geo_error, clickData):
        """
        Atualiza o alerta azul com:
        - Coordenadas do usuário (geolocation.position) quando permitido
        - Mensagem de erro se geolocation negado (geolocation.position_error)
        - Coordenadas do clique no mapa (map.clickData) se usuário clicar manualmente
        
        Prioridade: geo_position > geo_error > clickData
        """
        ctx = dash.callback_context
        
        if not ctx.triggered:
            # Inicial: mostrar mensagem padrão
            return dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Clique em ",
                html.Strong("qualquer ponto do mapa"),
                " para calcular ETo"
            ], color="info", className="py-2 px-3 mb-0")
        
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Prioridade 1: Geolocalização (usuário permitiu)
        if triggered_id == 'geolocation' and geo_position:
            lat = geo_position.get('lat', 0)
            lng = geo_position.get('lon', 0)
            
            elevation = get_elevation(lat, lng)
            alt = f"{elevation:.1f} m" if elevation is not None else "N/A"
            lat_fmt, lng_fmt = format_coordinates(lat, lng)
            
            return dbc.Alert([
                html.I(className="fas fa-crosshairs me-2", style={"color": "#0dcaf0"}),
                html.Strong("Sua localização atual: ", style={"color": "#055160"}),
                html.B("Latitude: "), lat_fmt, " | ",
                html.B("Longitude: "), lng_fmt, " | ",
                html.B("Altitude: "), alt
            ], color="info", className="py-2 px-3 mb-0")
        
        # Prioridade 2: Erro de geolocalização (usuário negou ou erro)
        if triggered_id == 'geolocation' and geo_error:
            error_msg = geo_error.get('message', 'Erro desconhecido')
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Strong("Geolocalização não disponível: "),
                error_msg,
                ". Clique no mapa para selecionar uma localização."
            ], color="warning", className="py-2 px-3 mb-0")
        
        # Prioridade 3: Clique no mapa
        if triggered_id == 'map' and clickData:
            try:
                lat = clickData['latlng']['lat']
                lng = clickData['latlng']['lng']
                
                elevation = get_elevation(lat, lng)
                alt = f"{elevation:.1f} m" if elevation is not None else "N/A"
                lat_fmt, lng_fmt = format_coordinates(lat, lng)
                
                return dbc.Alert([
                    html.I(className="fas fa-map-pin me-2"),
                    html.B("Latitude: "), lat_fmt, " | ",
                    html.B("Longitude: "), lng_fmt, " | ",
                    html.B("Altitude: "), alt
                ], color="info", className="py-2 px-3 mb-0")
            except (KeyError, TypeError):
                return dash.no_update
        
        return dash.no_update
    
    # =========================================================================
    # CALLBACK: Atualizar hrefs dos botões de ação com coordenadas
    # =========================================================================
    @app.callback(
        [
            Output('calculate-daily-eto-btn', 'href'),
            Output('calculate-period-eto-btn', 'href')
        ],
        [
            Input('geolocation', 'position'),
            Input('map', 'clickData')
        ],
        prevent_initial_call=True
    )
    def update_action_buttons_unified(geo_position, clickData):
        """
        Atualiza os links dos botões com as coordenadas.
        Prioridade: geo_position > clickData
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update
        
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Geolocalização
        if triggered_id == 'geolocation' and geo_position:
            lat = geo_position.get('lat', 0)
            lng = geo_position.get('lon', 0)
            return f"/eto?lat={lat}&lon={lng}", f"/eto?lat={lat}&lon={lng}"
        
        # Clique no mapa
        if triggered_id == 'map' and clickData:
            try:
                lat = clickData['latlng']['lat']
                lng = clickData['latlng']['lng']
                return f"/eto?lat={lat}&lon={lng}", f"/eto?lat={lat}&lon={lng}"
            except (KeyError, TypeError):
                return dash.no_update, dash.no_update
        
        return dash.no_update, dash.no_update

    # Callback para calcular ETo do dia atual (abre modal)
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

    # Callback para calcular ETo do período (redireciona para página ETo)
    @app.callback(
        [Output('url', 'pathname', allow_duplicate=True),
         Output('selected-location', 'data', allow_duplicate=True)],
        [Input('calc-eto-period-btn', 'n_clicks')],
        [State('selected-location', 'data')],
        prevent_initial_call=True
    )
    def calc_eto_period(n_clicks, location_data):
        if not n_clicks or not location_data:
            return dash.no_update, dash.no_update
        
        # Adicionar flag indicando que veio do mapa
        location_data['from_map'] = True
        
        # Redirecionar para a página ETo
        return '/eto', location_data

    # Callback para salvar/remover favoritos
    @app.callback(
        [Output('favorites-store', 'data'),
         Output('save-favorite-btn', 'children'),
         Output('save-favorite-btn', 'color')],
        [Input('save-favorite-btn', 'n_clicks')],
        [State('selected-location', 'data'),
         State('favorites-store', 'data')],
        prevent_initial_call=True
    )
    def toggle_favorite(n_clicks, location_data, favorites):
        if not n_clicks or not location_data:
            return dash.no_update, dash.no_update, dash.no_update
        
        if favorites is None:
            favorites = []
        
        lat = location_data['lat']
        lng = location_data['lng']
        
        # Verificar se já está nos favoritos
        is_favorite = any(
            abs(f['lat'] - lat) < 0.0001 and abs(f['lng'] - lng) < 0.0001
            for f in favorites
        )
        
        if is_favorite:
            # Remover dos favoritos
            favorites = [
                f for f in favorites
                if not (abs(f['lat'] - lat) < 0.0001 and
                        abs(f['lng'] - lng) < 0.0001)
            ]
            btn_text = [html.I(className="fas fa-star")]
            btn_color = "warning"
        else:
            # Verificar limite de 20 favoritos
            if len(favorites) >= 20:
                # Não adicionar - mostrar aviso
                btn_text = [html.I(className="fas fa-exclamation-triangle")]
                btn_color = "danger"
                return dash.no_update, btn_text, btn_color
            
            # Adicionar aos favoritos
            favorites.append({
                'lat': lat,
                'lng': lng,
                'name': f"Local {lat:.2f}, {lng:.2f}",
                'timestamp': datetime.now().isoformat()
            })
            btn_text = [html.I(className="fas fa-check")]
            btn_color = "success"
        
        return favorites, btn_text, btn_color
    
    # Callback para resetar o botão de favorito ao mudar de localização
    @app.callback(
        [Output('save-favorite-btn', 'children', allow_duplicate=True),
         Output('save-favorite-btn', 'color', allow_duplicate=True)],
        [Input('selected-location', 'data')],
        [State('favorites-store', 'data')],
        prevent_initial_call=True
    )
    def reset_favorite_button(location_data, favorites):
        if not location_data:
            return [html.I(className="fas fa-star")], "warning"
        
        if not favorites:
            return [html.I(className="fas fa-star")], "warning"
        
        lat = location_data['lat']
        lng = location_data['lng']
        
        # Verificar se a localização atual já está nos favoritos
        is_favorite = any(
            abs(f['lat'] - lat) < 0.0001 and abs(f['lng'] - lng) < 0.0001
            for f in favorites
        )
        
        if is_favorite:
            # Já é favorito - mostrar botão de remover
            return ([html.I(className="fas fa-star", 
                           style={"color": "#ffc107"})], "warning")
        else:
            # Não é favorito - mostrar botão de adicionar
            if len(favorites) >= 20:
                # Limite atingido - mostrar desabilitado
                return ([html.I(className="fas fa-star")], "secondary")
            else:
                # Pode adicionar
                return ([html.I(className="fas fa-star")], "warning")


    # Callback para exibir lista de favoritos com paginação
    @app.callback(
        [Output('favorites-list', 'children'),
         Output('favorites-count', 'children'),
         Output('favorites-pagination-info', 'children'),
         Output('favorites-pagination', 'style'),
         Output('favorites-prev-page', 'disabled'),
         Output('favorites-next-page', 'disabled')],
        [Input('favorites-store', 'data'),
         Input('favorites-current-page', 'data'),
         Input('favorites-page-size', 'value')]
    )
    def display_favorites(favorites, current_page, page_size):
        if not favorites or len(favorites) == 0:
            return (
                html.P("Nenhum favorito salvo ainda.",
                       className="text-muted text-center py-3"), 
                "0",
                "",
                {"display": "none"},  # Esconde paginação
                True,  # Desabilita prev
                True   # Desabilita next
            )
        
        # Calcular paginação
        total_items = len(favorites)
        total_pages = (total_items + page_size - 1) // page_size
        current_page = min(current_page, total_pages)  # Garantir página válida
        
        # Calcular índices para slice
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Favoritos da página atual (reversed para mostrar mais recentes primeiro)
        reversed_favorites = list(reversed(favorites))
        page_favorites = reversed_favorites[start_idx:end_idx]
        
        favorites_items = []
        for i, fav in enumerate(page_favorites):
            # Índice real no array original (para delete)
            real_index = start_idx + i
            
            lat_fmt, lng_fmt = format_coordinates(fav['lat'], fav['lng'])
            
            favorites_items.append(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Strong(
                                fav.get('name', f'Local {real_index + 1}'),
                                style={"fontSize": "13px"}
                            ),
                            html.Br(),
                            html.Small([
                                f"Lat: {lat_fmt}, Lng: {lng_fmt}"
                            ], className="text-muted")
                        ], style={'flex': '1'}),
                        # Grupo de botões de ação
                        html.Div([
                            dbc.Button(
                                html.I(className="fas fa-calendar-day"),
                                id={'type': 'fav-eto-today-btn', 
                                    'index': real_index},
                                color="primary",
                                size="sm",
                                outline=True,
                                style={'padding': '0.2rem 0.4rem',
                                       'fontSize': '12px',
                                       'marginRight': '0.2rem'},
                                title="Calcular ETo hoje"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-calendar-week"),
                                id={'type': 'fav-eto-period-btn',
                                    'index': real_index},
                                color="info",
                                size="sm",
                                outline=True,
                                style={'padding': '0.2rem 0.4rem',
                                       'fontSize': '12px',
                                       'marginRight': '0.2rem'},
                                title="Calcular ETo do período"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-trash"),
                                id={'type': 'delete-fav-btn', 
                                    'index': real_index},
                                color="danger",
                                size="sm",
                                outline=True,
                                style={'padding': '0.2rem 0.4rem',
                                       'fontSize': '12px'},
                                title="Remover favorito"
                            )
                        ], className="d-flex")
                    ], className="d-flex justify-content-between "
                                 "align-items-center p-2")
                ], className="mb-1", style={'fontSize': '12px'})
            )
        
        # Texto de informação de paginação
        pagination_text = (
            f"Página {current_page} de {total_pages} "
            f"(Mostrando {start_idx + 1}-{min(end_idx, total_items)} de {total_items})"
        )
        
        # Controlar visibilidade e estado dos botões
        show_pagination = total_pages > 1
        pagination_style = {
            "display": "flex" if show_pagination else "none",
            "justifyContent": "center",
            "alignItems": "center",
            "marginTop": "0.5rem"
        }
        
        prev_disabled = current_page == 1
        next_disabled = current_page == total_pages
        
        return (
            html.Div(favorites_items),
            str(total_items),
            pagination_text,
            pagination_style,
            prev_disabled,
            next_disabled
        )
    
    # Callback para navegar entre páginas
    @app.callback(
        Output('favorites-current-page', 'data'),
        [Input('favorites-prev-page', 'n_clicks'),
         Input('favorites-next-page', 'n_clicks'),
         Input('favorites-page-size', 'value')],
        [State('favorites-current-page', 'data'),
         State('favorites-store', 'data')],
        prevent_initial_call=True
    )
    def update_page(prev_clicks, next_clicks, page_size, 
                    current_page, favorites):
        if not favorites:
            return 1
        
        ctx = dash.callback_context
        if not ctx.triggered:
            return current_page
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Se mudou o tamanho da página, volta para página 1
        if button_id == 'favorites-page-size':
            return 1
        
        total_pages = (len(favorites) + page_size - 1) // page_size
        
        if button_id == 'favorites-prev-page' and current_page > 1:
            return current_page - 1
        elif button_id == 'favorites-next-page' and current_page < total_pages:
            return current_page + 1
        
        return current_page


    # Callback para deletar favorito específico
    @app.callback(
        Output('favorites-store', 'data', allow_duplicate=True),
        [Input({'type': 'delete-fav-btn', 'index': dash.dependencies.ALL},
               'n_clicks')],
        [State('favorites-store', 'data')],
        prevent_initial_call=True
    )
    def delete_favorite(n_clicks_list, favorites):
        if not any(n_clicks_list) or not favorites:
            return dash.no_update
        
        # Encontrar qual botão foi clicado
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update
        
        # Extrair o índice do botão clicado
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        button_data = json.loads(button_id)
        index = button_data['index']
        
        # Remover o favorito (lembrar que a lista está invertida)
        reversed_index = len(favorites) - 1 - index
        if 0 <= reversed_index < len(favorites):
            favorites.pop(reversed_index)
        
        return favorites

    # Callback para abrir modal de confirmação de limpar favoritos
    @app.callback(
        [Output('clear-favorites-modal', 'is_open'),
         Output('clear-favorites-count', 'children')],
        [Input('clear-all-favorites-btn', 'n_clicks'),
         Input('cancel-clear-favorites', 'n_clicks'),
         Input('confirm-clear-favorites', 'n_clicks')],
        [State('clear-favorites-modal', 'is_open'),
         State('favorites-store', 'data')],
        prevent_initial_call=True
    )
    def toggle_clear_modal(clear_clicks, cancel_clicks, confirm_clicks, 
                          is_open, favorites):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'clear-all-favorites-btn':
            # Abrir modal e mostrar contador
            count = len(favorites) if favorites else 0
            count_text = f"Você tem {count} favorito(s) salvo(s)."
            return True, count_text
        else:
            # Fechar modal (cancelar ou confirmar será tratado em outro callback)
            return False, ""
    
    # Callback para confirmar exclusão de todos os favoritos
    @app.callback(
        Output('favorites-store', 'data', allow_duplicate=True),
        [Input('confirm-clear-favorites', 'n_clicks')],
        [State('favorites-store', 'data')],
        prevent_initial_call=True
    )
    def clear_all_favorites(confirm_clicks, favorites):
        if not confirm_clicks:
            return dash.no_update
        
        # Limpar todos os favoritos
        return []
    
    # Callback para desabilitar botão "Limpar Tudo" quando vazio
    @app.callback(
        Output('clear-all-favorites-btn', 'disabled'),
        [Input('favorites-store', 'data')]
    )
    def disable_clear_button(favorites):
        return not favorites or len(favorites) == 0

    # Callback para calcular ETo hoje a partir de favorito (usa modal)
    @app.callback(
        [Output('selected-location', 'data', allow_duplicate=True),
         Output('result-modal', 'is_open', allow_duplicate=True),
         Output('modal-title', 'children', allow_duplicate=True),
         Output('modal-body', 'children', allow_duplicate=True)],
        [Input({'type': 'fav-eto-today-btn', 'index': ALL}, 'n_clicks')],
        [State('favorites-store', 'data')],
        prevent_initial_call=True
    )
    def calc_eto_today_from_favorite(n_clicks_list, favorites):
        # Verificar se há cliques reais (não None ou 0)
        if not n_clicks_list or not any(n_clicks_list) or not favorites:
            return (dash.no_update, dash.no_update, 
                    dash.no_update, dash.no_update)
        
        # Encontrar qual botão foi clicado
        ctx = dash.callback_context
        if not ctx.triggered:
            return (dash.no_update, dash.no_update, 
                    dash.no_update, dash.no_update)
        
        # Extrair o índice do botão clicado
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        button_data = json.loads(button_id)
        index = button_data['index']
        
        # Obter o favorito (lembrar que a lista está invertida)
        reversed_index = len(favorites) - 1 - index
        if 0 <= reversed_index < len(favorites):
            fav = favorites[reversed_index]
            lat_fmt, lng_fmt = format_coordinates(fav['lat'], fav['lng'])
            
            location_data = {
                'lat': fav['lat'],
                'lng': fav['lng'],
                'name': fav.get('name', 'Local')
            }
            
            title = [
                html.I(className="fas fa-star me-2 text-warning"),
                f"ETo Hoje - {fav.get('name', 'Favorito')}"
            ]
            
            body = html.Div([
                dbc.Alert([
                    html.H5([
                        html.I(className="fas fa-map-marker-alt me-2"),
                        fav.get('name', 'Local Selecionado')
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
                        "⚠️ Funcionalidade em desenvolvimento.",
                        color="warning"
                    )
                ])
            ])
            
            return location_data, True, title, body
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Callback para calcular ETo do período a partir de favorito
    @app.callback(
        [Output('url', 'pathname', allow_duplicate=True),
         Output('selected-location', 'data', allow_duplicate=True)],
        [Input({'type': 'fav-eto-period-btn', 'index': ALL}, 'n_clicks')],
        [State('favorites-store', 'data')],
        prevent_initial_call=True
    )
    def calc_eto_period_from_favorite(n_clicks_list, favorites):
        if not any(n_clicks_list) or not favorites:
            return dash.no_update, dash.no_update
        
        # Encontrar qual botão foi clicado
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update
        
        # Extrair o índice do botão clicado
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        button_data = json.loads(button_id)
        index = button_data['index']
        
        # Obter o favorito (lembrar que a lista está invertida)
        reversed_index = len(favorites) - 1 - index
        if 0 <= reversed_index < len(favorites):
            fav = favorites[reversed_index]
            # Salvar localização selecionada e redirecionar para página ETo
            location_data = {
                'lat': fav['lat'],
                'lng': fav['lng'],
                'name': fav.get('name', 'Local'),
                'from_favorite': True
            }
            return '/eto', location_data
        
        return dash.no_update, dash.no_update

    return app



if __name__ == '__main__':
    app = create_dash_app()
    app.run(
        debug=True,
        host='127.0.0.1',
        port=8050
    )