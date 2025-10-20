"""
Página de Documentação do EVAonline - Otimizada para SEO e performance.
"""
import json
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import html


def documentation_layout() -> dbc.Container:
    """
    Layout da página de documentação otimizado para produção.
    """
    current_year = datetime.now().year
    
    # Metadados estruturados para SEO
    structured_data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "EVAonline",
        "description": "An online tool for reference evapotranspiration estimation using multiple climate data sources",
        "applicationCategory": "ScientificApplication",
        "operatingSystem": "Web Browser",
        "permissions": "AGPL-3.0",
        "author": {
            "@type": "Organization",
            "name": "ESALQ/USP"
        }
    }
    
    return dbc.Container([
        # Metadados estruturados (invisível)
        html.Script(
            f"window.structuredData = {json.dumps(structured_data)}",
            type="application/ld+json"
        ),
        
        # Header
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-book me-3", style={"color": "#2d5016"}),
                    "EVAonline Documentation"
                ], className="text-center mb-2", style={"color": "#2d5016"}),
                html.P(
                    "An online tool for reference evapotranspiration "
                    "estimation using multiple climate data sources",
                    className="text-center text-muted mb-4",
                    style={"fontSize": "18px"}
                ),
            ], width=12)
        ]),
        
        html.Hr(className="my-4"),
        
        # Navegação rápida
        dbc.Card([
            dbc.CardBody([
                html.H5("📖 Quick Navigation", className="mb-3"),
                dbc.Nav([
                    dbc.NavLink("License", href="#license", external_link=True),
                    dbc.NavLink("How to Cite", href="#citation", external_link=True),
                    dbc.NavLink("Data Sources", href="#data-sources", external_link=True),
                    dbc.NavLink("Technical Docs", href="#technical", external_link=True),
                    dbc.NavLink("Contact", href="#contact", external_link=True),
                ], pills=True, fill=True)
            ])
        ], className="mb-4"),
        
        # License Section
        _create_license_section(current_year),
        
        # Citation Section
        _create_citation_section(),
        
        # Data Sources and Attributions
        _create_data_sources_section(),
        
        # Technical Documentation
        _create_technical_section(),
        
        # Contact Section
        _create_contact_section()
        
    ], fluid=True, className="py-4")


def _create_license_section(current_year: int) -> dbc.Row:
    """Cria seção de licença."""
    return dbc.Row([
        dbc.Col([
            html.H2([
                html.I(className="fas fa-balance-scale me-2"),
                "License"
            ], id="license", className="mb-3", style={"color": "#2d5016"}),
            dbc.Card([
                dbc.CardBody([
                    html.H5("GNU AGPL v3 License", className="mb-3"),
                    html.P([
                        f"Copyright © {current_year} Ângela S. M. C. Soares, ",
                        "Patricia A. A. Marques, Carlos D. Maciel"
                    ], className="mb-3"),
                    dbc.Alert([
                        html.Strong("Open Source Software"),
                        html.Br(),
                        "EVAonline is licensed under the GNU Affero "
                        "General Public License v3.0 (AGPL-3.0)."
                    ], color="success", className="mb-3"),
                    html.Div([
                        dbc.Badge("✅ Free to use", color="success", className="me-2"),
                        dbc.Badge("✅ Modify and distribute", color="success", className="me-2"),
                        dbc.Badge("✅ Source code remains open", color="success", className="me-2"),
                        dbc.Badge("✅ Network use triggers disclosure", color="success"),
                    ], className="mb-3"),
                    html.A([
                        html.I(className="fab fa-github me-2"),
                        "Full license on GitHub"
                    ], href="https://github.com/angelassilviane/Evaonline_Temp/blob/main/LICENSE",
                       target="_blank", className="btn btn-outline-success btn-sm")
                ])
            ], className="mb-4")
        ], width=12)
    ])


def _create_citation_section() -> dbc.Row:
    """Cria seção de citação."""
    return dbc.Row([
        dbc.Col([
            html.H2([
                html.I(className="fas fa-quote-right me-2"),
                "How to Cite"
            ], id="citation", className="mb-3", style={"color": "#2d5016"}),
            dbc.Card([
                dbc.CardBody([
                    html.P("If you use EVAonline in your research, please cite:", className="mb-3"),
                    dbc.Alert([
                        html.Strong("Soares, A.S.M.C., "),
                        "Marques, P.A.A., Maciel, C.D. (2025). ",
                        html.Em("EVAonline: An online tool for reference evapotranspiration estimation."),
                        " SoftwareX, [In submission]."
                    ], color="light", className="mb-3"),
                    html.H6("BibTeX:", className="mt-3 mb-2"),
                    html.Pre(
                        _get_bibtex_content(),
                        style={
                            "backgroundColor": "#f8f9fa",
                            "padding": "15px",
                            "borderRadius": "5px",
                            "fontSize": "12px",
                            "overflow": "auto"
                        }
                    )
                ])
            ], className="mb-4")
        ], width=12)
    ])


def _get_bibtex_content() -> str:
    """Retorna conteúdo BibTeX formatado."""
    return """@article{soares2025evaonline,
  title={EVAonline: An online tool for reference evapotranspiration estimation},
  author={Soares, Angela S. M. C. and Marques, Patricia A. A. and Maciel, Carlos D.},
  journal={SoftwareX},
  year={2025},
  note={In submission}
}"""


