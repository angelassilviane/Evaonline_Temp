# -*- coding: utf-8 -*-
"""
Página inicial do EVAonline - Otimizada para performance.
"""
import dash_bootstrap_components as dbc
from dash import html
from loguru import logger

# Importar layout do mapa mundial com tratamento de erro
try:
    from frontend.components.world_map_tabs import create_world_map_layout
except ImportError as e:
    logger.error(f'Erro ao importar world_map_tabs: {e}')
    create_world_map_layout = None


def home_layout():
    """
    Retorna o layout da página inicial.
    """
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H1("EVAonline", className="mt-5 mb-3"),
                                html.P(
                                    "Plataforma para cálculo de Evapotranspiração de Referência",
                                    className="lead"
                                ),
                            ]
                        ),
                        md=6,
                    ),
                ],
                align="center",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        create_world_map_layout() if create_world_map_layout else html.Div("Mapa não disponível"),
                        md=12,
                    ),
                ],
                className="mt-4",
            ),
        ],
        fluid=True,
    )
