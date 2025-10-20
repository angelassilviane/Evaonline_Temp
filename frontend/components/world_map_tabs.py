"""
Mapa mundial interativo com Leaflet - Otimizado para produção.

Features otimizadas:
- Cache agressivo para GeoJSON
- Lazy loading de camadas
- Performance monitoring
- Tratamento de erro robusto
- Internacionalização
"""
import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import dcc, html
from loguru import logger

# Importar utilitário de MATOPIBA otimizado
try:
    from frontend.utils.matopiba import get_matopiba_geojson_with_clustering
except ImportError as e:
    logger.warning(f"MATOPIBA utils não disponíveis: {e}")
    get_matopiba_geojson_with_clustering = None


class GeoJSONManager:
    """Gerencia carregamento e cache de arquivos GeoJSON."""
    
    def __init__(self):
        self._cache = {}
        self._load_times = {}
    
    @lru_cache(maxsize=10)
    def load_geojson(self, filename: str) -> Optional[Dict]:
        """
        Carrega arquivo GeoJSON com cache e monitoramento de performance.
        
        Args:
            filename: Nome do arquivo GeoJSON
            
        Returns:
            Dict: Dados GeoJSON ou None se erro
        """
        cache_key = f"geojson_{filename}"
        
        # Verificar cache primeiro
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        geojson_path = (
            Path(__file__).parent.parent.parent / 
            'data' / 'geojson' / filename
        )
        
        if not geojson_path.exists():
            logger.error(f"❌ Arquivo GeoJSON não encontrado: {geojson_path}")
            return None
        
        start_time = time.time()
        
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            load_time = time.time() - start_time
            self._load_times[filename] = load_time
            
            # Validar estrutura básica do GeoJSON
            if not self._validate_geojson(geojson_data):
                logger.warning(f"⚠️ GeoJSON {filename} com estrutura inválida")
                return None
            
            # Cache por 1 hora
            self._cache[cache_key] = geojson_data
            
            feature_count = len(geojson_data.get('features', []))
            logger.info(f"✅ GeoJSON {filename} carregado: {feature_count} features, {load_time:.3f}s")
            
            return geojson_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {filename}: {e}")
            return None
    
    def _validate_geojson(self, geojson_data: Dict) -> bool:
        """Valida estrutura básica do GeoJSON."""
        if not isinstance(geojson_data, dict):
            return False
        
        if geojson_data.get('type') != 'FeatureCollection':
            return False
        
        if 'features' not in geojson_data:
            return False
        
        return True
    
    def get_performance_stats(self) -> Dict:
        """Retorna estatísticas de performance."""
        return {
            'cached_files': len(self._cache),
            'load_times': self._load_times
        }


# Instância global do gerenciador
geojson_manager = GeoJSONManager()


def load_geojson(filename: str) -> Optional[Dict]:
    """
    Função de compatibilidade para carregamento de GeoJSON.
    
    Args:
        filename: Nome do arquivo GeoJSON
        
    Returns:
        Dict: Dados GeoJSON ou None
    """
    return geojson_manager.load_geojson(filename)


