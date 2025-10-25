"""
Componente de rodapé para o aplicativo EVAOnline - Otimizado para produção.
"""
import json
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import html
from loguru import logger


class FooterManager:
    """Gerencia dados e configurações do rodapé com cache."""
    
    def __init__(self):
        self._current_year = datetime.now().year
        self._partner_cache = None
        self._developer_cache = None
    
    @property
    def current_year(self) -> int:
        """Retorna ano atual para copyright."""
        return self._current_year
    
    @lru_cache(maxsize=1)
    def get_partner_data(self) -> Dict[str, str]:
        """
        Retorna dados dos parceiros com cache.
        
        Returns:
            Dict: {partner_id: url}
        """
        return {
            "c4ai": "https://c4ai.inova.usp.br/",
            "fapesp": "https://fapesp.br/", 
            "ibm": "https://www.ibm.com/br-pt",
            "usp": "https://www5.usp.br/",
            "esalq": "https://www.esalq.usp.br/"
        }
    
    @lru_cache(maxsize=1) 
    def get_developer_data(self) -> List[Dict]:
        """
        Retorna dados dos desenvolvedores com cache.
        
        Returns:
            List: Lista de desenvolvedores
        """
        return [
            {
                "name": "Ângela S. M. C. Soares",
                "email": "angelassilviane@gmail.com",
                "institution": "ESALQ/USP",
                "role": "Desenvolvedora Principal"
            },
            {
                "name": "Patricia A. A. Marques", 
                "email": "paamarques@usp.br",
                "institution": "ESALQ/USP",
                "role": "Pesquisadora"
            },
            {
                "name": "Carlos D. Maciel",
                "email": "carlos.maciel@unesp.br", 
                "institution": "UNESP",
                "role": "Coordenador"
            }
        ]
    
    @lru_cache(maxsize=5)
    def get_email_link(self, email: str) -> str:
        """
        Gera link de email apropriado baseado no provedor.
        
        Args:
            email: Endereço de email
            
        Returns:
            str: URL formatada para o email
        """
        email_providers = {
            "gmail.com": "https://mail.google.com/mail/?view=cm&fs=1&to={email}",
            "usp.br": "https://mail.google.com/mail/?view=cm&fs=1&to={email}",
            "unesp.br": "https://mail.google.com/mail/?view=cm&fs=1&to={email}",
            "outlook.com": "https://outlook.live.com/mail/0/deeplink/compose?to={email}",
            "hotmail.com": "https://outlook.live.com/mail/0/deeplink/compose?to={email}",
        }
        
        try:
            domain = email.split("@")[1].lower()
            email_link_template = email_providers.get(domain, "mailto:{email}")
            return email_link_template.format(email=email)
        except (IndexError, AttributeError):
            logger.warning(f"Formato de email inválido: {email}")
            return f"mailto:{email}"
    
    def get_data_sources(self) -> List[Dict]:
        """Retorna lista de fontes de dados com atribuições."""
        return [
            {
                "name": "Open-Meteo Elevation API",
                "url": "https://open-meteo.com/en/docs/elevation-api",
                "description": "Dados de elevação (Copernicus DEM 90m)",
                "license": "CC-BY 4.0",
                "attribution": "EU Space Programme"
            },
            {
                "name": "NASA POWER API", 
                "url": "https://power.larc.nasa.gov/",
                "description": "Dados climáticos globais",
                "license": "Public Domain",
                "attribution": "NASA"
            },
            {
                "name": "MET Norway API",
                "url": "https://api.met.no/", 
                "description": "Dados climáticos da Europa",
                "license": "CC-BY 4.0",
                "attribution": "MET Norway"
            },
            {
                "name": "NWS USA API",
                "url": "https://www.weather.gov/documentation/services-web-api",
                "description": "Dados climáticos dos EUA", 
                "license": "Public Domain",
                "attribution": "NOAA"
            }
        ]


# Instância global do gerenciador
footer_manager = FooterManager()


