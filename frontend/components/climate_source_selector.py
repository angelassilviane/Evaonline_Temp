"""
Componente de seleção de fontes de dados climáticos - Otimizado para produção.
"""
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import dash_bootstrap_components as dbc
from dash import dcc, html
from loguru import logger


class ClimateSourceManager:
    """Gerencia fontes de dados climáticos com cache e validação."""
    
    def __init__(self):
        self._source_cache = {}
        self._translations_cache = {}
    
    def validate_source_data(self, source: Dict) -> Tuple[bool, str]:
        """
        Valida dados da fonte climática.
        
        Args:
            source: Dicionário com dados da fonte
            
        Returns:
            Tuple (is_valid, error_message)
        """
        required_fields = ['id', 'name', 'available', 'coverage', 'license']
        
        for field in required_fields:
            if field not in source:
                return False, f"Campo obrigatório ausente: {field}"
        
        if not isinstance(source['available'], bool):
            return False, "Campo 'available' deve ser booleano"
        
        valid_licenses = ['public_domain', 'cc_by_4.0', 'non_commercial']
        if source['license'] not in valid_licenses:
            return False, f"Licença inválida: {source['license']}"
        
        return True, ""

    @lru_cache(maxsize=100)
    def get_source_tooltip(self, source_id: str) -> str:
        """
        Retorna tooltip com cache para fonte específica.
        
        Args:
            source_id: ID da fonte de dados
            
        Returns:
            str: Texto do tooltip
        """
        tooltips = {
            "nasa_power": (
                "🌍 NASA POWER: Dados climáticos da NASA (domínio público). "
                "Cobertura global desde 1981. Dados diários com 1-2 dias de "
                "atraso. Alta confiabilidade para cálculo de ETo. "
                "✅ Livre para fusão e download sem restrições."
            ),
            "met_norway": (
                "🇳🇴 MET Norway: Serviço meteorológico norueguês (CC-BY 4.0). "
                "Cobertura: Europa (35°N-72°N, 25°W-45°E). "
                "Dados horários de alta precisão para refinamento regional. "
                "✅ Livre para fusão e download com atribuição obrigatória."
            ),
            "nws_usa": (
                "🇺🇸 National Weather Service: Serviço oficial dos EUA "
                "(domínio público - NOAA). "
                "Cobertura: Estados Unidos continental (24°N-49°N, 125°W-66°W). "
                "Dados horários governamentais oficiais. "
                "✅ Livre para fusão e download sem restrições."
            ),
            "open_meteo": (
                "🌤️ Open-Meteo: Dados climáticos de múltiplas fontes (CC-BY 4.0). "
                "Cobertura global com dados em tempo real e históricos. "
                "✅ Livre para fusão e download com atribuição."
            )
        }
        
        return tooltips.get(source_id, "ℹ️ Informações detalhadas não disponíveis para esta fonte.")


# Instância global para reutilização
source_manager = ClimateSourceManager()


@lru_cache(maxsize=10)
def get_translations(lang: str = "pt") -> Dict:
    """
    Retorna traduções com cache.
    
    Args:
        lang: Idioma (pt/en)
        
    Returns:
        Dict: Dicionário com traduções
    """
    translations = {
        "pt": {
            "title": "🌐 Fontes de Dados Disponíveis",
            "coverage": "Cobertura",
            "temporal": "Resolução",
            "realtime": "Tempo Real",
            "license": "Licença",
            "yes": "Sim",
            "no": "Não",
            "mode_title": "🎛️ Modo de Operação",
            "fusion_mode": "Fusão de Dados (Recomendado)",
            "fusion_desc": "Combina múltiplas fontes para maior precisão usando Ensemble Kalman Filter",
            "single_mode": "Fonte Única",
            "single_desc": "Usa apenas uma fonte selecionada - mais rápido",
            "info": "💡 Fontes detectadas automaticamente para esta localização",
            "commercial_ok": "Uso Comercial OK",
            "global": "Global",
            "regional": "Regional",
            "hourly": "Horária",
            "daily": "Diária",
            "unavailable": "Indisponível",
            "bbox": "Área de cobertura",
            "select_all": "Selecionar Todas",
            "deselect_all": "Desselecionar Todas",
            "source_details": "Detalhes da Fonte",
            "attribution_required": "Atribuição Obrigatória"
        },
        "en": {
            "title": "🌐 Available Data Sources",
            "coverage": "Coverage",
            "temporal": "Resolution", 
            "realtime": "Real Time",
            "license": "License",
            "yes": "Yes",
            "no": "No",
            "mode_title": "🎛️ Operation Mode",
            "fusion_mode": "Data Fusion (Recommended)",
            "fusion_desc": "Combines multiple sources for higher accuracy using Ensemble Kalman Filter",
            "single_mode": "Single Source", 
            "single_desc": "Uses only one selected source - faster",
            "info": "💡 Sources automatically detected for this location",
            "commercial_ok": "Commercial Use OK",
            "global": "Global",
            "regional": "Regional",
            "hourly": "Hourly",
            "daily": "Daily",
            "unavailable": "Unavailable",
            "bbox": "Coverage area",
            "select_all": "Select All",
            "deselect_all": "Deselect All",
            "source_details": "Source Details",
            "attribution_required": "Attribution Required"
        }
    }
    
    return translations.get(lang, translations["pt"])


