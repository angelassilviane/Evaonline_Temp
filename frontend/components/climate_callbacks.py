"""
Callbacks para componente de seleção de fontes climáticas.
Gerencia detecção geográfica automática e disponibilidade de fontes.
"""

from typing import List

from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate


@callback(
    Output("single-source-selector", "style"),
    Input("data-fusion-mode", "value"),
    prevent_initial_call=True
)
def toggle_single_source_dropdown(mode: str) -> dict:
    """
    Mostra/esconde dropdown de fonte única baseado no modo selecionado.
    
    Args:
        mode: 'fusion' ou 'single'
        
    Returns:
        dict: Estilo CSS (display: block/none)
    """
    if mode == "single":
        return {"display": "block"}
    return {"display": "none"}


@callback(
    Output("fusion-weights-info", "children"),
    Input("data-fusion-mode", "value"),
    State({"type": "source-checkbox", "source": "nasa_power"}, "value"),
    State({"type": "source-checkbox", "source": "met_norway"}, "value"),
    State({"type": "source-checkbox", "source": "nws_usa"}, "value"),
    prevent_initial_call=True
)
def update_fusion_info(
    mode: str,
    nasa_power: bool,
    met_norway: bool,
    nws_usa: bool
) -> html.Div:
    """
    Atualiza informações sobre fontes selecionadas para fusão.
    
    Args:
        mode: 'fusion' ou 'single'
        nasa_power: Se NASA POWER está selecionado
        met_norway: Se MET Norway está selecionado
        nws_usa: Se NWS está selecionado
        
    Returns:
        html.Div: Informações sobre fontes para fusão
    """
    if mode != "fusion":
        raise PreventUpdate
    
    # Coletar fontes selecionadas
    fusion_sources = []
    if nasa_power:
        fusion_sources.append("NASA POWER")
    if met_norway:
        fusion_sources.append("MET Norway")
    if nws_usa:
        fusion_sources.append("NWS USA")
    
    if not fusion_sources:
        return html.Div([
            html.I(className="bi bi-exclamation-circle me-2"),
            "⚠️ Selecione pelo menos uma fonte para fusão de dados."
        ], className="text-warning")
    
    return html.Div([
        html.I(className="bi bi-check-circle me-2"),
        f"✅ Fusão ativa com {len(fusion_sources)} fonte(s): ",
        html.Strong(", ".join(fusion_sources))
    ], className="text-success")


@callback(
    Output("data-download-format", "options"),
    Output("data-download-format", "value"),
    Input("single-source-dropdown", "value"),
    prevent_initial_call=True
)
def update_download_formats(selected_source: str) -> tuple:
    """
    Atualiza formatos de download disponíveis baseado na fonte selecionada.
    
    Args:
        selected_source: Fonte selecionada no modo single
        
    Returns:
        tuple: (options, default_value)
    """
    # Formatos padrão disponíveis para todas as fontes
    formats = [
        {"label": "CSV (Excel compatível)", "value": "csv"},
        {"label": "JSON (API format)", "value": "json"},
        {"label": "NetCDF (científico)", "value": "nc"}
    ]
    
    return formats, "csv"


@callback(
    Output("attribution-footer", "children"),
    Input({"type": "source-checkbox", "source": "nasa_power"}, "value"),
    Input({"type": "source-checkbox", "source": "met_norway"}, "value"),
    Input({"type": "source-checkbox", "source": "nws_usa"}, "value"),
    prevent_initial_call=True
)
def update_attribution(
    nasa_power: bool,
    met_norway: bool,
    nws_usa: bool
) -> html.Div:
    """
    Atualiza footer com atribuições necessárias baseado em fontes selecionadas.
    
    Args:
        nasa_power: Se NASA POWER está selecionado
        met_norway: Se MET Norway está selecionado
        nws_usa: Se NWS está selecionado
        
    Returns:
        html.Div: Footer com atribuições
    """
    attributions = []
    
    if nasa_power:
        attributions.append(
            html.Div([
                "Data source: ",
                html.A(
                    "NASA POWER",
                    href="https://power.larc.nasa.gov",
                    target="_blank",
                    className="text-decoration-none"
                ),
                " (Public Domain)"
            ])
        )
    
    if met_norway:
        attributions.append(
            html.Div([
                "Data source: ",
                html.A(
                    "MET Norway",
                    href="https://api.met.no",
                    target="_blank",
                    className="text-decoration-none"
                ),
                " (CC-BY 4.0)"
            ])
        )
    
    if nws_usa:
        attributions.append(
            html.Div([
                "Data source: ",
                html.A(
                    "NOAA National Weather Service",
                    href="https://www.weather.gov",
                    target="_blank",
                    className="text-decoration-none"
                ),
                " (US Public Domain)"
            ])
        )
    
    if not attributions:
        raise PreventUpdate
    
    return html.Div(
        attributions,
        className="text-muted small mt-3"
    )