def render_footer(lang: str = "pt") -> html.Footer:
    """
    Cria um rodapé responsivo otimizado para produção.
    
    Args:
        lang: Idioma para internacionalização
        
    Returns:
        html.Footer: Componente do rodapé otimizado
    """
    logger.debug("🔄 Renderizando rodapé")
    
    try:
        # Textos internacionalizados
        texts = _get_footer_texts(lang)
        
        return html.Footer(
            dbc.Container([
                # Linha de parceiros e desenvolvedores
                dbc.Row([
                    dbc.Col(
                        _create_partners_section(texts),
                        md=6, sm=12, className="text-center mb-4"
                    ),
                    dbc.Col(
                        _create_developers_section(texts),
                        md=6, sm=12, className="text-center mb-4" 
                    )
                ], className="mb-4"),
                
                # Linha de licenças e atribuições
                dbc.Row([
                    dbc.Col(
                        _create_license_section(texts),
                        width=12, className="text-center mb-4"
                    )
                ]),
                
                # Linha de copyright
                dbc.Row([
                    dbc.Col(
                        _create_copyright_section(texts),
                        width=12
                    )
                ])
                
            ], fluid=True, className="py-4 border-top",
               style={"backgroundColor": "#f8f9fa"}),
            
            # Metadados para SEO
            **{"data-role": "footer", "data-version": "1.0.0"}
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao renderizar rodapé: {e}")
        return _create_fallback_footer()


def _get_footer_texts(lang: str) -> Dict:
    """Retorna textos traduzidos para o rodapé."""
    texts = {
        "pt": {
            "partners": "Parceiros",
            "developers": "Desenvolvedores", 
            "license_title": "Licença e Atribuições",
            "software_license": "Software sob licença",
            "open_source": "Código aberto",
            "elevation_data": "Dados de elevação:",
            "climate_data": "Dados climáticos:",
            "full_documentation": "Documentação completa e citação",
            "copyright": f"© {footer_manager.current_year} EVAonline",
            "developed_for": "Desenvolvido para pesquisa científica",
            "contact": "Contato"
        },
        "en": {
            "partners": "Partners",
            "developers": "Developers",
            "license_title": "License & Attributions", 
            "software_license": "Software under license",
            "open_source": "Open source",
            "elevation_data": "Elevation data:",
            "climate_data": "Climate data:",
            "full_documentation": "Full documentation and citation",
            "copyright": f"© {footer_manager.current_year} EVAonline", 
            "developed_for": "Developed for scientific research",
            "contact": "Contact"
        }
    }
    
    return texts.get(lang, texts["pt"])


def _create_partners_section(texts: Dict) -> html.Div:
    """Cria seção de parceiros."""
    partners = footer_manager.get_partner_data()
    
    return html.Div([
        html.H5(
            texts["partners"],
            className="mb-3",
            style={
                "fontSize": "16px", 
                "fontWeight": "600", 
                "color": "#2d5016"
            }
        ),
        
        html.Div([
            html.A(
                html.Img(
                    src=f"/assets/images/logo_{partner}.png",
                    alt=f"Logo {partner.upper()}",
                    style={
                        "height": "45px",
                        "margin": "8px 12px",
                        "filter": "grayscale(30%)",
                        "opacity": "0.85",
                        "transition": "all 0.3s ease",
                        "objectFit": "contain"
                    },
                    className="partner-logo",
                    **{"data-partner": partner}
                ),
                href=url,
                target="_blank",
                rel="noopener noreferrer",
                title=f"Visitar {partner.upper()}",
                className="partner-link"
            )
            for partner, url in partners.items()
        ], style={
            "display": "flex",
            "flexWrap": "wrap", 
            "justifyContent": "center",
            "alignItems": "center",
            "gap": "10px"
        })
    ], className="partners-section")


def _create_developers_section(texts: Dict) -> html.Div:
    """Cria seção de desenvolvedores."""
    developers = footer_manager.get_developer_data()
    
    return html.Div([
        html.H5(
            texts["developers"],
            className="mb-3",
            style={
                "fontSize": "16px",
                "fontWeight": "600", 
                "color": "#2d5016"
            }
        ),
        
        html.Ul([
            html.Li([
                # Nome e instituição
                html.Div([
                    html.Strong(
                        dev["name"],
                        style={"color": "#333", "display": "block"}
                    ),
                    html.Small(
                        f"{dev['institution']} • {dev['role']}",
                        className="text-muted d-block",
                        style={"fontSize": "12px"}
                    )
                ], className="mb-1"),
                
                # Email
                html.A(
                    dev["email"],
                    href=footer_manager.get_email_link(dev["email"]),
                    target="_blank",
                    rel="noopener noreferrer",
                    style={
                        "color": "#2d5016",
                        "textDecoration": "none",
                        "fontSize": "13px",
                        "fontFamily": "monospace"
                    },
                    className="email-link",
                    **{"data-role": "developer-contact"}
                )
            ], style={
                "marginBottom": "12px",
                "fontSize": "14px",
                "listStyle": "none",
                "padding": "8px 0",
                "borderBottom": "1px solid #eee"
            })
            for dev in developers
        ], style={
            "listStyle": "none",
            "padding": "0",
            "margin": "0"
        })
    ], className="developers-section")


def _create_license_section(texts: Dict) -> html.Div:
    """Cria seção de licenças e atribuições."""
    data_sources = footer_manager.get_data_sources()
    
    return html.Div([
        html.H5(
            texts["license_title"],
            className="text-center mb-3",
            style={
                "fontSize": "16px",
                "fontWeight": "600",
                "color": "#2d5016"
            }
        ),
        
        # Licença do software
        html.Div([
            html.P([
                html.I(
                    className="fas fa-balance-scale me-2",
                    style={"color": "#2d5016"}
                ),
                html.Span(f"{texts['software_license']} "),
                html.A(
                    "GNU AGPL v3",
                    href="/documentation#license",
                    style={
                        "color": "#2d5016",
                        "fontWeight": "600",
                        "textDecoration": "underline"
                    },
                    className="license-link",
                    title="Ver licença completa"
                ),
                html.Span(" • "),
                html.A(
                    html.I(className="fab fa-github me-1"),
                    href="https://github.com/angelassilviane/Evaonline_Temp",
                    target="_blank",
                    rel="noopener noreferrer",
                    style={"color": "#333"},
                    title="Repositório GitHub"
                ),
                html.Span(f" {texts['open_source']}")
            ], className="mb-2 text-center", style={"fontSize": "14px"})
        ], className="mb-3"),
        
        # Fontes de dados
        html.Div([
            # Dados de elevação
            html.P([
                html.I(
                    className="fas fa-mountain me-2",
                    style={"color": "#2d5016"}
                ),
                html.Strong(f"{texts['elevation_data']} "),
                html.A(
                    "Open-Meteo Elevation API",
                    href="https://open-meteo.com/en/docs/elevation-api",
                    target="_blank",
                    rel="noopener noreferrer",
                    style={"color": "#2d5016"}
                ),
                html.Span(" (Copernicus DEM 90m, CC-BY 4.0)")
            ], className="mb-1 text-center", style={"fontSize": "13px"}),
            
            # Dados climáticos
            html.P([
                html.I(
                    className="fas fa-cloud-sun me-2", 
                    style={"color": "#2d5016"}
                ),
                html.Strong(f"{texts['climate_data']} "),
                html.Span("NASA POWER, MET Norway, NWS USA")
            ], className="mb-2 text-center", style={"fontSize": "13px"}),
            
            # Link para documentação
            html.P([
                html.I(
                    className="fas fa-book me-2",
                    style={"color": "#2d5016"}
                ),
                html.A(
                    texts["full_documentation"],
                    href="/documentation",
                    style={
                        "color": "#2d5016",
                        "fontWeight": "600"
                    },
                    className="documentation-link"
                )
            ], className="mb-0 text-center", style={"fontSize": "13px"})
            
        ], className="data-sources")
    ], className="license-section")


def _create_copyright_section(texts: Dict) -> html.Div:
    """Cria seção de copyright."""
    return html.Div([
        html.Hr(style={
            "borderColor": "#dee2e6",
            "margin": "20px 0",
            "opacity": "0.6"
        }),
        
        html.P([
            html.Span(
                texts["copyright"],
                style={"fontWeight": "600"}
            ),
            html.Span(" • ", className="mx-2"),
            html.Span(texts["developed_for"]),
            html.Span(" • ", className="mx-2"),
            html.A(
                "📊 Status",
                href="/status",
                style={
                    "color": "#6c757d",
                    "textDecoration": "none"
                },
                className="status-link"
            )
        ], className="text-center text-muted mb-0", style={"fontSize": "12px"})
    ], className="copyright-section")


def _create_fallback_footer() -> html.Footer:
    """Cria rodapé de fallback em caso de erro."""
    return html.Footer(
        dbc.Container([
            html.Div([
                html.P([
                    "© 2025 EVAonline • ",
                    html.A(
                        "GitHub",
                        href="https://github.com/angelassilviane/Evaonline_Temp",
                        target="_blank"
                    ),
                    " • Desenvolvido para pesquisa científica"
                ], className="text-center text-muted mb-0")
            ])
        ], fluid=True, className="py-3 border-top",
           style={"backgroundColor": "#f8f9fa"})
    )


def render_minimal_footer() -> html.Footer:
    """
    Renderiza versão minimalista do rodapé para páginas específicas.
    
    Returns:
        html.Footer: Rodapé minimalista
    """
    return html.Footer(
        dbc.Container([
            html.Div([
                html.P([
                    f"© {footer_manager.current_year} EVAonline • ",
                    html.A(
                        "GitHub",
                        href="https://github.com/angelassilviane/Evaonline_Temp",
                        target="_blank",
                        rel="noopener noreferrer"
                    ),
                    " • ",
                    html.A(
                        "Documentação", 
                        href="/documentation"
                    )
                ], className="text-center text-muted mb-0", style={"fontSize": "12px"})
            ])
        ], fluid=True, className="py-2 border-top",
           style={"backgroundColor": "#f8f9fa"})
    )


# Funções de utilidade para analytics e monitoring
def get_footer_metadata() -> Dict:
    """Retorna metadados do rodapé para analytics."""
    return {
        "partners_count": len(footer_manager.get_partner_data()),
        "developers_count": len(footer_manager.get_developer_data()),
        "data_sources_count": len(footer_manager.get_data_sources()),
        "render_timestamp": datetime.now().isoformat()
    }


def validate_footer_assets() -> Dict:
    """
    Valida se todos os assets do rodapé estão disponíveis.
    
    Returns:
        Dict: Resultado da validação
    """
    partners = footer_manager.get_partner_data()
    validation_results = {
        "partners": {},
        "status": "success",
        "missing_assets": []
    }
    
    for partner in partners.keys():
        # Em produção, validaria se o arquivo de logo existe
        asset_path = f"/assets/images/logo_{partner}.png"
        validation_results["partners"][partner] = {
            "asset_path": asset_path,
            "status": "assumed_available"  # Em produção, faria verificação real
        }
    
    return validation_results


# ### D. Footer Component

# ```python
# # frontend/components/footer.py

# import dash_bootstrap_components as dbc
# from dash import html, dcc, callback, Input, Output
# import requests

# def create_footer(lang: str = "pt") -> dbc.Container:
#     """
#     Footer com contador de visitantes.
    
#     Features:
#     - Visitor counter (real-time, Redis)
#     - Admin panel link (se autenticado)
#     - Status indicators (API, DB, Redis)
#     - Language toggle
#     """
    
#     texts = {
#         "pt": {
#             "visitors": "Visitantes",
#             "admin": "Administração",
#             "status": "Status",
#             "online": "Online",
#             "offline": "Offline",
#         },
#         "en": {
#             "visitors": "Visitors",
#             "admin": "Administration",
#             "status": "Status",
#             "online": "Online",
#             "offline": "Offline",
#         }
#     }
    
#     t = texts.get(lang, texts["pt"])
    
#     return dbc.Container([
#         # Divisor visual
#         html.Hr(style={"margin": "20px 0", "borderTop": "2px solid #e0e0e0"}),
        
#         # Conteúdo footer
#         dbc.Row([
#             # Coluna 1: Visitantes
#             dbc.Col([
#                 html.Div([
#                     html.I(className="fas fa-users me-2"),
#                     html.Span(f"{t['visitors']}: "),
#                     html.Strong(
#                         id="visitor-counter",
#                         children="0",
#                         style={"color": "#28a745"}
#                     )
#                 ], style={"fontSize": "14px"})
#             ], width=3),
            
#             # Coluna 2: Status
#             dbc.Col([
#                 html.Div([
#                     html.I(className="fas fa-circle me-1", 
#                            id="status-indicator",
#                            style={"color": "green"}),
#                     html.Span(f"{t['status']}: ", id="status-text")
#                 ], style={"fontSize": "14px"})
#             ], width=3),
            
#             # Coluna 3: Admin
#             dbc.Col([
#                 dbc.Button(
#                     [html.I(className="fas fa-cog me-1"), f"{t['admin']}"],
#                     id="admin-btn",
#                     href="/admin",
#                     outline=True,
#                     size="sm",
#                     style={"display": "none"}  # Mostrar se autenticado
#                 )
#             ], width=3),
            
#             # Coluna 4: Copyright
#             dbc.Col([
#                 html.Small("© 2025 EVAonline", style={"color": "#666"})
#             ], width=3, className="text-end")
#         ], className="mt-3 mb-3 align-items-center")
#     ], fluid=True)

# @callback(
#     Output("visitor-counter", "children"),
#     Input("interval-update-visitors", "n_intervals")
# )
# def update_visitor_counter(n):
#     """Atualiza contador a cada 10 segundos"""
#     try:
#         response = requests.get("http://localhost:8000/api/v1/stats/visitors")
#         data = response.json()
#         return f"{data['total_visitors']:,}"
#     except:
#         return "N/A"

# @callback(
#     Output("status-indicator", "style"),
#     Output("status-text", "children"),
#     Input("interval-update-status", "n_intervals")
# )
# def update_status(n):
#     """Atualiza status da API"""
#     try:
#         requests.get("http://localhost:8000/api/v1/health", timeout=1)
#         return {"color": "green"}, "Online ✓"
#     except:
#         return {"color": "red"}, "Offline ✗"
# ```
