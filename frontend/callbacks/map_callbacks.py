"""
Callbacks do mapa mundial - Mapa Leaflet interativo com camadas GeoJSON e marcadores.
"""
import json
import os
from datetime import datetime
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pandas as pd
import pytz
from dash import dcc, html
from dash.dependencies import Input, Output, State
from loguru import logger
from timezonefinderL import TimezoneFinder

from frontend.utils.coordinates import format_coordinates
from frontend.utils.elevation import get_elevation


def register_map_callbacks(app: dash.Dash):
    """
    Registra todos os callbacks relacionados ao mapa mundial.
    
    Inclui:
    - Renderização das tabs (Leaflet/Plotly)
    - Adição de markers (geolocalização e cliques)
    - Renderização de markers
    - Atualização do alerta de informações
    - Atualização dos botões de ação
    
    Args:
        app: Instância do aplicativo Dash
    """
    
    # =========================================================================
    # FUNÇÃO AUXILIAR: Carregar GeoJSON
    # =========================================================================
    def load_geojson(filename):
        """Carrega arquivo GeoJSON da pasta data/geojson."""
        geojson_path = Path(__file__).parent.parent.parent / 'data' / 'geojson' / filename
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {filename}: {e}")
            return None

    # =========================================================================
    # CALLBACK: Renderizar mapa mundial Leaflet com camadas
    # =========================================================================
    @app.callback(
        Output('map-tab-content', 'children'),
        Input('map-tabs', 'data')
    )
    def render_map_tab_content(active_tab):
        """
        Renderiza mapa mundial Leaflet com camadas GeoJSON e marcadores.
        
        Camadas incluídas:
        - Contorno do Brasil (verde)
        - Região MATOPIBA (azul)
        - Marcador especial: Piracicaba/ESALQ (ícone universidade)
        - LocateControl para geolocalização
        - LayersControl para gerenciar camadas
        
        IMPORTANTE: O mapa deve ter id='map' para os callbacks de clique funcionarem.
        """
        logger.info(f"🗺️ Renderizando mapa mundial (tab: {active_tab})")
        
        # Carregar GeoJSON files
        brasil_geojson = load_geojson('BR_UF_2024.geojson')
        matopiba_geojson = load_geojson('Matopiba_Perimetro.geojson')
        
        # Definir camadas base
        map_children = [
            # Camada de tiles base
            dl.TileLayer(
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                attribution='&copy; OpenStreetMap contributors',
                noWrap=True
            ),
            
            # LayerGroup para markers dinâmicos (geolocalização e cliques)
            dl.LayerGroup(id='markers-layer', children=[]),
            
            # LocateControl - Geolocalização integrada
            dl.LocateControl(
                options={
                    'position': 'topleft',
                    'strings': {'title': 'Localizar-me'},
                    'locateOptions': {'enableHighAccuracy': True}
                }
            ),
        ]
        
        # Adicionar camada Brasil (verde) se disponível
        if brasil_geojson:
            map_children.append(
                dl.GeoJSON(
                    id='brasil-layer',
                    data=brasil_geojson,
                    options={
                        'style': {
                            'color': '#28a745',
                            'weight': 2,
                            'fillColor': '#28a745',
                            'fillOpacity': 0.1
                        }
                    }
                )
            )
        
        # Adicionar camada MATOPIBA (azul) se disponível
        if matopiba_geojson:
            map_children.append(
                dl.GeoJSON(
                    id='matopiba-layer',
                    data=matopiba_geojson,
                    options={
                        'style': {
                            'color': '#007bff',
                            'weight': 2,
                            'fillColor': '#007bff',
                            'fillOpacity': 0.2
                        }
                    }
                )
            )
        
        # Adicionar marcador especial para Piracicaba/ESALQ
        # Coordenadas: -22.7252, -47.6493
        piracicaba_marker = dl.Marker(
            position=[-22.7252, -47.6493],
            children=[
                dl.Tooltip("Piracicaba - ESALQ/USP"),
                dl.Popup([
                    html.H6("🎓 Piracicaba - ESALQ/USP", className="mb-2"),
                    html.P([
                        html.Strong("Escola Superior de Agricultura"),
                        html.Br(),
                        "Luiz de Queiroz - USP",
                        html.Br(),
                        html.Br(),
                        html.Small([
                            "📍 ", format_coordinates(-22.7252, -47.6493),
                            html.Br(),
                            "🏔️ Elevação: 527 m"
                        ])
                    ], className="mb-0 small"),
                    html.Hr(className="my-2"),
                    html.A(
                        "🌐 www.esalq.usp.br",
                        href="https://www.esalq.usp.br/",
                        target="_blank",
                        className="text-success"
                    )
                ])
            ],
            icon={
                'iconUrl': 'https://cdn-icons-png.flaticon.com/512/3976/3976625.png',
                'iconSize': [32, 32],
                'iconAnchor': [16, 32],
                'popupAnchor': [0, -32]
            }
        )
        map_children.append(piracicaba_marker)
        
        # Adicionar LayersControl para gerenciar camadas
        if brasil_geojson or matopiba_geojson:
            overlays = {}
            if brasil_geojson:
                overlays['brasil-layer'] = '🇧🇷 Brasil'
            if matopiba_geojson:
                overlays['matopiba-layer'] = '🌾 MATOPIBA'
            
            map_children.append(
                dl.LayersControl(
                    position='topright',
                    overlays=overlays
                )
            )
        
        # Criar mapa Leaflet com ID FIXO 'map' para compatibilidade com callbacks
        return dl.Map(
            id="map",
            children=map_children,
            center=[-15, -47],  # Centro do Brasil
            zoom=4,
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

    # =========================================================================
    # CALLBACK: Adicionar marker de geolocalização
    # =========================================================================
    @app.callback(
        Output('markers-store', 'data', allow_duplicate=True),
        [Input('geolocation', 'position')],
        [State('markers-store', 'data')],
        prevent_initial_call=True
    )
    def add_geolocation_marker(position, markers_data):
        """Adiciona marker da posição GPS do usuário."""
        if not position:
            return dash.no_update
        
        if markers_data is None:
            markers_data = []
            
        lat, lon = position.get('lat', 0), position.get('lon', 0)
        elevation = get_elevation(lat, lon)
        alt = f"{elevation:.1f} m" if elevation is not None else "N/A"
        
        lat_fmt, lng_fmt = format_coordinates(lat, lon)
        popup_content = [
            html.H6("📍 Sua localização atual",
                    style={'marginBottom': '8px', 'textAlign': 'center'}),
            html.Div([html.B("Latitude: "), lat_fmt]),
            html.Div([html.B("Longitude: "), lng_fmt]),
            html.Div([html.B("Altitude: "), alt])
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

    # =========================================================================
    # CALLBACK: Adicionar marker de clique no mapa
    # =========================================================================
    @app.callback(
        Output('markers-store', 'data', allow_duplicate=True),
        [Input('map', 'clickData')],
        [State('markers-store', 'data')],
        prevent_initial_call=True
    )
    def add_click_marker(clickData, markers_data):
        """Adiciona marker onde usuário clicou no mapa."""
        print(f"DEBUG: clickData recebido: {clickData}")
        
        if not clickData:
            return dash.no_update
        
        try:
            lat = clickData['latlng']['lat']
            lng = clickData['latlng']['lng']
            print(f"DEBUG: Coordenadas extraídas: {lat}, {lng}")
        except (KeyError, TypeError) as e:
            print(f"DEBUG: Erro ao extrair coordenadas: {e}")
            return dash.no_update
        
        if markers_data is None:
            markers_data = []
        
        print(f"DEBUG: Buscando elevação para {lat}, {lng}")
        elevation = get_elevation(lat, lng)
        print(f"DEBUG: Elevação: {elevation}")
        alt = f"{elevation:.1f} m" if elevation is not None else "N/A"
        
        # Buscar fuso horário e hora local
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lng, lat=lat)
        
        lat_fmt, lng_fmt = format_coordinates(lat, lng)
        popup_content = [
            html.H6("📍 Localização selecionada",
                    style={'color': '#2d5016', 'marginBottom': '8px',
                           'textAlign': 'center'}),
            html.Div([html.B("Latitude: "), lat_fmt], style={'fontSize': '13px'}),
            html.Div([html.B("Longitude: "), lng_fmt], style={'fontSize': '13px'}),
            html.Div([html.B("Altitude: "), alt], style={'fontSize': '13px'})
        ]
        
        # Adicionar fuso horário se disponível
        if tz_name:
            tz = pytz.timezone(tz_name)
            current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
            popup_content.extend([
                html.Div([html.B("Fuso horário: "), tz_name], 
                        style={'fontSize': '13px'}),
                html.Div([html.B("Hora local: "), current_time], 
                        style={'fontSize': '13px'})
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
        
        # Limitar a 10 markers (user + 9 click markers)
        user_markers = [m for m in markers_data if m.get('type') == 'user']
        click_markers = [m for m in markers_data if m.get('type') == 'click']
        
        if len(click_markers) > 9:
            click_markers = click_markers[-9:]
        
        markers_data = user_markers + click_markers
        print(f"DEBUG: Total de markers: {len(markers_data)}")
        return markers_data

    # =========================================================================
    # CALLBACK: Atualizar LayerGroup de markers
    # =========================================================================
    @app.callback(
        Output('markers-layer', 'children'),
        [Input('markers-store', 'data')],
        prevent_initial_call=True
    )
    def update_markers_layer(markers_data):
        """Atualiza a camada de markers dinâmicos (geolocalização e cliques)."""
        if markers_data is None or len(markers_data) == 0:
            return []
        
        markers = []
        for marker in markers_data:
            markers.append(
                dl.Marker(
                    id=marker['id'],
                    position=marker['position'],
                    children=[dl.Popup(children=marker['popup'])]
                )
            )
        return markers

    # =========================================================================
    # CALLBACK: Renderizar markers no mapa (DESABILITADO - conflito com render_map_tab_content)
    # =========================================================================
    # NOTA: Este callback estava sobrescrevendo os children do mapa,
    # removendo as camadas GeoJSON e outros elementos.
    # Os markers agora são gerenciados via LayerGroup dentro do render_map_tab_content
    # @app.callback(
    #     Output('map', 'children'),
    #     [Input('markers-store', 'data')],
    #     prevent_initial_call=False
    # )
    # def render_markers(markers_data):
    #     """Renderiza todos os markers armazenados no mapa."""
    #     children = [dl.TileLayer()]
    #     
    #     if markers_data is None:
    #         markers_data = []
    #     
    #     for marker in markers_data:
    #         children.append(
    #             dl.Marker(
    #                 id=marker['id'],
    #                 position=marker['position'],
    #                 children=[dl.Popup(children=marker['popup'])]
    #             )
    #         )
    #     return children

    # =========================================================================
    # CALLBACK: Atualizar alerta com coordenadas
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
        Atualiza o alerta azul com coordenadas.
        
        Prioridade: geo_position > geo_error > clickData
        """
        ctx = dash.callback_context
        
        if not ctx.triggered:
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
        
        # Prioridade 2: Erro de geolocalização
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
    # CALLBACK: Atualizar hrefs dos botões de ação
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