def create_world_map_layout(lang: str = "pt") -> html.Div:
    """
    Cria layout completo com mapa mundial Leaflet interativo otimizado.
    
    Args:
        lang: Idioma para internacionalização
        
    Returns:
        html.Div: Layout completo do mapa
    """
    logger.info("🎨 Criando layout do mapa mundial interativo (otimizado)")
    
    # Textos internacionalizados
    texts = _get_map_texts(lang)
    
    try:
        # Carregar camadas GeoJSON de forma otimizada
        map_children = _create_map_layers()
        
        return html.Div([
            # Stores para estado da aplicação
            dcc.Store(id='markers-store', data=[], storage_type='memory'),
            dcc.Store(id='selected-location-store', data=None, storage_type='session'),
            dcc.Store(id='map-state-store', data={
                'center': [-15, -47],
                'zoom': 4,
                'loaded_layers': ['base', 'brasil', 'matopiba']
            }),
            
            # Geolocalização
            dcc.Geolocation(
                id='geolocation', 
                high_accuracy=True,
                position_options={
                    'enableHighAccuracy': True,
                    'timeout': 10000,
                    'maximumAge': 60000
                },
                # Em produção, considerar user permission
                # location=None  # Solicitar permissão sob demanda
            ),
            
            # Modal para resultados
            _create_results_modal(),
            
            # Layout principal
            dbc.Container([
                # Header com ações
                _create_map_header(texts),
                
                # Informações de coordenadas
                html.Div(id='click-info', className="mb-2"),
                html.Div(id='geolocation-error-msg', className="mb-3"),
                
                # Mapa interativo
                _create_map_component(map_children),
                
                # Instruções de uso
                _create_instructions_accordion(texts),
                
                # Performance stats (apenas em debug)
                _create_performance_footer() if logger._core.min_level <= 10 else None
                
            ], fluid=True, className="px-0")  # Remove padding lateral
            
        ], id="world-map-container")
        
    except Exception as e:
        logger.error(f"❌ Erro crítico ao criar layout do mapa: {e}")
        return _create_error_fallback(lang)


def _get_map_texts(lang: str) -> Dict:
    """Retorna textos traduzidos para o mapa."""
    texts = {
        "pt": {
            "title": "Cálculo de ET₀ com Fusão de Dados",
            "subtitle": "Fusão via Ensemble Kalman Filter (EnKF) | Clique em qualquer ponto do mapa para calcular ET₀",
            "quick_actions": "Ações rápidas:",
            "geolocation_tooltip": "📍 Usar minha localização atual (GPS)",
            "daily_eto_tooltip": "🧮 Calcular ETo Diária", 
            "period_eto_tooltip": "📅 Calcular ETo do Período",
            "instructions_title": "ℹ️ Como usar o mapa",
            "instructions": [
                "🗺️ Navegação no Mapa:",
                [
                    "Clique em qualquer ponto do mapa para capturar coordenadas e altitude",
                    "Use o botão de localização (canto superior esquerdo) para obter sua posição via GPS",
                    "Use o MeasureControl (canto superior direito) para medir distâncias/áreas", 
                    "Calcule ETo Diária ou do Período usando os botões de ação rápida acima"
                ],
                "🌍 Camadas Disponíveis:",
                [
                    "Brasil: Contorno do território brasileiro (verde)",
                    "MATOPIBA: Região agrícola (Maranhão, Tocantins, Piauí, Bahia) em azul",
                    "Piracicaba: Marcador especial destacando a ESALQ/USP",
                    "Use os controles no canto superior direito para funcionalidades extras",
                    "Escala: Bottom-left (ScaleControl) mostra distâncias em km",
                    "Tela cheia: Top-right (FullScreenControl) para visualização expandida"
                ],
                "🌐 Fusão automática de dados climáticos (NASA POWER, MET Norway, NWS USA)"
            ]
        },
        "en": {
            "title": "ET₀ Calculation with Data Fusion", 
            "subtitle": "Fusion via Ensemble Kalman Filter (EnKF) | Click anywhere on the map to calculate ET₀",
            "quick_actions": "Quick actions:",
            "geolocation_tooltip": "📍 Use my current location (GPS)",
            "daily_eto_tooltip": "🧮 Calculate Daily ETo",
            "period_eto_tooltip": "📅 Calculate Period ETo",
            "instructions_title": "ℹ️ How to use the map",
            "instructions": [
                "🗺️ Map Navigation:",
                [
                    "Click anywhere on the map to capture coordinates and altitude",
                    "Use the location button (top left) to get your position via GPS",
                    "Use MeasureControl (top right) to measure distances/areas",
                    "Calculate Daily or Period ETo using the quick action buttons above"
                ],
                "🌍 Available Layers:",
                [
                    "Brazil: Brazilian territory outline (green)",
                    "MATOPIBA: Agricultural region (Maranhão, Tocantins, Piauí, Bahia) in blue", 
                    "Piracicaba: Special marker highlighting ESALQ/USP",
                    "Use controls in top right for extra functionality",
                    "Scale: Bottom-left shows distances in km",
                    "Full screen: Top-right for expanded view"
                ],
                "🌐 Automatic climate data fusion (NASA POWER, MET Norway, NWS USA)"
            ]
        }
    }
    
    return texts.get(lang, texts["pt"])