def _create_data_sources_section() -> dbc.Row:
    """Cria seção de fontes de dados."""
    return dbc.Row([
        dbc.Col([
            html.H2([
                html.I(className="fas fa-database me-2"),
                "Data Sources & Attributions"
            ], id="data-sources", className="mb-3", style={"color": "#2d5016"}),
            
            # Open-Meteo Elevation
            _create_data_source_card(
                "Elevation Data",
                "Open-Meteo Elevation API",
                "https://open-meteo.com/en/docs/elevation-api",
                "Copernicus DEM 90m (EU Space Programme)",
                "CC-BY 4.0",
                "Global (-90° to 90° latitude)",
                "90 meters (typical accuracy: ±5-10m)"
            ),
            
            # NASA POWER
            _create_data_source_card(
                "Climate Data - NASA POWER",
                "NASA POWER API", 
                "https://power.larc.nasa.gov/",
                "Prediction Of Worldwide Energy Resources",
                "Public Domain",
                "Global",
                "Daily since 1981"
            ),
            
            # MET Norway
            _create_data_source_card(
                "Climate Data - MET Norway",
                "MET Norway Locationforecast API",
                "https://api.met.no/",
                "MET Norway Meteorological Data",
                "CC-BY 4.0", 
                "Europe and Nordic countries",
                "Hourly real-time"
            ),
            
            # NWS USA
            _create_data_source_card(
                "Climate Data - NWS USA",
                "National Weather Service API",
                "https://www.weather.gov/documentation/services-web-api",
                "NOAA National Weather Service",
                "Public Domain",
                "Continental United States", 
                "Hourly real-time"
            )
        ], width=12)
    ])


def _create_data_source_card(title: str, source: str, source_url: str, 
                           dataset: str, license: str, coverage: str, resolution: str) -> dbc.Card:
    """Cria card padronizado para fonte de dados."""
    return dbc.Card([
        dbc.CardHeader(html.Strong(title)),
        dbc.CardBody([
            html.P([html.Strong("Source: "), html.A(source, href=source_url, target="_blank")]),
            html.P([html.Strong("Dataset: "), dataset]),
            html.P([html.Strong("License: "), license]),
            html.P([html.Strong("Coverage: "), coverage]),
            html.P([html.Strong("Resolution: "), resolution]),
        ])
    ], className="mb-3")


def _create_technical_section() -> dbc.Row:
    """Cria seção técnica."""
    return dbc.Row([
        dbc.Col([
            html.H2([
                html.I(className="fas fa-code me-2"),
                "Technical Documentation"
            ], id="technical", className="mb-3", style={"color": "#2d5016"}),
            
            dbc.Card([
                dbc.CardBody([
                    html.H4("System Requirements", className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Ul([
                                html.Li("Python 3.12+"),
                                html.Li("Docker & Docker Compose"), 
                                html.Li("PostgreSQL 15 with PostGIS"),
                            ])
                        ], md=6),
                        dbc.Col([
                            html.Ul([
                                html.Li("Redis 7"),
                                html.Li("Modern web browser"),
                                html.Li("4GB+ RAM recommended"),
                            ])
                        ], md=6)
                    ]),
                    
                    html.H4("Quick Start", className="mt-4 mb-3"),
                    html.Pre(
                        _get_installation_commands(),
                        style={
                            "backgroundColor": "#f8f9fa",
                            "padding": "15px",
                            "borderRadius": "5px",
                            "fontSize": "13px"
                        }
                    ),
                    
                    html.H4("Documentation Links", className="mt-4 mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            html.I(className="fab fa-github me-2"),
                            html.A("GitHub Repository", href="https://github.com/angelassilviane/Evaonline_Temp", target="_blank")
                        ]),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-book me-2"), 
                            html.A("API Documentation", href="http://localhost:8000/docs", target="_blank")
                        ]),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-chart-line me-2"),
                            html.A("Monitoring Dashboard", href="http://localhost:3000", target="_blank")
                        ])
                    ])
                ])
            ], className="mb-4")
        ], width=12)
    ])


def _get_installation_commands() -> str:
    """Retorna comandos de instalação."""
    return """# Clone repository
git clone https://github.com/angelassilviane/Evaonline_Temp.git

# Start with Docker Compose
docker-compose up -d

# Access application
http://localhost:8050"""


def _create_contact_section() -> dbc.Row:
    """Cria seção de contato."""
    return dbc.Row([
        dbc.Col([
            html.H2([
                html.I(className="fas fa-envelope me-2"),
                "Contact"
            ], id="contact", className="mb-3", style={"color": "#2d5016"}),
            html.P("For questions, bug reports, or contributions, please contact:"),
            html.Ul([
                html.Li([html.Strong("Ângela S. M. C. Soares: "), html.A("angelassilviane@gmail.com", href="mailto:angelassilviane@gmail.com")]),
                html.Li([html.Strong("Patricia A. A. Marques: "), html.A("paamarques@usp.br", href="mailto:paamarques@usp.br")]),
                html.Li([html.Strong("Carlos D. Maciel: "), html.A("carlos.maciel@unesp.br", href="mailto:carlos.maciel@unesp.br")])
            ])
        ], width=12)
    ])