@callback(
    Output("available-sources-store", "data"),
    Input("selected-location-store", "data"),
    prevent_initial_call=True
)
def detect_available_sources(location_data: dict) -> dict:
    """
    Detecta fontes de dados climáticos disponíveis para a localização
    selecionada no mapa mundial.
    
    Utiliza ClimateSourceManager.get_available_sources_for_location()
    que automaticamente:
    - Verifica cobertura geográfica (bbox intersection)
    - Retorna apenas fontes disponíveis para fusão
    
    Args:
        location_data: {"lat": float, "lon": float, "name": str}
        
    Returns:
        dict: Fontes disponíveis com metadados
            {
                "nasa_power": {
                    "available": True,
                    "name": "NASA POWER",
                    "bbox_str": "Global coverage",
                    ...
                },
                ...
            }
    
    Example:
        >>> # Usuário clica em Paris (48.8566°N, 2.3522°E)
        >>> detect_available_sources({
        ...     "lat": 48.8566,
        ...     "lon": 2.3522,
        ...     "name": "Paris"
        ... })
        >>> # Retorna: nasa_power (global) + met_norway (Europa)
    """
    if not location_data:
        raise PreventUpdate
    
    lat = location_data.get("lat")
    lon = location_data.get("lon")
    
    if lat is None or lon is None:
        raise PreventUpdate
    
    # Import necessário (evitar circular imports)
    try:
        from backend.api.services.climate_source_manager import ClimateSourceManager
    except ImportError:
        # Fallback se backend não disponível
        return {}
    
    # Inicializar gerenciador e detectar fontes
    manager = ClimateSourceManager()
    sources = manager.get_available_sources_for_location(
        lat=lat,
        lon=lon,
        exclude_non_commercial=True  
    )
    
    return sources


@callback(
    Output("climate-sources-card", "children"),
    Input("available-sources-store", "data"),
    prevent_initial_call=True
)
def render_climate_source_selector(sources_data: dict):
    """
    Renderiza o seletor de fontes de dados climáticos baseado
    nas fontes disponíveis para a localização selecionada.
    
    Args:
        sources_data: Dicionário de fontes disponíveis do store
            (retornado por detect_available_sources)
    
    Returns:
        Component: Card com seletor de fontes ou mensagem de
                  seleção de localização
    
    Example:
        >>> # Após usuário clicar em Paris
        >>> sources_data = {
        ...     "nasa_power": {"available": True, ...},
        ...     "met_norway": {"available": True, ...}
        ... }
        >>> # Renderiza card com 2 checkboxes (NASA + MET)
    """
    if not sources_data:
        # Mensagem inicial: nenhuma localização selecionada
        return html.Div([
            html.I(
                className="bi bi-info-circle text-muted",
                style={"fontSize": "2rem"}
            ),
            html.P(
                "Selecione uma localização no mapa mundial para "
                "visualizar as fontes de dados climáticos disponíveis.",
                className="text-muted text-center mt-3"
            )
        ], className="text-center py-5")
    
    # Converter dict para list (formato esperado pelo selector)
    available_sources = []
    for source_id, metadata in sources_data.items():
        if metadata.get("available", False):
            available_sources.append({
                "id": source_id,
                "name": metadata["name"],
                "coverage": metadata["coverage"],
                "bbox_str": metadata["bbox_str"],
                "license": metadata["license"],
                "can_fuse": metadata["can_fuse"],
                "can_download": metadata["can_download"],
                "realtime": metadata["realtime"],
                "temporal": metadata["temporal"],
                "available": True,
                "attribution_required": metadata.get(
                    "attribution_required", False
                )
            })
    
    # Import do componente
    from frontend.components.climate_source_selector import create_climate_source_selector

    # Renderizar seletor
    return create_climate_source_selector(available_sources)