def create_climate_source_selector(
    available_sources: List[Dict],
    lang: str = "pt",
    enable_bulk_actions: bool = True
) -> dbc.Card:
    """
    Cria card com seletor de fontes de dados climáticos otimizado.
    
    Args:
        available_sources: Lista de fontes disponíveis para a localidade
        lang: Idioma para traduções
        enable_bulk_actions: Habilita seleção/deseleção em massa
        
    Returns:
        dbc.Card: Card com seletor de fontes
        
    Raises:
        ValueError: Se dados de fonte forem inválidos
    """
    logger.info(f"🔄 Criando seletor de fontes para {len(available_sources)} fontes")
    
    translations = get_translations(lang)
    
    # Validar e filtrar fontes disponíveis
    active_sources = []
    invalid_sources = []
    
    for source in available_sources:
        is_valid, error_msg = source_manager.validate_source_data(source)
        if is_valid and source.get("available", False):
            active_sources.append(source)
        else:
            invalid_sources.append((source.get('id', 'unknown'), error_msg))
    
    # Log de fontes inválidas
    if invalid_sources:
        logger.warning(f"Fontes inválidas detectadas: {invalid_sources}")
    
    # Caso sem fontes disponíveis
    if not active_sources:
        return _create_no_sources_card(translations)
    
    # Criar interface otimizada
    return _create_sources_selector(active_sources, translations, enable_bulk_actions)


def _create_no_sources_card(translations: Dict) -> dbc.Card:
    """Cria card para quando não há fontes disponíveis."""
    return dbc.Card([
        dbc.CardHeader(
            html.H5(translations["title"], className="mb-0")
        ),
        dbc.CardBody([
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle me-2"),
                "🚫 Nenhuma fonte de dados disponível para esta localização.",
                html.Br(),
                html.Small(
                    "Tente selecionar uma localização diferente no mapa.",
                    className="text-muted"
                )
            ], color="warning", className="mb-0")
        ])
    ], className="mb-3 shadow-sm")


def _create_sources_selector(
    active_sources: List[Dict],
    translations: Dict,
    enable_bulk_actions: bool
) -> dbc.Card:
    """Cria o seletor de fontes com todas as funcionalidades."""
    
    # Header com ações em massa
    header_children = [html.H5(translations["title"], className="mb-0")]
    
    if enable_bulk_actions and len(active_sources) > 1:
        header_children.extend([
            html.Div([
                dbc.Button(
                    translations["select_all"],
                    id="select-all-sources",
                    color="outline-primary",
                    size="sm",
                    className="me-2"
                ),
                dbc.Button(
                    translations["deselect_all"], 
                    id="deselect-all-sources",
                    color="outline-secondary",
                    size="sm"
                )
            ], className="ms-auto")
        ])
    
    # Cards das fontes
    source_cards = [
        _create_source_card(source, translations) 
        for source in active_sources
    ]
    
    return dbc.Card([
        # Header
        dbc.CardHeader(
            html.Div(header_children, className="d-flex align-items-center")
        ),
        
        # Body
        dbc.CardBody([
            # Informação sobre detecção automática
            dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                translations["info"],
                html.Br(),
                html.Small(
                    f"{len(active_sources)} fonte(s) compatível(s) detectada(s)",
                    className="text-muted"
                )
            ], color="info", className="mb-3"),
            
            # Cards das fontes
            html.Div(source_cards, id="sources-container"),
            
            # Contador de seleção
            html.Div([
                html.Small([
                    "📊 ",
                    html.Span(id="selected-sources-count", children="0"),
                    f" de {len(active_sources)} fonte(s) selecionada(s)"
                ], className="text-muted")
            ], className="mb-3 text-center"),
            
            # Seletor de modo de operação
            _create_operation_mode_selector(translations, active_sources),
            
            # Informações de fusão
            html.Div(id="fusion-info-container", className="mt-3")
            
        ])
    ], className="mb-3 shadow-sm", id="climate-sources-selector")


