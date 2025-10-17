"""
Mapa mundial interativo com Leaflet, camadas GeoJSON e marcadores.

Features:
- Mapa Leaflet interativo com camadas Brasil e MATOPIBA
- Marcador especial: Piracicaba - ESALQ/USP
- LocateControl para geolocalização
- LayersControl para gerenciar camadas
"""
import dash_bootstrap_components as dbc
from dash import dcc, html
from loguru import logger


def create_world_map_layout() -> html.Div:
    """
    Cria layout completo com mapa mundial Leaflet interativo.
    
    Inclui:
    - Camadas GeoJSON (Brasil, MATOPIBA)
    - Marcador especial (Piracicaba/ESALQ)
    - LocateControl (geolocalização)
    - LayersControl (gerenciar camadas)
    
    O conteúdo é inserido via callback (ver map_callbacks.py)
    """
    logger.info("🎨 Criando layout do mapa mundial interativo")
    
    return html.Div([
        # Stores para persistência de dados
        dcc.Store(id='markers-store', data=[]),
        dcc.Store(id='selected-location-store', data=None),
        
        # Geolocalização
        dcc.Geolocation(id='geolocation', high_accuracy=True),
        
        # Modal de resultados
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='modal-title')),
            dbc.ModalBody(id='modal-body'),
            dbc.ModalFooter(
                dbc.Button("Fechar", id="close-modal", className="ms-auto", n_clicks=0)
            ),
        ], id="result-modal", size="lg", is_open=False),
        
        dbc.Container([
            # Header com botões de ação rápida FIXOS
            dbc.Card([
                dbc.CardBody([
                    # Linha 1: Título e Botões de Ação
                    html.Div([
                        # Título à esquerda
                        html.Div([
                            html.I(className="fas fa-globe-americas me-2", 
                                   style={"color": "#2d5016", "font-size": "1.2rem"}),
                            html.Span([
                                "Cálculo de ET",
                                html.Sub("0"),
                                " com Fusão de Dados"
                            ], style={"color": "#2d5016", "font-weight": "600", "font-size": "1.1rem"})
                        ], style={"display": "inline-block"}),
                        
                        # Ações rápidas à direita (sempre visíveis)
                        html.Div([
                            html.Small([
                                html.I(className="fas fa-bolt me-2", style={"color": "#ffc107"}),
                                html.Strong("Ações rápidas:", style={"color": "#2d5016", "margin-right": "10px"})
                            ], style={"display": "inline-block", "margin-right": "10px"}),
                            
                            # Ícones de ação
                            dbc.Button(
                                html.I(className="fas fa-crosshairs fa-lg"),
                                id="use-geolocation-btn",
                                color="info",
                                outline=True,
                                size="sm",
                                className="me-2",
                                style={"width": "40px", "height": "38px"}
                            ),
                            dbc.Tooltip("📍 Usar minha localização atual (GPS)", target="use-geolocation-btn", placement="bottom"),
                            
                            dbc.Button(
                                html.I(className="fas fa-calculator fa-lg"),
                                id="calculate-daily-eto-btn",
                                color="success",
                                outline=True,
                                size="sm",
                                className="me-2",
                                style={"width": "40px", "height": "38px"}
                            ),
                            dbc.Tooltip("🧮 Calcular ETo Diária", target="calculate-daily-eto-btn", placement="bottom"),
                            
                            dbc.Button(
                                html.I(className="fas fa-calendar-alt fa-lg"),
                                id="calculate-period-eto-btn",
                                color="primary",
                                outline=True,
                                size="sm",
                                style={"width": "40px", "height": "38px"}
                            ),
                            dbc.Tooltip("📅 Calcular ETo do Período", target="calculate-period-eto-btn", placement="bottom")
                        ], style={"display": "inline-block", "float": "right"})
                    ], className="d-flex justify-content-between align-items-center mb-2"),
                    
                    # Linha 2: Subtítulo
                    html.P([
                        html.I(className="fas fa-filter me-2"),
                        "Fusão via Ensemble Kalman Filter (EnKF) | ",
                        html.I(className="fas fa-mouse-pointer me-2"),
                        "Clique em qualquer ponto do mapa para calcular ET",
                        html.Sub("0")
                    ], className="text-muted mb-0", style={"font-size": "0.9rem"})
                ])
            ], className="mb-3 shadow-sm"),
            
            # Elemento para mostrar coordenadas (substitui o alerta azul dentro da tab)
            html.Div(id='click-info', className="mb-2", children=''),
            html.Div(id='geolocation-error-msg', className="mb-3", children=''),
            
            # Mapa Mundial Interativo (conteúdo inserido via callback)
            html.Div([
                # Hidden input para manter compatibilidade com callback
                dcc.Store(id="map-tabs", data="tab-leaflet"),
                html.Div(id="map-tab-content", className="p-3")
            ], className="mb-3 card"),
            
            # Accordion de Instruções
            dbc.Accordion([
                dbc.AccordionItem([
                    html.P("📌 Instruções de uso:", className="fw-bold"),
                    html.Ul([
                        html.Li("🗺️ Navegação no Mapa:"),
                        html.Ul([
                            html.Li("Clique em qualquer ponto do mapa para capturar coordenadas e altitude"),
                            html.Li("📍 Use o botão de localização (canto superior esquerdo) para obter sua posição via GPS"),
                            html.Li("🧮 Calcule ETo Diária ou do Período usando os botões de ação rápida acima")
                        ]),
                        html.Li("🌍 Camadas Disponíveis:"),
                        html.Ul([
                            html.Li("🇧🇷 Brasil: Contorno do território brasileiro (verde)"),
                            html.Li("🌾 MATOPIBA: Região agrícola (Maranhão, Tocantins, Piauí, Bahia) em azul"),
                            html.Li("🎓 Piracicaba: Marcador especial destacando a ESALQ/USP"),
                            html.Li("Use o controle de camadas (canto superior direito) para ativar/desativar")
                        ]),
                        html.Li("🌐 Fusão automática de dados climáticos (NASA POWER, MET Norway, NWS USA)"),
                    ])
                ], title="ℹ️ Como usar o mapa")
            ], start_collapsed=True, className="mb-3")
            
        ], fluid=True)
    ])