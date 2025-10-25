"""
Callbacks do mapa mundial - Otimizados para produção.
"""
import json
from datetime import datetime
from typing import Dict, List, Optional

import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import dcc, html
from dash.dependencies import Input, Output, State
from loguru import logger
from pytz import timezone
from timezonefinderL import TimezoneFinder

from frontend.utils.coordinates import format_coordinates


class MapCallbackManager:
    """Gerencia callbacks do mapa com estado e cache."""
    
    def __init__(self):
        self.user_markers: List[Dict] = []
        self.click_markers: List[Dict] = []
        self.max_markers = 10
        
    def add_marker(self, marker_data: Dict) -> List[Dict]:
        """Adiciona marker com limite de quantidade."""
        if marker_data.get('type') == 'user':
            self.user_markers = [marker_data]  # Apenas um marker de usuário
        elif marker_data.get('type') == 'click':
            self.click_markers.append(marker_data)
            # Manter apenas os últimos N markers
            if len(self.click_markers) > self.max_markers - 1:
                self.click_markers = self.click_markers[-(self.max_markers - 1):]
        
        return self.user_markers + self.click_markers


# Instância global do gerenciador
marker_manager = MapCallbackManager()


def register_map_callbacks(app: dash.Dash):
    """
    Registra todos os callbacks relacionados ao mapa mundial.
    
    Inclui:
    - Adição de markers (geolocalização e cliques)
    - Atualização de markers dinâmicos
    - Atualização do alerta de informações (coordenadas e erros)
    - Toggle automático de camadas baseado em zoom
    """
    
    @app.callback(
        Output('dynamic-markers', 'children'),
        Input('markers-store', 'data'),
        prevent_initial_call=False  # Permitir chamada inicial
    )
    def update_dynamic_markers(markers_data: List[Dict]) -> List[dl.Marker]:
        """Atualiza os markers dinâmicos no mapa."""
        if not markers_data:
            return []
        
        markers = []
        for marker in markers_data:
            try:
                if marker.get('type') == 'user':
                    # Marker de geolocalização (azul)
                    markers.append(
                        dl.Marker(
                            position=marker['position'],
                            children=dl.Popup(marker['popup']),
                            icon={
                                'iconUrl': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                                'iconSize': [25, 41],
                                'iconAnchor': [12, 41]
                            }
                        )
                    )
                elif marker.get('type') == 'click':
                    # Marker de clique (vermelho)
                    markers.append(
                        dl.Marker(
                            position=marker['position'],
                            children=dl.Popup(marker['popup']),
                            icon={
                                'iconUrl': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                                'iconSize': [25, 41],
                                'iconAnchor': [12, 41]
                            }
                        )
                    )
            except Exception as e:
                logger.error(f"Erro ao criar marker: {e}")
                continue
        
        logger.debug(f"Renderizados {len(markers)} markers")
        return markers

    @app.callback(
        Output('markers-store', 'data'),
        [Input('geolocation', 'position'),
         Input('map', 'clickData')],
        [State('markers-store', 'data')],
        prevent_initial_call=True
    )
    def handle_map_interactions(
        geo_position: Optional[Dict], 
        click_data: Optional[Dict], 
        current_markers: List[Dict]
    ) -> List[Dict]:
        """Gerencia interações do mapa (geolocalização e cliques)."""
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            if trigger_id == 'geolocation' and geo_position:
                return _create_geolocation_marker(geo_position, current_markers)
            elif trigger_id == 'map' and click_data:
                return _create_click_marker(click_data, current_markers)
        except Exception as e:
            logger.error(f"Erro em handle_map_interactions: {e}")
        
        return dash.no_update

    def _create_geolocation_marker(
        position: Dict, 
        markers: List[Dict]
    ) -> List[Dict]:
        """Cria marker de geolocalização."""
        lat, lon = position.get('lat', 0), position.get('lon', 0)
        
        lat_fmt, lng_fmt = format_coordinates(lat, lon)
        popup_content = [
            html.H6("📍 Sua localização atual",
                    style={'marginBottom': '8px', 'textAlign': 'center'}),
            html.Div([html.B("Latitude: "), lat_fmt]),
            html.Div([html.B("Longitude: "), lng_fmt]),
            html.Div([html.B("Altitude: "), "N/A (obtida no cálculo do ETo)"])
        ]
        
        new_marker = {
            'id': 'user-location-marker',
            'position': [lat, lon],
            'popup': popup_content,
            'type': 'user',
            'timestamp': datetime.now().isoformat()
        }
        
        return marker_manager.add_marker(new_marker)

    def _create_click_marker(click_data: Dict, markers: List[Dict]) -> List[Dict]:
        """Cria marker de clique no mapa."""
        try:
            lat = click_data['latlng']['lat']
            lng = click_data['latlng']['lng']
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao extrair coordenadas do click: {e}")
            return dash.no_update
        
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
            html.Div([html.B("Altitude: "), "N/A (obtida no cálculo do ETo)"], 
                    style={'fontSize': '13px'})
        ]
        
        # Adicionar fuso horário se disponível
        if tz_name:
            tz = timezone(tz_name)
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
            'id': f'click-marker-{datetime.now().timestamp()}',
            'position': [lat, lng],
            'popup': popup_content,
            'type': 'click',
            'lat': lat,
            'lng': lng,
            'timestamp': datetime.now().isoformat()
        }
        
        return marker_manager.add_marker(new_marker)

    @app.callback(
        Output('click-info', 'children'),
        [Input('geolocation', 'position'),
         Input('geolocation', 'position_error'),
         Input('map', 'clickData')],
        prevent_initial_call=False
    )
    def update_click_info_unified(
        geo_position: Optional[Dict], 
        geo_error: Optional[Dict], 
        click_data: Optional[Dict]
    ) -> dbc.Alert:
        """Atualiza informações de coordenadas com prioridade."""
        ctx = dash.callback_context
        
        # Estado inicial
        if not ctx.triggered:
            return dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Clique em ",
                html.Strong("qualquer ponto do mapa"),
                " para calcular ETo"
            ], color="info", className="py-2 px-3 mb-0")
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            # Prioridade 1: Geolocalização
            if trigger_id == 'geolocation' and geo_position:
                return _create_geo_alert(geo_position)
            
            # Prioridade 2: Erro de geolocalização
            if trigger_id == 'geolocation' and geo_error:
                return _create_error_alert(geo_error)
            
            # Prioridade 3: Clique no mapa
            if trigger_id == 'map' and click_data:
                return _create_click_alert(click_data)
                
        except Exception as e:
            logger.error(f"Erro em update_click_info_unified: {e}")
        
        return dash.no_update

    def _create_geo_alert(position: Dict) -> dbc.Alert:
        """Cria alerta para geolocalização."""
        lat, lon = position.get('lat', 0), position.get('lon', 0)
        lat_fmt, lng_fmt = format_coordinates(lat, lon)
        
        return dbc.Alert([
            html.I(className="fas fa-crosshairs me-2", style={"color": "#0dcaf0"}),
            html.Strong("Sua localização atual: ", style={"color": "#055160"}),
            html.B("Latitude: "), lat_fmt, " | ",
            html.B("Longitude: "), lng_fmt, " | ",
            html.B("Altitude: "), "N/A (obtida no cálculo do ETo)"
        ], color="info", className="py-2 px-3 mb-0")

    def _create_error_alert(error: Dict) -> dbc.Alert:
        """Cria alerta para erro de geolocalização."""
        error_msg = error.get('message', 'Erro desconhecido')
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            html.Strong("Geolocalização não disponível: "),
            error_msg,
            ". Clique no mapa para selecionar uma localização."
        ], color="warning", className="py-2 px-3 mb-0")

    def _create_click_alert(click_data: Dict) -> dbc.Alert:
        """Cria alerta para clique no mapa."""
        lat = click_data['latlng']['lat']
        lng = click_data['latlng']['lng']
        lat_fmt, lng_fmt = format_coordinates(lat, lng)
        
        return dbc.Alert([
            html.I(className="fas fa-map-pin me-2"),
            html.B("Latitude: "), lat_fmt, " | ",
            html.B("Longitude: "), lng_fmt, " | ",
            html.B("Altitude: "), "N/A (obtida no cálculo do ETo)"
        ], color="info", className="py-2 px-3 mb-0")

    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        [Input('calculate-daily-eto-btn', 'n_clicks'),
         Input('calculate-period-eto-btn', 'n_clicks')],
        [State('geolocation', 'position'),
         State('map', 'clickData'),
         State('selected-location', 'data')],
        prevent_initial_call=True
    )
    def handle_quick_actions(
        daily_clicks, period_clicks,
        geo_position: Optional[Dict], 
        click_data: Optional[Dict],
        location_data: Optional[Dict]
    ) -> Optional[str]:
        """Manipula ações rápidas dos botões (navegação)."""
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            # Obter coordenadas da geolocalização ou clique no mapa
            lat, lon = None, None
            
            if geo_position:
                lat, lon = geo_position.get('lat'), geo_position.get('lon')
            elif click_data:
                lat = click_data.get('latlng', {}).get('lat')
                lon = click_data.get('latlng', {}).get('lng')
            
            if lat is None or lon is None:
                logger.warning("Nenhuma localização disponível para ação rápida")
                return dash.no_update
            
            # Redirecionar baseado no botão clicado
            if trigger_id == 'calculate-daily-eto-btn':
                # Calcular ETo diária (rápido)
                return f"/eto?lat={lat}&lon={lon}&mode=daily"
            
            elif trigger_id == 'calculate-period-eto-btn':
                # Ir para página de cálculo de período (customizável)
                return f"/eto?lat={lat}&lon={lon}&mode=period"
                
        except Exception as e:
            logger.error(f"Erro em handle_quick_actions: {e}")
        
        return dash.no_update

    logger.info("✅ Callbacks do mapa registrados com sucesso")