def _create_map_layers() -> List:
    """Cria e configura todas as camadas do mapa."""
    map_children = []
    
    # 1. Camada base principal com fallbacks
    base_layers = [
        dl.TileLayer(
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution='© OpenStreetMap contributors',
            noWrap=True,
            maxZoom=19,
            id="base-layer-osm"
        ),
        # Camada satélite como alternativa
        dl.TileLayer(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attribution="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
            noWrap=True,
            maxZoom=19,
            id="base-layer-satellite"
        )
    ]
    
    map_children.extend(base_layers)
    
    # 2. Camada Brasil (GeoJSON)
    brasil_geojson = geojson_manager.load_geojson('BR_UF_2024.geojson')
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
                    },
                    'onEachFeature': _create_brasil_popup
                },
                hoverStyle={
                    'color': '#218838', 
                    'fillColor': '#218838',
                    'fillOpacity': 0.2
                }
            )
        )
        logger.debug("✅ Camada Brasil carregada")
    
    # 3. Camada MATOPIBA com clustering otimizado
    matopiba_data = _load_matopiba_layer()
    if matopiba_data:
        map_children.append(matopiba_data)
        logger.debug("✅ Camada MATOPIBA carregada")
    
    # 4. Marcador especial Piracicaba/ESALQ
    map_children.append(_create_piracicaba_marker())
    
    # 5. Layer group para markers dinâmicos
    map_children.append(
        dl.LayerGroup(id='dynamic-markers', children=[])
    )
    
    # 6. Controles do mapa
    map_children.extend(_create_map_controls())
    
    logger.info(f"✅ {len(map_children)} camadas criadas para o mapa")
    return map_children


def _create_brasil_popup(feature, layer):
    """Cria popup para features do Brasil."""
    if feature.get('properties'):
        props = feature['properties']
        state_name = props.get('NM_ESTADO', 'Estado')
        state_uf = props.get('SIGLA_UF', 'UF')
        
        popup_content = f"""
        <div style="min-width: 150px;">
            <h6 style="margin: 0 0 8px 0; color: #2d5016;">{state_name}</h6>
            <hr style="margin: 4px 0;">
            <p style="margin: 0; font-size: 12px;">
                <strong>UF:</strong> {state_uf}<br>
                <strong>Região:</strong> {props.get('NM_REGIAO', 'N/A')}
            </p>
        </div>
        """
        layer.bindPopup(popup_content)


def _load_matopiba_layer() -> Optional[dl.GeoJSON]:
    """Carrega camada MATOPIBA com tratamento de erro."""
    if not get_matopiba_geojson_with_clustering:
        return None
    
    try:
        matopiba_geojson = get_matopiba_geojson_with_clustering()
        if matopiba_geojson and matopiba_geojson.get('features'):
            return dl.GeoJSON(
                id='matopiba-layer',
                data=matopiba_geojson,
                cluster=True,
                clusterOptions={
                    'maxClusterRadius': 50,
                    'disableClusteringAtZoom': 12
                },
                zoomToBoundsOnClick=True
            )
    except Exception as e:
        logger.error(f"❌ Erro ao carregar MATOPIBA: {e}")
    
    return None


