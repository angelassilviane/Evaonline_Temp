"""
Página inicial do EVAonline com mapas interativos em abas.
"""
import sys
from pathlib import Path

import dash_bootstrap_components as dbc
from dash import dcc, html

# Adicionar backend ao path para importar map_results
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent / "backend")
)
from core.map_results.map_results import create_world_real_map


# Layout da página inicial com mapa mundial único (sem tabs)
def home_layout() -> html.Div:
    """
    Cria o layout da página inicial com mapa mundial interativo.
    
    Funcionalidade MATOPIBA removida - foco em mapa mundial com fusão
    de dados via Ensemble Kalman Filter (EnKF).

    Returns:
        html.Div: Layout da página inicial
    """
    print("🔍 DEBUG HOME_LAYOUT: Starting to create layout...")
    try:
        layout = html.Div([
            # Stores para persistência de dados (locais da página home)
            dcc.Store(id='markers-store', data=[]),
            dcc.Store(id='favorites-store', data=[], storage_type='local'),
            dcc.Store(id='selected-location-store', data=None),  # ✨ NOVO: Para callbacks de fusão
            
            dbc.Container([
                # Header com título
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-globe-americas me-2",
                                   style={"fontSize": "16px", "color": "#2d5016"}),
                            html.Strong(
                                "Mapa Mundial - Cálculo de ETo com Fusão de Dados",
                                style={"fontSize": "16px", "color": "#2d5016"}
                            )
                        ], className="mb-2"),
                        html.P(
                            "🔬 Fusão via Ensemble Kalman Filter (EnKF) | "
                            "🌍 Clique em qualquer ponto do mapa para calcular ETo "
                            "usando múltiplas fontes climáticas (NASA POWER, MET Norway, NWS).",
                            className="text-muted small mb-0"
                        )
                    ], className="py-3 px-3")
                ], className="mb-3 shadow-sm"),

                # Mapa Mundial (renderizado direto, sem tabs)
                create_world_real_map()
            ], className="container-fluid")
        ])
        print("✅ DEBUG HOME_LAYOUT: Layout created successfully!")
        return layout
    except Exception as e:
        print(f"❌ DEBUG HOME_LAYOUT ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