def _create_source_card(source: Dict, translations: Dict) -> dbc.Card:
    """Cria card individual para cada fonte de dados."""
    source_id = source["id"]
    
    # Badges com tooltips
    coverage_badge, coverage_tooltip = _create_coverage_badge(source, translations, source_id)
    temporal_badge = _create_temporal_badge(source, translations)
    realtime_badge = _create_realtime_badge(source, translations)
    license_badge, license_tooltip = _create_license_badge(source, translations, source_id)
    
    # Tooltip de informações detalhadas
    detail_tooltip = dbc.Tooltip(
        source_manager.get_source_tooltip(source_id),
        target=f"source-info-{source_id}",
        placement="top"
    )
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                # Checkbox de seleção
                dbc.Checkbox(
                    id={"type": "source-checkbox", "source": source_id},
                    label="",
                    value=True,  # Default selecionado para fusão
                    className="float-end mt-1"
                ),
                
                # Nome e badges
                html.Div([
                    html.H6([
                        # Ícone de informações
                        html.I(
                            className="bi bi-info-circle text-primary me-1",
                            id=f"source-info-{source_id}",
                            style={"cursor": "help"}
                        ),
                        source["name"],
                        coverage_badge,
                        temporal_badge, 
                        realtime_badge,
                        license_badge
                    ], className="mb-2"),
                    
                    # Tooltips
                    coverage_tooltip,
                    license_tooltip,
                    detail_tooltip
                ]),
                
                # Metadados adicionais (se disponíveis)
                _create_source_metadata(source)
                
            ]),
        ])
    ], className="mb-2 border-0 shadow-sm", style={"backgroundColor": "#f8f9fa"})


def _create_coverage_badge(source: Dict, translations: Dict, source_id: str) -> Tuple[dbc.Badge, dbc.Tooltip]:
    """Cria badge de cobertura com tooltip."""
    coverage_value = source.get("coverage", "global")
    coverage_text = translations.get(coverage_value, coverage_value.capitalize())
    
    badge = dbc.Badge(
        coverage_text,
        color="primary" if coverage_value == "global" else "info",
        className="me-1",
        id={"type": "coverage-badge", "source": source_id}
    )
    
    bbox_str = source.get("bbox_str", "Cobertura global")
    tooltip = dbc.Tooltip(
        f"🗺️ {translations['bbox']}: {bbox_str}",
        target={"type": "coverage-badge", "source": source_id},
        placement="top"
    )
    
    return badge, tooltip


def _create_temporal_badge(source: Dict, translations: Dict) -> dbc.Badge:
    """Cria badge de resolução temporal."""
    temporal_value = source.get("temporal", "daily")
    temporal_text = translations.get(temporal_value, temporal_value.capitalize())
    
    color_map = {
        "hourly": "success",
        "daily": "warning", 
        "monthly": "secondary"
    }
    
    return dbc.Badge(
        f"⏱️ {temporal_text}",
        color=color_map.get(temporal_value, "dark"),
        className="me-1"
    )


def _create_realtime_badge(source: Dict, translations: Dict) -> dbc.Badge:
    """Cria badge de tempo real."""
    realtime_value = source.get("realtime", False)
    realtime_text = translations["yes"] if realtime_value else translations["no"]
    
    return dbc.Badge(
        f"⚡ {realtime_text}",
        color="success" if realtime_value else "secondary",
        className="me-1"
    )


def _create_license_badge(source: Dict, translations: Dict, source_id: str) -> Tuple[dbc.Badge, dbc.Tooltip]:
    """Cria badge de licença com tooltip."""
    license_type = source.get("license", "")
    attribution_req = source.get("attribution_required", False)
    
    badge_configs = {
        "non_commercial": {
            "text": "⚠️ Visualização",
            "color": "warning",
            "tooltip": "CC-BY-NC 4.0: Uso restrito a visualização e pesquisa acadêmica."
        },
        "public_domain": {
            "text": "✅ Domínio Público", 
            "color": "success",
            "tooltip": "Domínio Público: Uso livre para fusão, download e aplicações comerciais."
        },
        "cc_by_4.0": {
            "text": "✅ CC-BY 4.0",
            "color": "success", 
            "tooltip": "CC-BY 4.0: Uso livre com atribuição obrigatória."
        }
    }
    
    config = badge_configs.get(license_type, {
        "text": "📄 Licença",
        "color": "secondary",
        "tooltip": "Informações de licença não disponíveis."
    })
    
    # Ajustar tooltip se atribuição for necessária
    if attribution_req and license_type != "non_commercial":
        config["tooltip"] += " Atribuição obrigatória."
    
    badge = dbc.Badge(
        config["text"],
        color=config["color"],
        className="me-1",
        id={"type": "license-badge", "source": source_id}
    )
    
    tooltip = dbc.Tooltip(
        config["tooltip"],
        target={"type": "license-badge", "source": source_id},
        placement="top"
    )
    
    return badge, tooltip


