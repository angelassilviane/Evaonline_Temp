"""
Componente de seleção de fontes de dados climáticos.
"""

from typing import Dict, List

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_climate_source_selector(
    available_sources: List[Dict],
    translations: Dict = None
) -> dbc.Card:
    """
    Cria card com seletor de fontes de dados climáticos.
    
    Args:
        available_sources: Lista de fontes disponíveis para a localidade
            Cada fonte deve conter:
            - id: Identificador único
            - name: Nome da fonte
            - available: bool indicando se está disponível
            - coverage: Cobertura geográfica
            - bbox_str: String formatada do bbox (ex: "35°N-72°N, 25°W-45°E")
            - license: Tipo de licença
            - can_fuse: bool indicando se pode ser usada em fusão
            - can_download: bool indicando se permite download
            - realtime: bool indicando se dados em tempo real
            - temporal: Resolução temporal
        translations: Traduções para i18n (opcional)
        
    Returns:
        dbc.Card: Card com seletor de fontes
    """
    if translations is None:
        translations = {
            "title": "🌐 Fontes de Dados Disponíveis",
            "coverage": "Cobertura",
            "temporal": "Resolução",
            "realtime": "Tempo Real",
            "license": "Licença",
            "yes": "Sim",
            "no": "Não",
            "mode_title": "Modo de Operação",
            "fusion_mode": "Fusão de Dados (Recomendado)",
            "fusion_desc": "Combina múltiplas fontes para maior precisão",
            "single_mode": "Fonte Única",
            "single_desc": "Usa apenas uma fonte selecionada",
            "info": (
                "💡 Fontes detectadas automaticamente "
                "para esta localização"
            ),
            "commercial_ok": "Uso Comercial OK",
            "global": "Global",
            "regional": "Regional",
            "hourly": "Horária",
            "daily": "Diária",
            "unavailable": "Indisponível para esta localização",
            "bbox": "Área de cobertura"
        }
    
    # Filtrar apenas fontes disponíveis para a localização
    active_sources = [
        s for s in available_sources if s.get("available", False)
    ]
    
    # Se não há fontes disponíveis
    if not active_sources:
        return dbc.Card([
            dbc.CardHeader(
                html.H5(translations["title"], className="mb-0")
            ),
            dbc.CardBody([
                dbc.Alert(
                    (
                        "⚠️ Nenhuma fonte de dados disponível "
                        "para esta localização."
                    ),
                    color="warning"
                )
            ])
        ], className="mb-3")
    
    # Criar cards para cada fonte
    source_cards = []
    for source in active_sources:
        # Badge de tempo real
        realtime_value = source.get("realtime")
        realtime_text = (
            translations["yes"] if realtime_value
            else translations["no"]
        )
        realtime_badge = dbc.Badge(
            realtime_text,
            color="success" if realtime_value else "secondary",
            className="ms-2"
        )
        
        # Badge de cobertura com tooltip
        coverage_value = source.get("coverage", "global")
        coverage_text = translations.get(
            coverage_value,
            source.get("coverage", "Global")
        )
        coverage_badge = dbc.Badge(
            coverage_text,
            color="primary" if coverage_value == "global" else "info",
            className="ms-2",
            id={"type": "coverage-badge", "source": source["id"]}
        )
        
        # Tooltip de cobertura com bbox
        bbox_str = source.get("bbox_str", "Global coverage")
        coverage_tooltip = dbc.Tooltip(
            f"{translations['bbox']}: {bbox_str}",
            target={"type": "coverage-badge", "source": source["id"]},
            placement="top"
        )
        
        # Badge de resolução temporal
        temporal_value = source.get("temporal", "daily")
        temporal_text = translations.get(
            temporal_value,
            source.get("temporal", "Diária")
        )
        temporal_badge = dbc.Badge(
            temporal_text,
            color="dark",
            className="ms-2"
        )
        
        # Badge de licença
        license_type = source.get("license", "")
        
        if license_type == "non_commercial":
            license_badge = dbc.Badge(
                "⚠️ Visualização Apenas",
                color="warning",
                className="ms-2",
                id={"type": "license-badge", "source": source["id"]}
            )
            license_tooltip = dbc.Tooltip(
                "CC-BY-NC 4.0: Dados não disponíveis para download ou fusão. "
                "Uso restrito a visualização e pesquisa acadêmica.",
                target={"type": "license-badge", "source": source["id"]},
                placement="top"
            )
        elif license_type == "public_domain":
            license_badge = dbc.Badge(
                "✅ Domínio Público",
                color="success",
                className="ms-2",
                id={"type": "license-badge", "source": source["id"]}
            )
            license_tooltip = dbc.Tooltip(
                "Domínio Público (NASA/NOAA): Uso livre para fusão, "
                "download e aplicações comerciais. Sem restrições.",
                target={"type": "license-badge", "source": source["id"]},
                placement="top"
            )
        else:  # CC-BY-4.0 ou similar
            license_badge = dbc.Badge(
                "✅ Uso Livre",
                color="success",
                className="ms-2",
                id={"type": "license-badge", "source": source["id"]}
            )
            attribution_req = source.get("attribution_required", False)
            license_tooltip = dbc.Tooltip(
                f"{license_type.upper()}: Uso livre para fusão, "
                f"download e aplicações comerciais. "
                f"{'Atribuição obrigatória.' if attribution_req else ''}",
                target={"type": "license-badge", "source": source["id"]},
                placement="top"
            )
        
        card = dbc.Card([
            dbc.CardBody([
                html.Div([
                    dbc.Checkbox(
                        id={"type": "source-checkbox", "source": source["id"]},
                        label="",
                        value=True,  # Default: todas selecionadas (fusão)
                        className="float-end"
                    ),
                    html.H6([
                        source["name"],
                        coverage_badge,
                        temporal_badge,
                        realtime_badge,
                        license_badge
                    ], className="mb-2"),
                    coverage_tooltip,
                    license_tooltip
                ]),
            ])
        ], className="mb-2")
        
        source_cards.append(card)
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5(translations["title"], className="mb-0")
        ]),
        dbc.CardBody([
            # Informação sobre detecção automática
            dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                translations["info"]
            ], color="info", className="mb-3"),
            
            # Cards das fontes
            html.Div(source_cards),
            
            # Informação sobre disponibilidade geográfica
            html.Div(id="source-availability-info", className="mb-3"),
            
            # Seletor de modo de operação
            html.Hr(),
            html.H6(translations["mode_title"], className="mb-3"),
            dbc.RadioItems(
                id="data-fusion-mode",
                options=[
                    {
                        "label": html.Div([
                            html.Strong(translations["fusion_mode"]),
                            html.Br(),
                            html.Small(
                                translations["fusion_desc"],
                                className="text-muted"
                            )
                        ]),
                        "value": "fusion"
                    },
                    {
                        "label": html.Div([
                            html.Strong(translations["single_mode"]),
                            html.Br(),
                            html.Small(
                                translations["single_desc"],
                                className="text-muted"
                            )
                        ]),
                        "value": "single"
                    }
                ],
                value="fusion",
                className="mb-3"
            ),
            
            # Dropdown para seleção de fonte única (aparece se mode=single)
            html.Div([
                html.Label("Selecione a fonte:", className="mb-2"),
                dcc.Dropdown(
                    id="single-source-dropdown",
                    options=[
                        {"label": s["name"], "value": s["id"]}
                        for s in active_sources
                    ],
                    value=(
                        active_sources[0]["id"]
                        if active_sources else None
                    ),
                    clearable=False
                )
            ], id="single-source-selector", style={"display": "none"})
        ])
    ], className="mb-3")


def get_source_info_tooltip(source_id: str) -> str:
    """
    Retorna tooltip com informações detalhadas da fonte.
    
    Args:
        source_id: ID da fonte de dados
        
    Returns:
        str: Texto do tooltip
    """
    tooltips = {
        "nasa_power": (
            "NASA POWER: Dados climáticos da NASA (domínio público). "
            "Cobertura global desde 1981. Dados diários com 1-2 dias de "
            "atraso. Alta confiabilidade para cálculo de ETo. "
            "✅ Livre para fusão e download."
        ),
        "met_norway": (
            "MET Norway: Serviço meteorológico norueguês (CC-BY 4.0). "
            "Cobertura: Europa (35°N-72°N, 25°W-45°E). "
            "Dados horários de alta precisão para refinamento regional. "
            "✅ Livre para fusão e download com atribuição."
        ),
        "nws_usa": (
            "National Weather Service: Serviço oficial dos EUA "
            "(domínio público - NOAA). "
            "Cobertura: Estados Unidos continental (24°N-49°N, 125°W-66°W). "
            "Dados horários governamentais oficiais. "
            "✅ Livre para fusão e download."
        )
    }
    
    return tooltips.get(source_id, "Informações não disponíveis")
