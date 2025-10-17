"""
Sistema de tabs para mapas mundiais (padrão oficial dbc.Tabs).
Ref: https://dash-bootstrap-components.opensource.faculty.ai/docs/components/tabs/

✅ Tab 1: Mapa Leaflet (calcular ETo)
✅ Tab 2: Mapa Plotly (6.738 cidades)
"""
import dash_bootstrap_components as dbc
from dash import dcc, html
from loguru import logger


def create_world_map_layout() -> html.Div:
    """
    Cria layout completo com sistema de tabs (padrão oficial).
    
    Estrutura:
        dbc.Card([
            dbc.CardHeader(dbc.Tabs([...])),
            dbc.CardBody(id="map-tab-content")
        ])
    
    O conteúdo é inserido via callback (ver world_map_tabs_callback.py)
    """
    logger.info("🎨 Criando layout com tabs do mapa mundial")
    
    return html.Div([
        # Stores para persistência de dados
        dcc.Store(id='markers-store', data=[]),
        dcc.Store(id='favorites-store', data=[], storage_type='local'),
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
                                className="me-2",
                                style={"width": "40px", "height": "38px"}
                            ),
                            dbc.Tooltip("📅 Calcular ETo do Período", target="calculate-period-eto-btn", placement="bottom"),
                            
                            dbc.Button(
                                html.I(className="fas fa-star fa-lg"),
                                id="save-favorite-btn",
                                color="warning",
                                outline=True,
                                size="sm",
                                style={"width": "40px", "height": "38px"}
                            ),
                            dbc.Tooltip("⭐ Salvar nos favoritos", target="save-favorite-btn", placement="bottom")
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
            
            # SISTEMA DE TABS - Usando dcc.Tabs (nativo do Dash)
            html.Div([
                dcc.Tabs(
                    id="map-tabs",
                    value="tab-leaflet",
                    children=[
                        dcc.Tab(
                            label="🌍 Mapa Mundial Interativo",
                            value="tab-leaflet",
                            className="custom-tab",
                            selected_className="custom-tab-selected"
                        ),
                        dcc.Tab(
                            label="📍 Explorar Cidades (6.738)",
                            value="tab-plotly",
                            className="custom-tab",
                            selected_className="custom-tab-selected"
                        ),
                    ],
                    className="custom-tabs-container"
                ),
                html.Div(id="map-tab-content", className="p-3")
            ], className="mb-3 card"),
            
            # Accordion de Instruções
            dbc.Accordion([
                dbc.AccordionItem([
                    html.P("📌 Instruções de uso:", className="fw-bold"),
                    html.Ul([
                        html.Li("🗺️ Tab 1 (Mapa Mundial Interativo):"),
                        html.Ul([
                            html.Li("Clique em qualquer ponto do mapa para capturar coordenadas e altitude"),
                            html.Li("📍 Use 'Minha Localização' para obter sua posição atual via GPS"),
                            html.Li("🧮 Calcule ETo Diária ou do Período usando os botões de ação rápida"),
                            html.Li("⭐ Salve até 20 localizações favoritas para acesso rápido")
                        ]),
                        html.Li("📊 Tab 2 (Explorar Cidades):"),
                        html.Ul([
                            html.Li("Visualize a distribuição de 6.738 cidades mundiais no mapa"),
                            html.Li("Passe o mouse sobre os pontos para ver detalhes das cidades")
                        ]),
                        html.Li("🌐 Fusão automática de 3 fontes climáticas (NASA POWER, MET Norway, NWS USA)"),
                    ])
                ], title="ℹ️ Como usar o mapa")
            ], start_collapsed=True, className="mb-3"),
            
            # Seção de Favoritos
            html.Div([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="fas fa-star me-2", style={"color": "#ffc107"}),
                            html.Strong("Favoritos "),
                            html.Span(id='favorites-count', className="badge bg-secondary ms-2")
                        ], style={"display": "inline-block"}),
                        dbc.Button(
                            [html.I(className="fas fa-trash me-2"), "Limpar Todos"],
                            id="clear-all-favorites-btn",
                            color="danger",
                            size="sm",
                            outline=True,
                            className="float-end"
                        )
                    ]),
                    dbc.CardBody([
                        # Controles de paginação
                        dbc.Row([
                            dbc.Col([
                                html.Label("Itens por página:", className="me-2"),
                                dcc.Dropdown(
                                    id='favorites-page-size',
                                    options=[
                                        {'label': '5', 'value': 5},
                                        {'label': '10', 'value': 10},
                                        {'label': '20', 'value': 20}
                                    ],
                                    value=5,
                                    clearable=False,
                                    style={'width': '100px', 'display': 'inline-block'}
                                )
                            ], width=6),
                            dbc.Col([
                                html.Div(id='favorites-current-page', 
                                        style={'display': 'none'}, 
                                        children=1)
                            ], width=6)
                        ], className="mb-3"),
                        
                        # Lista de favoritos
                        html.Div(id='favorites-list'),
                        
                        # Paginação
                        dbc.Row([
                            dbc.Col([
                                dbc.ButtonGroup([
                                    dbc.Button("◀ Anterior", id="favorites-prev-page", 
                                             outline=True, color="secondary", size="sm"),
                                    dbc.Button(id="favorites-pagination-info", 
                                             color="light", size="sm", disabled=True),
                                    dbc.Button("Próximo ▶", id="favorites-next-page", 
                                             outline=True, color="secondary", size="sm")
                                ], className="w-100")
                            ])
                        ], id="favorites-pagination", className="mt-3")
                    ])
                ], className="shadow-sm")
            ]),
            
        ], fluid=True),
        
        # Modal de confirmação para limpar favoritos
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Confirmar Exclusão")),
            dbc.ModalBody([
                html.P(id='clear-favorites-count', className="mb-3"),
                html.P("Esta ação não pode ser desfeita.", className="text-danger")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="cancel-clear-favorites", className="me-2"),
                dbc.Button("Confirmar", id="confirm-clear-favorites", color="danger")
            ])
        ], id="clear-favorites-modal", is_open=False),
    ])
