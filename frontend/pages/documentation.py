"""
Página de Documentação do EVAonline.
Estruturada conforme requisitos SoftwareX.
"""
import dash_bootstrap_components as dbc
from dash import html


def documentation_layout():
    """
    Layout da página de documentação conforme SoftwareX requirements.
    """
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-book me-3",
                           style={"color": "#2d5016"}),
                    "EVAonline Documentation"
                ], className="text-center mb-2",
                   style={"color": "#2d5016"}),
                html.P(
                    "An online tool for reference evapotranspiration "
                    "estimation using multiple climate data sources",
                    className="text-center text-muted mb-4",
                    style={"fontSize": "18px"}
                ),
            ], width=12)
        ]),
        
        html.Hr(className="my-4"),
        
        # License Section
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-balance-scale me-2"),
                    "License"
                ], id="license", className="mb-3",
                   style={"color": "#2d5016"}),
                dbc.Card([
                    dbc.CardBody([
                        html.H5("GNU AGPL v3 License", className="mb-3"),
                        html.P([
                            "Copyright © 2025 Ângela S. M. C. Soares, ",
                            "Patricia A. A. Marques, Carlos D. Maciel"
                        ], className="mb-3"),
                        dbc.Alert([
                            html.Strong("Open Source Software"),
                            html.Br(),
                            "EVAonline is licensed under the GNU Affero ",
                            "General Public License v3.0 (AGPL-3.0). This ",
                            "is a copyleft license that requires anyone who ",
                            "distributes your code or provides it as a ",
                            "service over a network to make the source code ",
                            "available under the same license terms."
                        ], color="success", className="mb-3"),
                        html.P([
                            html.Strong("Key Points:"),
                            html.Ul([
                                html.Li("✅ Free to use, modify, and "
                                        "distribute"),
                                html.Li("✅ Source code must remain open"),
                                html.Li("✅ Network use triggers source "
                                        "disclosure"),
                                html.Li("✅ Compatible with SoftwareX "
                                        "requirements")
                            ])
                        ], style={"fontSize": "14px"}),
                        html.A([
                            html.I(className="fab fa-github me-2"),
                            "Full license on GitHub"
                        ], href="https://github.com/angelassilviane/"
                                "Evaonline_Temp/blob/main/LICENSE",
                            target="_blank",
                            className="btn btn-outline-success btn-sm mt-2")
                    ])
                ], className="mb-4")
            ], width=12)
        ]),
        
        # Citation Section
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-quote-right me-2"),
                    "How to Cite"
                ], className="mb-3", style={"color": "#2d5016"}),
                dbc.Card([
                    dbc.CardBody([
                        html.P(
                            "If you use EVAonline in your research, "
                            "please cite:",
                            className="mb-3"
                        ),
                        dbc.Alert([
                            html.Strong("Soares, A.S.M.C., "),
                            "Marques, P.A.A., Maciel, C.D. (2025). ",
                            html.Em("EVAonline: An online tool for "
                                    "reference evapotranspiration "
                                    "estimation."),
                            " SoftwareX, [In submission]."
                        ], color="light", className="mb-3"),
                        html.H6("BibTeX:", className="mt-3 mb-2"),
                        html.Pre([
                            "@article{soares2025evaonline,\n",
                            "  title={EVAonline: An online tool for "
                            "reference evapotranspiration estimation},\n",
                            "  author={Soares, Angela S. M. C. and "
                            "Marques, Patricia A. A. and "
                            "Maciel, Carlos D.},\n",
                            "  journal={SoftwareX},\n",
                            "  year={2025},\n",
                            "  note={In submission}\n",
                            "}"
                        ], style={"backgroundColor": "#f8f9fa",
                                  "padding": "15px",
                                  "borderRadius": "5px",
                                  "fontSize": "12px",
                                  "overflow": "auto"})
                    ])
                ], className="mb-4")
            ], width=12)
        ]),
        
        # Data Sources and Attributions
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-database me-2"),
                    "Data Sources & Attributions"
                ], className="mb-3", style={"color": "#2d5016"}),
                
                # Open-Meteo Elevation
                dbc.Card([
                    dbc.CardHeader(html.Strong("Elevation Data")),
                    dbc.CardBody([
                        html.P([
                            html.Strong("Source: "),
                            html.A("Open-Meteo Elevation API",
                                   href="https://open-meteo.com/"
                                        "en/docs/elevation-api",
                                   target="_blank")
                        ]),
                        html.P([
                            html.Strong("Dataset: "),
                            "Copernicus DEM 90m (EU Space Programme)"
                        ]),
                        html.P([
                            html.Strong("License: "),
                            html.A("CC-BY 4.0",
                                   href="https://creativecommons.org/"
                                        "licenses/by/4.0/",
                                   target="_blank")
                        ]),
                        html.P([
                            html.Strong("Coverage: "),
                            "Global (-90° to 90° latitude)"
                        ]),
                        html.P([
                            html.Strong("Resolution: "),
                            "90 meters (typical accuracy: ±5-10m)"
                        ]),
                        dbc.Alert([
                            html.Strong("⚠️ Usage Terms & Rate Limiting"),
                            html.Br(),
                            "Per ",
                            html.A("Open-Meteo Terms of Service",
                                   href="https://open-meteo.com/en/terms",
                                   target="_blank",
                                   className="alert-link"),
                            ":",
                            html.Ul([
                                html.Li("Non-commercial use: Up to 10,000 "
                                        "requests/day"),
                                html.Li("Attribution required (provided in "
                                        "this app)"),
                                html.Li("Implemented protections:"),
                                html.Ul([
                                    html.Li("✅ Redis cache (30-day TTL) "
                                            "reduces API calls"),
                                    html.Li("✅ Retry logic with exponential "
                                            "backoff"),
                                    html.Li("✅ User-initiated requests only "
                                            "(map clicks)")
                                ])
                            ], className="mb-0", style={"fontSize": "13px"})
                        ], color="warning", className="mt-2 mb-0")
                    ])
                ], className="mb-3"),
                
                # NASA POWER
                dbc.Card([
                    dbc.CardHeader(html.Strong("Climate Data - NASA POWER")),
                    dbc.CardBody([
                        html.P([
                            html.Strong("Source: "),
                            html.A("NASA POWER API",
                                   href="https://power.larc.nasa.gov/",
                                   target="_blank")
                        ]),
                        html.P([
                            html.Strong("Dataset: "),
                            "Prediction Of Worldwide Energy Resources"
                        ]),
                        html.P([
                            html.Strong("Coverage: "),
                            "Global"
                        ]),
                        html.P([
                            html.Strong("Variables: "),
                            "Temperature, humidity, wind speed, "
                            "solar radiation"
                        ])
                    ])
                ], className="mb-3"),
                
                # MET Norway
                dbc.Card([
                    dbc.CardHeader(html.Strong(
                        "Climate Data - MET Norway"
                    )),
                    dbc.CardBody([
                        html.P([
                            html.Strong("Source: "),
                            html.A("MET Norway Locationforecast API",
                                   href="https://api.met.no/",
                                   target="_blank")
                        ]),
                        html.P([
                            html.Strong("Coverage: "),
                            "Europe and Nordic countries"
                        ])
                    ])
                ], className="mb-3"),
                
                # NWS USA
                dbc.Card([
                    dbc.CardHeader(html.Strong(
                        "Climate Data - NWS USA"
                    )),
                    dbc.CardBody([
                        html.P([
                            html.Strong("Source: "),
                            html.A("National Weather Service API",
                                   href="https://www.weather.gov/documentation"
                                        "/services-web-api",
                                   target="_blank")
                        ]),
                        html.P([
                            html.Strong("Coverage: "),
                            "Continental United States"
                        ])
                    ])
                ], className="mb-4")
            ], width=12)
        ]),
        
        # Technical Documentation
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-code me-2"),
                    "Technical Documentation"
                ], className="mb-3", style={"color": "#2d5016"}),
                
                html.H4("System Requirements", className="mb-2"),
                html.Ul([
                    html.Li("Python 3.12+"),
                    html.Li("Docker & Docker Compose"),
                    html.Li("PostgreSQL 15 with PostGIS"),
                    html.Li("Redis 7"),
                    html.Li("Modern web browser (Chrome, Firefox, Safari)")
                ], className="mb-3"),
                
                html.H4("Installation", className="mb-2"),
                html.Pre([
                    "# Clone repository\n",
                    "git clone https://github.com/angelassilviane/"
                    "Evaonline_Temp.git\n\n",
                    "# Start with Docker Compose\n",
                    "docker-compose up -d\n\n",
                    "# Access application\n",
                    "http://localhost:8050"
                ], style={"backgroundColor": "#f8f9fa",
                          "padding": "15px",
                          "borderRadius": "5px",
                          "fontSize": "13px"}),
                
                html.H4("Documentation Links", className="mb-2 mt-4"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.I(className="fab fa-github me-2"),
                        html.A("GitHub Repository",
                               href="https://github.com/angelassilviane/"
                                    "Evaonline_Temp",
                               target="_blank")
                    ]),
                    dbc.ListGroupItem([
                        html.I(className="fas fa-book me-2"),
                        html.A("API Documentation",
                               href="http://localhost:8000/docs",
                               target="_blank")
                    ]),
                    dbc.ListGroupItem([
                        html.I(className="fas fa-chart-line me-2"),
                        html.A("Monitoring Dashboard",
                               href="http://localhost:3000",
                               target="_blank")
                    ])
                ], className="mb-4")
            ], width=12)
        ]),
        
        # Contact Section
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-envelope me-2"),
                    "Contact"
                ], className="mb-3", style={"color": "#2d5016"}),
                html.P([
                    "For questions, bug reports, or contributions, "
                    "please contact:"
                ]),
                html.Ul([
                    html.Li([
                        html.Strong("Ângela S. M. C. Soares: "),
                        html.A("angelassilviane@gmail.com",
                               href="mailto:angelassilviane@gmail.com")
                    ]),
                    html.Li([
                        html.Strong("Patricia A. A. Marques: "),
                        html.A("paamarques@usp.br",
                               href="mailto:paamarques@usp.br")
                    ]),
                    html.Li([
                        html.Strong("Carlos D. Maciel: "),
                        html.A("carlos.maciel@unesp.br",
                               href="mailto:carlos.maciel@unesp.br")
                    ])
                ])
            ], width=12)
        ])
        
    ], fluid=True, className="py-4")