def _create_piracicaba_marker() -> dl.Marker:
    """Cria marcador especial para Piracicaba/ESALQ."""
    return dl.Marker(
        id="piracicaba-marker",
        position=[-22.7253, -47.6490],  # Coordenadas precisas da ESALQ
        children=[
            dl.Tooltip("Piracicaba - ESALQ/USP 🎓"),
            dl.Popup([
                html.Div([
                    html.H6("🎓 Piracicaba - ESALQ/USP", 
                           className="mb-2", 
                           style={"color": "#2d5016"}),
                    html.P([
                        html.Strong("Escola Superior de Agricultura"),
                        html.Br(),
                        "Luiz de Queiroz - Universidade de São Paulo",
                        html.Br(),
                        html.Br(),
                        html.Small([
                            "📍 22°43'31\"S, 47°38'57\"W",
                            html.Br(), 
                            "🏔️ Elevação: 527 m",
                            html.Br(),
                            "🌡️ Clima: Tropical úmido"
                        ], className="text-muted")
                    ], className="mb-2"),
                    html.Hr(className="my-2"),
                    html.A(
                        "🌐 Visitar site da ESALQ",
                        href="https://www.esalq.usp.br/",
                        target="_blank",
                        className="btn btn-success btn-sm w-100",
                        style={"textDecoration": "none"}
                    )
                ], style={"minWidth": "200px"})
            ], maxWidth=300)
        ],
        icon={
            'iconUrl': 'https://cdn-icons-png.flaticon.com/512/197/197386.png',  # Bandeira Brasil
            'iconSize': [30, 30],
            'iconAnchor': [15, 30],
            'popupAnchor': [0, -30],
            'className': 'university-marker'
        }
    )


def _create_map_controls() -> List:
    """Cria controles interativos do mapa."""
    return [
        # Layers control para alternar entre camadas base
        dl.LayersControl(
            position="topright",
            collapsed=True
        ),
        
        # Geolocalização
        dl.LocateControl(
            position='topleft',
            strings={
                'title': 'Mostrar minha localização',
                'popup': 'Você está aqui!'
            },
            locateOptions={
                'enableHighAccuracy': True,
                'maxZoom': 16,
                'timeout': 10000
            },
            drawCircle=True,
            showPopup=True
        ),
        
        # Escala
        dl.ScaleControl(
            position='bottomleft',
            metric=True,
            imperial=False
        ),
        
        # Tela cheia
        dl.FullScreenControl(
            position='topright'
        ),
        
        # Medição
        dl.MeasureControl(
            position='topright',
            primaryLengthUnit='kilometers',
            secondaryLengthUnit='meters',
            primaryAreaUnit='hectares',
            secondaryAreaUnit='squaremeters',
            activeColor='#2d5016',
            completedColor='#28a745'
        )
    ]


def _create_results_modal() -> dbc.Modal:
    """Cria modal para exibição de resultados."""
    return dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle(id='modal-title'),
            close_button=True
        ),
        dbc.ModalBody(
            html.Div(id='modal-body')
        ),
        dbc.ModalFooter([
            dbc.Button(
                "Fechar",
                id="close-modal",
                color="secondary",
                className="ms-auto"
            ),
            dbc.Button(
                "Calcular ETo",
                id="modal-calculate-eto",
                color="primary",
                className="ms-2"
            )
        ])
    ], id="result-modal", size="lg", scrollable=True, is_open=False)


def _create_map_header(texts: Dict) -> dbc.Card:
    """Cria header do mapa com ações rápidas."""
    return dbc.Card([
        dbc.CardBody([
            # Linha 1: Título e ações
            html.Div([
                # Título
                html.Div([
                    html.I(
                        className="fas fa-globe-americas me-2",
                        style={"color": "#2d5016", "fontSize": "1.3rem"}
                    ),
                    html.Span(
                        texts["title"],
                        style={
                            "color": "#2d5016", 
                            "fontWeight": "600", 
                            "fontSize": "1.2rem"
                        }
                    )
                ], className="flex-grow-1"),
                
                # Ações rápidas
                html.Div([
                    html.Small([
                        html.I(
                            className="fas fa-bolt me-2",
                            style={"color": "#ffc107"}
                        ),
                        html.Strong(
                            texts["quick_actions"],
                            style={"color": "#2d5016", "marginRight": "10px"}
                        )
                    ]),
                    
                    # Botões de ação
                    dbc.ButtonGroup([
                        dbc.Button(
                            html.I(className="fas fa-crosshairs fa-lg"),
                            id="use-geolocation-btn",
                            color="info",
                            outline=True,
                            size="sm",
                            className="action-btn"
                        ),
                        dbc.Button(
                            html.I(className="fas fa-calculator fa-lg"),
                            id="calculate-daily-eto-btn", 
                            color="success",
                            outline=True,
                            size="sm",
                            className="action-btn"
                        ),
                        dbc.Button(
                            html.I(className="fas fa-calendar-alt fa-lg"),
                            id="calculate-period-eto-btn",
                            color="primary", 
                            outline=True,
                            size="sm",
                            className="action-btn"
                        )
                    ], className="ms-2")
                    
                ], className="d-flex align-items-center")
                
            ], className="d-flex justify-content-between align-items-center mb-2"),
            
            # Linha 2: Subtítulo
            html.P(
                texts["subtitle"],
                className="text-muted mb-0",
                style={"fontSize": "0.9rem"}
            )
            
        ])
    ], className="mb-3 shadow-sm")