# =============================================================================
# CALLBACKS PARA PÁGINA ETo (/eto)
# Seletor de fontes climáticas aparece na página ETo, não no mapa mundial
# =============================================================================

@callback(
    Output("climate-sources-card", "children"),
    Input("url", "pathname"),
    Input("selected-location", "data"),
    prevent_initial_call=False
)
def show_climate_sources_on_eto_page(pathname, location_data):
    """
    Mostra seletor de fontes climáticas na página ETo baseado na localização.
    
    UX: Usuário seleciona localização no mapa → Clica "Calcular ETo Período"
        → Chega na página /eto → Vê este seletor com fontes detectadas
    
    Args:
        pathname: URL atual (só renderiza se /eto)
        location_data: {"lat": float, "lon": float, "name": str}
    
    Returns:
        Component: Card com seletor de fontes ou mensagem
    """
    print(f"🔍 DEBUG show_climate_sources_on_eto_page: pathname={pathname}, location_data={location_data}")
    
    # Só renderizar na página ETo
    if pathname != "/eto":
        print(f"⏭️  DEBUG: Skipping, pathname is not /eto")
        raise PreventUpdate
    
    if not location_data:
        # Usuário chegou direto em /eto sem selecionar localização
        return html.Div([
            html.I(
                className="bi bi-info-circle text-muted",
                style={"fontSize": "2rem"}
            ),
            html.P(
                "📍 Selecione uma localização no mapa mundial primeiro.",
                className="text-muted text-center mt-3"
            ),
            html.P([
                html.A(
                    [html.I(className="fas fa-arrow-left me-2"), "Voltar ao Mapa"],
                    href="/",
                    className="btn btn-outline-primary btn-sm"
                )
            ], className="text-center")
        ], className="text-center py-5")
    
    lat = location_data.get("lat")
    lon = location_data.get("lon")
    
    if lat is None or lon is None:
        raise PreventUpdate
    
    try:
        # Detectar fontes disponíveis para esta localização
        from backend.api.services.climate_source_manager import ClimateSourceManager
        
        manager = ClimateSourceManager()
        sources_dict = manager.get_available_sources_for_location(
            lat=lat,
            lon=lon,
            exclude_non_commercial=False  # Mostrar todas as 3 fontes
        )
        
        # Converter dict para list (formato esperado pelo selector)
        available_sources = []
        for source_id, metadata in sources_dict.items():
            if metadata.get("available", False):
                available_sources.append({
                    "id": source_id,
                    "name": metadata["name"],
                    "coverage": metadata["coverage"],
                    "bbox_str": metadata["bbox_str"],
                    "license": metadata["license"],
                    "can_fuse": metadata["can_fuse"],
                    "can_download": metadata["can_download"],
                    "realtime": metadata["realtime"],
                    "temporal": metadata["temporal"],
                    "available": True,
                    "attribution_required": metadata.get(
                        "attribution_required", False
                    )
                })
        
        # Renderizar seletor
        from frontend.components.climate_source_selector import create_climate_source_selector
        
        return create_climate_source_selector(available_sources)
    
    except Exception as e:
        # Log erro mas retorna mensagem amigável
        print(f"Erro ao detectar fontes para ({lat}, {lon}): {e}")
        return html.Div([
            html.I(className="bi bi-exclamation-triangle text-warning me-2"),
            html.Strong("Erro ao detectar fontes disponíveis. "),
            "Tente selecionar a localização novamente."
        ], className="alert alert-warning")