def _create_source_metadata(source: Dict) -> Optional[html.Div]:
    """Cria metadados adicionais da fonte se disponíveis."""
    metadata = []
    
    if source.get("description"):
        metadata.append(html.Small(source["description"], className="text-muted d-block"))
    
    if source.get("last_updated"):
        metadata.append(html.Small(f"🕒 Atualizado: {source['last_updated']}", className="text-muted d-block"))
    
    if source.get("accuracy"):
        metadata.append(html.Small(f"🎯 Precisão: {source['accuracy']}", className="text-muted d-block"))
    
    return html.Div(metadata, className="mt-1") if metadata else None


def _create_operation_mode_selector(translations: Dict, active_sources: List[Dict]) -> html.Div:
    """Cria seletor de modo de operação."""
    return html.Div([
        html.Hr(),
        html.H6(translations["mode_title"], className="mb-3"),
        
        # Modos de operação
        dbc.RadioItems(
            id="data-fusion-mode",
            options=[
                {
                    "label": html.Div([
                        html.Strong("🔀 " + translations["fusion_mode"]),
                        html.Br(),
                        html.Small(
                            translations["fusion_desc"],
                            className="text-muted"
                        )
                    ], className="py-1"),
                    "value": "fusion"
                },
                {
                    "label": html.Div([
                        html.Strong("🎯 " + translations["single_mode"]),
                        html.Br(),
                        html.Small(
                            translations["single_desc"], 
                            className="text-muted"
                        )
                    ], className="py-1"),
                    "value": "single"
                }
            ],
            value="fusion",
            className="mb-3"
        ),
        
        # Dropdown para fonte única (condicional)
        html.Div([
            html.Label("Selecione a fonte:", className="fw-bold mb-2"),
            dcc.Dropdown(
                id="single-source-dropdown",
                options=[
                    {
                        "label": html.Div([
                            source["name"],
                            html.Small(
                                f" - {source.get('coverage', 'global')}",
                                className="text-muted ms-1"
                            )
                        ]),
                        "value": source["id"]
                    }
                    for source in active_sources
                ],
                value=active_sources[0]["id"] if active_sources else None,
                clearable=False,
                className="mb-2"
            )
        ], id="single-source-selector", style={"display": "none"})
    ])


def create_source_availability_summary(available_sources: List[Dict], lang: str = "pt") -> dbc.Alert:
    """
    Cria resumo da disponibilidade de fontes.
    
    Args:
        available_sources: Lista de fontes
        lang: Idioma
        
    Returns:
        dbc.Alert: Resumo formatado
    """
    translations = get_translations(lang)
    
    total_sources = len(available_sources)
    available_count = sum(1 for s in available_sources if s.get("available", False))
    
    if available_count == 0:
        color = "warning"
        icon = "⚠️"
        message = "Nenhuma fonte disponível"
    elif available_count == total_sources:
        color = "success" 
        icon = "✅"
        message = f"Todas as {total_sources} fontes disponíveis"
    else:
        color = "info"
        icon = "ℹ️"
        message = f"{available_count} de {total_sources} fontes disponíveis"
    
    return dbc.Alert([
        html.Strong(f"{icon} {message}"),
        html.Br(),
        html.Small(
            "A disponibilidade é determinada pela localização selecionada",
            className="text-muted"
        )
    ], color=color, className="py-2")


# Funções de utilidade para callbacks
def get_source_info_tooltip(source_id: str) -> str:
    """
    Retorna tooltip com informações detalhadas da fonte.
    
    Args:
        source_id: ID da fonte de dados
        
    Returns:
        str: Texto do tooltip
    """
    return source_manager.get_source_tooltip(source_id)


def validate_source_selection(selected_sources: List[str], operation_mode: str) -> Tuple[bool, str]:
    """
    Valida seleção de fontes baseado no modo de operação.
    
    Args:
        selected_sources: Lista de IDs de fontes selecionadas
        operation_mode: 'fusion' ou 'single'
        
    Returns:
        Tuple (is_valid, message)
    """
    if operation_mode == "fusion":
        if len(selected_sources) < 2:
            return False, "Selecione pelo menos 2 fontes para fusão de dados"
        if len(selected_sources) > 5:
            return False, "Máximo de 5 fontes permitidas para fusão"
        return True, f"✅ {len(selected_sources)} fontes selecionadas para fusão"
    
    else:  # single mode
        if len(selected_sources) != 1:
            return False, "Selecione exatamente 1 fonte para modo único"
        return True, "✅ 1 fonte selecionada para modo único"


# Função de compatibilidade para código existente
def get_source_info_tooltip_legacy(source_id: str) -> str:
    """Versão legacy para compatibilidade."""
    return get_source_info_tooltip(source_id)