def _create_map_component(map_children: List) -> dbc.Card:
    """Cria componente do mapa principal."""
    return dbc.Card([
        dbc.CardBody([
            dl.Map(
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
                    'height': '65vh',  # Viewport height responsivo
                    'minHeight': '500px',
                    'cursor': 'pointer',
                    'borderRadius': '8px'
                },
                dragging=True,
                scrollWheelZoom=True,
                doubleClickZoom=True,
                boxZoom=True,
                keyboard=True,
                touchZoom=True
            )
        ], className="p-2")  # Padding reduzido
    ], className="mb-3 shadow-sm")


def _create_instructions_accordion(texts: Dict) -> dbc.Accordion:
    """Cria accordion com instruções de uso."""
    instructions = texts["instructions"]
    
    instruction_items = []
    for i, item in enumerate(instructions):
        if isinstance(item, list):
            # Sub-lista
            instruction_items.extend([
                html.Li(sub_item, className="ms-3 mb-1")
                for sub_item in item
            ])
        else:
            # Item principal
            instruction_items.append(
                html.Li(item, className="fw-medium mb-2")
            )
    
    return dbc.Accordion([
        dbc.AccordionItem([
            html.Ul(instruction_items, className="mb-0")
        ], title=texts["instructions_title"])
    ], start_collapsed=True, className="mb-3", flush=True)


def _create_performance_footer() -> html.Div:
    """Cria footer com estatísticas de performance (apenas debug)."""
    stats = geojson_manager.get_performance_stats()
    
    return html.Div([
        html.Hr(),
        html.Small([
            "📊 Performance: ",
            f"{stats['cached_files']} arquivos em cache | ",
            " | ".join([f"{k}: {v:.3f}s" for k, v in stats['load_times'].items()])
        ], className="text-muted")
    ], className="mt-3")


def _create_error_fallback(lang: str) -> html.Div:
    """Cria fallback em caso de erro crítico."""
    error_texts = {
        "pt": {
            "title": "⚠️ Mapa Indisponível",
            "message": "O mapa interativo está temporariamente indisponível.",
            "action": "Recarregar a página"
        },
        "en": {
            "title": "⚠️ Map Unavailable", 
            "message": "The interactive map is temporarily unavailable.",
            "action": "Reload the page"
        }
    }
    
    texts = error_texts.get(lang, error_texts["pt"])
    
    return html.Div([
        dbc.Alert([
            html.H4(texts["title"], className="alert-heading"),
            html.P(texts["message"]),
            html.Hr(),
            dbc.Button(
                texts["action"],
                color="primary",
                id="reload-page-btn"
            )
        ], color="warning", className="m-4 text-center")
    ])


# Funções de utilidade para debugging
def get_map_performance_stats() -> Dict:
    """Retorna estatísticas de performance do mapa para monitoring."""
    return {
        'geojson_manager': geojson_manager.get_performance_stats(),
        'timestamp': time.time()
    }


def clear_geojson_cache():
    """Limpa cache de GeoJSON (útil para desenvolvimento)."""
    geojson_manager._cache.clear()
    logger.info("🗑️ Cache de GeoJSON limpo")
