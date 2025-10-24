"""
EVAonline ETo Calculator Page - Otimizada para produção.
"""
from datetime import datetime, timedelta
from typing import Any, Dict

import dash_bootstrap_components as dbc
from dash import dcc, html
from loguru import logger


def eto_calculator_dash(lang: str = "pt") -> dbc.Container:
    """
    Cria o layout da página ETo Calculator otimizado.
    
    Args:
        lang: Código do idioma (pt/en)
        
    Returns:
        dbc.Container: Layout da página
    """
    # Configurações de período com validação
    today = datetime.now()
    min_date = today - timedelta(days=85*365)  # 85+ anos (Open-Meteo Archive desde 1940)
    max_date = today + timedelta(days=16)      # +16 dias (Forecast horizon)
    
    # Textos baseados no idioma
    texts = _get_eto_texts(lang)
    
    return dbc.Container([
        # Exibir localização selecionada
        html.Div(id='eto-location-info', className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                # Header
                html.Div([
                    html.H1(
                        texts["title"], 
                        className="text-center mb-3",
                        style={"color": "#2d5016", "fontWeight": "bold"}
                    ),
                    html.P(
                        texts["subtitle"],
                        className="text-center lead text-muted mb-4"
                    )
                ]),
                
                # Card com informações da localização
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("📍 " + texts["location_title"], className="mb-0")
                    ),
                    dbc.CardBody(id='selected-location-display')
                ], className="mb-3 shadow-sm"),
                
                # Card com seletor de fontes de dados
                html.Div(id='climate-sources-card'),
                
                # Card com formulário de período
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("📅 " + texts["period_title"], className="mb-0")
                    ),
                    dbc.CardBody([
                        # Informação sobre limites de período
                        dbc.Alert([
                            html.I(className="bi bi-info-circle me-2"),
                            html.Strong(texts["period_info_label"]),
                            texts["period_info_text"].format(
                                min_date=min_date.strftime('%d/%m/%Y'),
                                max_date=max_date.strftime('%d/%m/%Y')
                            )
                        ], color="info", className="mb-3"),
                        
                        # Seletor de datas
                        dbc.Row([
                            dbc.Col([
                                html.Label(texts["start_date_label"], className="fw-bold"),
                                dcc.DatePickerSingle(
                                    id='start-date-picker',
                                    display_format='DD/MM/YYYY',
                                    min_date_allowed=min_date,
                                    max_date_allowed=max_date,
                                    initial_visible_month=today,
                                    date=today - timedelta(days=7),
                                    className="mb-2 w-100",
                                    clearable=False
                                )
                            ], md=6),
                            dbc.Col([
                                html.Label(texts["end_date_label"], className="fw-bold"),
                                dcc.DatePickerSingle(
                                    id='end-date-picker',
                                    display_format='DD/MM/YYYY',
                                    min_date_allowed=min_date,
                                    max_date_allowed=max_date,
                                    initial_visible_month=today,
                                    date=today,
                                    className="mb-2 w-100",
                                    clearable=False
                                )
                            ], md=6)
                        ]),
                        
                        # Validação de período
                        html.Div(id='period-validation', className="mt-2"),
                        
                        # Badge mostrando qual API será usado
                        html.Div(id='api-strategy-badge', className="mt-2"),
                        
                        # Botão de cálculo
                        dbc.Button(
                            texts["calculate_button"],
                            id="calculate-eto-btn",
                            color="primary",
                            className="mt-3 w-100",
                            size="lg",
                            disabled=False
                        )
                    ])
                ], className="mb-3 shadow-sm"),
                
                # Área de resultados com loading
                html.Div([
                    dbc.Spinner(
                        html.Div(id='eto-results'),
                        color="primary",
                        type="border"
                    )
                ], className="mt-3")
                
            ], lg=8, className="mx-auto")
        ]),
        
        # Stores para estado da aplicação
        dcc.Store(id='favorites-store', data=[], storage_type='local'),
        dcc.Store(id='selected-location-store', storage_type='session'),
        dcc.Store(id='available-sources-store', storage_type='session'),
        dcc.Store(id='selected-sources-store', storage_type='session')
        # Nota: calculation-state já está em app.py (global)
    ], fluid=True, className="py-3")


def _get_eto_texts(lang: str) -> Dict[str, Any]:
    """Retorna textos traduzidos para a página ETo."""
    return {
        "pt": {
            "title": "Calculadora de ETo",
            "subtitle": "Cálculo da evapotranspiração de referência com Open-Meteo (Archive + Forecast)",
            "location_title": "Localização Selecionada",
            "period_title": "Selecione o Período",
            "period_info_label": "Período permitido: ",
            "period_info_text": "Mínimo 7 dias, máximo 30 dias. Histórico: desde 1940 até hoje. Previsão: +16 dias.",
            "start_date_label": "Data Inicial:",
            "end_date_label": "Data Final:",
            "calculate_button": "📊 Calcular ETo",
            "api_info": "ℹ️ API Selection",
            "api_archive": "📚 Archive (1940+)",
            "api_forecast": "🔮 Forecast (Recent+16d)",
            "api_hybrid": "🔀 Hybrid (Archive + Forecast)"
        },
        "en": {
            "title": "ETo Calculator",
            "subtitle": "Reference evapotranspiration calculation with Open-Meteo (Archive + Forecast)",
            "location_title": "Selected Location",
            "period_title": "Select Period",
            "period_info_label": "Allowed period: ",
            "period_info_text": "Minimum 7 days, maximum 30 days. History: since 1940 until today. Forecast: +16 days.",
            "start_date_label": "Start Date:",
            "end_date_label": "End Date:",
            "calculate_button": "📊 Calculate ETo",
            "api_info": "ℹ️ API Selection",
            "api_archive": "📚 Archive (1940+)",
            "api_forecast": "🔮 Forecast (Recent+16d)",
            "api_hybrid": "🔀 Hybrid (Archive + Forecast)"
        }
    }.get(lang, "pt")


def create_period_validation_alert(is_valid: bool, message: str) -> dbc.Alert:
    """Cria alerta de validação de período."""
    color = "success" if is_valid else "danger"
    icon = "bi bi-check-circle" if is_valid else "bi bi-exclamation-triangle"
    
    return dbc.Alert([
        html.I(className=f"{icon} me-2"),
        html.Strong("Período " + ("válido" if is_valid else "inválido") + ": "),
        message
    ], color=color, className="py-2")
