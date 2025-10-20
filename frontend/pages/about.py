"""
EVAonline About Page - Internacionalizada e otimizada.
"""
from typing import Dict

import dash_bootstrap_components as dbc
from dash import html

# Textos internacionalizados
ABOUT_TEXTS = {
    "pt": {
        "title": "Sobre o EVAonline",
        "subtitle": "Sistema para cálculo de evapotranspiração de referência",
        "description": (
            "Este é um sistema desenvolvido para auxiliar no cálculo "
            "da evapotranspiração de referência (ETo) utilizando "
            "dados meteorológicos de múltiplas fontes com fusão por "
            "Ensemble Kalman Filter (EnKF)."
        ),
        "features_title": "Principais Funcionalidades",
        "features": [
            "🌍 Mapa mundial interativo para seleção de localizações",
            "📊 Cálculo de ETo com múltiplas fontes de dados climáticos",
            "🔍 Fusão de dados via Ensemble Kalman Filter",
            "📈 Visualização de resultados e histórico",
            "💾 Exportação de dados em múltiplos formatos"
        ]
    },
    "en": {
        "title": "About EVAonline",
        "subtitle": "Reference evapotranspiration calculation system",
        "description": (
            "This is a system developed to assist in reference "
            "evapotranspiration (ETo) calculation using meteorological "
            "data from multiple sources with Ensemble Kalman Filter (EnKF) fusion."
        ),
        "features_title": "Main Features",
        "features": [
            "🌍 Interactive world map for location selection",
            "📊 ETo calculation with multiple climate data sources",
            "🔍 Data fusion via Ensemble Kalman Filter",
            "📈 Results visualization and history",
            "💾 Data export in multiple formats"
        ]
    }
}


def about_dash(lang: str = "pt") -> dbc.Container:
    """
    Cria o layout da página About otimizado.
    
    Args:
        lang: Código do idioma (pt/en)
        
    Returns:
        dbc.Container: Layout da página
    """
    texts = ABOUT_TEXTS.get(lang, ABOUT_TEXTS["pt"])
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                # Header
                html.Div([
                    html.H1(
                        texts["title"], 
                        className="text-center mb-4",
                        style={"color": "#2d5016", "fontWeight": "bold"}
                    ),
                    html.P(
                        texts["subtitle"],
                        className="text-center lead text-muted"
                    ),
                    html.Hr(className="my-4")
                ]),
                
                # Descrição
                dbc.Card([
                    dbc.CardBody([
                        html.P(
                            texts["description"],
                            className="mb-0",
                            style={"fontSize": "1.1rem", "lineHeight": "1.6"}
                        )
                    ])
                ], className="mb-4"),
                
                # Funcionalidades
                dbc.Card([
                    dbc.CardHeader([
                        html.H4(
                            texts["features_title"],
                            className="mb-0",
                            style={"color": "#2d5016"}
                        )
                    ]),
                    dbc.CardBody([
                        html.Ul([
                            html.Li(
                                feature,
                                className="mb-2",
                                style={"fontSize": "1rem"}
                            ) for feature in texts["features"]
                        ], className="mb-0")
                    ])
                ], className="mb-4"),
                
                # Informações técnicas
                dbc.Card([
                    dbc.CardHeader([
                        html.H4(
                            "🛠️ Informações Técnicas" if lang == "pt" else "🛠️ Technical Information",
                            className="mb-0",
                            style={"color": "#2d5016"}
                        )
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6("🌐 Frontend", className="mb-2"),
                                html.Ul([
                                    html.Li("Dash Plotly"),
                                    html.Li("Bootstrap 5"),
                                    html.Li("Leaflet Maps"),
                                    html.Li("React Components")
                                ])
                            ], md=6),
                            dbc.Col([
                                html.H6("⚙️ Backend", className="mb-2"),
                                html.Ul([
                                    html.Li("FastAPI"),
                                    html.Li("PostgreSQL + PostGIS"),
                                    html.Li("Redis Cache"),
                                    html.Li("Celery Workers")
                                ])
                            ], md=6)
                        ])
                    ])
                ])
                
            ], lg=10, className="mx-auto")
        ])
    ], fluid=True, className="py-4")
