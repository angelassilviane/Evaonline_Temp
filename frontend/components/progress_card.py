"""
Componentes Dash para exibição de progresso em tempo real.

Componentes:
- ProgressCard: Card principal com status e progresso
- StatusBadge: Indicador visual de status
- ProgressBar: Barra de progresso animada
- ResultsDisplay: Tabela de resultados finais
- ProcessingStatus: Exibição formatada de status do processamento
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


class StatusType(Enum):
    """Tipos de status possíveis."""
    IDLE = "idle"
    CONNECTING = "connecting"
    DOWNLOADING = "downloading"
    PREPROCESSING = "preprocessing"
    FUSING = "fusing"
    CALCULATING = "calculating"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class StatusBadge:
    """
    Cria badges (etiquetas) visuais para status.
    
    Exemplo:
    ```python
    badge = StatusBadge.create(StatusType.CALCULATING)
    ```
    """
    
    STATUS_CONFIG = {
        StatusType.IDLE: {
            "color": "secondary",
            "icon": "bi bi-hourglass-split",
            "label": "Aguardando"
        },
        StatusType.CONNECTING: {
            "color": "info",
            "icon": "bi bi-arrow-repeat",
            "label": "Conectando..."
        },
        StatusType.DOWNLOADING: {
            "color": "info",
            "icon": "bi bi-cloud-download",
            "label": "Baixando dados..."
        },
        StatusType.PREPROCESSING: {
            "color": "info",
            "icon": "bi bi-gear",
            "label": "Pré-processando..."
        },
        StatusType.FUSING: {
            "color": "info",
            "icon": "bi bi-shuffle",
            "label": "Fusionando dados..."
        },
        StatusType.CALCULATING: {
            "color": "info",
            "icon": "bi bi-calculator",
            "label": "Calculando ETo..."
        },
        StatusType.SUCCESS: {
            "color": "success",
            "icon": "bi bi-check-circle",
            "label": "Concluído com sucesso!"
        },
        StatusType.ERROR: {
            "color": "danger",
            "icon": "bi bi-exclamation-triangle",
            "label": "Erro no processamento"
        },
        StatusType.TIMEOUT: {
            "color": "warning",
            "icon": "bi bi-clock-history",
            "label": "Tempo limite excedido"
        },
    }
    
    @classmethod
    def create(
        cls,
        status: StatusType,
        custom_label: Optional[str] = None,
        size: str = "md"
    ) -> dbc.Badge:
        """
        Cria um badge para o status.
        
        Args:
            status: Tipo de status
            custom_label: Label customizado (sobrescreve o padrão)
            size: Tamanho do badge ("sm", "md", "lg")
            
        Returns:
            dbc.Badge: Componente de badge
        """
        default_config = cls.STATUS_CONFIG[StatusType.IDLE]
        config = cls.STATUS_CONFIG.get(status, default_config)
        
        size_class = {
            "sm": "text-start small",
            "md": "text-base",
            "lg": "fs-6"
        }.get(size, "")
        
        return dbc.Badge(
            [
                html.I(className=f"{config['icon']} me-2"),
                custom_label or config["label"]
            ],
            color=config["color"],
            className=f"{size_class} px-3 py-2"
        )


class ProgressBar:
    """
    Cria barra de progresso animada com labels.
    
    Exemplo:
    ```python
    progress_bar = ProgressBar.create(75, "Processando...")
    ```
    """
    
    @classmethod
    def create(
        cls,
        value: int,
        label: str = "",
        animated: bool = True,
        show_percentage: bool = True,
        height: int = 25
    ) -> html.Div:
        """
        Cria barra de progresso.
        
        Args:
            value: Percentual (0-100)
            label: Label para exibir
            animated: Se a barra deve animar
            show_percentage: Se deve mostrar percentual
            height: Altura em pixels
            
        Returns:
            html.Div: Componente de barra de progresso
        """
        # Garantir que value está entre 0-100
        value = max(0, min(100, value))
        
        # Classe de cor baseada em valor
        if value < 33:
            color = "info"
        elif value < 66:
            color = "warning"
        else:
            color = "success"
        
        # Texto a exibir na barra
        bar_text = ""
        if show_percentage:
            bar_text = f"{value}%"
        if label and bar_text:
            bar_text = f"{label} - {bar_text}"
        elif label:
            bar_text = label
        
        animated_class = "progress-bar-animated" if animated else ""
        
        return html.Div([
            html.Div(
                bar_text,
                style={
                    "width": f"{value}%",
                    "height": f"{height}px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "color": "white",
                    "fontWeight": "bold",
                    "fontSize": "0.9rem",
                    "backgroundColor": cls._get_color_value(color),
                    "transition": "width 0.3s ease"
                },
                className=animated_class
            )
        ], style={
            "width": "100%",
            "height": f"{height}px",
            "backgroundColor": "#e9ecef",
            "borderRadius": "4px",
            "overflow": "hidden",
            "boxShadow": "inset 0 1px 2px rgba(0, 0, 0, 0.1)"
        })
    
    @staticmethod
    def _get_color_value(color: str) -> str:
        """Converte nome de cor para valor hex."""
        colors = {
            "info": "#0dcaf0",
            "warning": "#ffc107",
            "success": "#198754",
            "danger": "#dc3545"
        }
        return colors.get(color, "#0dcaf0")


class ProcessingStatus:
    """
    Exibe status de processamento com múltiplas linhas de informação.
    
    Exemplo:
    ```python
    status = ProcessingStatus.create(
        stage="Fusionando dados",
        progress=65,
        data_points=1500,
        elapsed_time=125
    )
    ```
    """
    
    @classmethod
    def create(
        cls,
        stage: str,
        progress: int,
        data_points: Optional[int] = None,
        elapsed_time: Optional[int] = None,
        remaining_time: Optional[int] = None,
        warnings: Optional[List[str]] = None
    ) -> html.Div:
        """
        Cria card de status de processamento.
        
        Args:
            stage: Nome do estágio atual
            progress: Percentual de progresso (0-100)
            data_points: Número de pontos de dados processados
            elapsed_time: Tempo decorrido em segundos
            remaining_time: Tempo restante estimado em segundos
            warnings: Lista de avisos
            
        Returns:
            html.Div: Componente de status
        """
        info_items = []
        
        # Tempo decorrido
        if elapsed_time is not None:
            elapsed_str = cls._format_time(elapsed_time)
            info_items.append(
                html.P(
                    [
                        html.I(className="bi bi-clock me-2"),
                        html.Strong("Tempo decorrido: "),
                        elapsed_str
                    ],
                    className="mb-1 small"
                )
            )
        
        # Tempo restante
        if remaining_time is not None:
            remaining_str = cls._format_time(remaining_time)
            info_items.append(
                html.P(
                    [
                        html.I(className="bi bi-hourglass-end me-2"),
                        html.Strong("Tempo restante: "),
                        remaining_str
                    ],
                    className="mb-1 small"
                )
            )
        
        # Pontos de dados
        if data_points is not None:
            info_items.append(
                html.P(
                    [
                        html.I(className="bi bi-bar-chart me-2"),
                        html.Strong("Pontos de dados: "),
                        f"{data_points:,}"
                    ],
                    className="mb-1 small"
                )
            )
        
        # Avisos
        warnings_section = []
        if warnings:
            warnings_section = [
                html.Hr(className="my-2"),
                dbc.Alert(
                    [
                        html.H6("⚠️ Avisos", className="alert-heading"),
                        html.Ul(
                            [html.Li(w, className="small") for w in warnings],
                            className="mb-0"
                        )
                    ],
                    color="warning",
                    className="py-2 mb-0"
                )
            ]
        
        return html.Div([
            html.H6(
                [
                    html.I(className="bi bi-activity me-2"),
                    stage
                ],
                className="mb-2 fw-bold text-primary"
            ),
            ProgressBar.create(progress, show_percentage=True),
            html.Hr(className="my-2"),
            html.Div(info_items),
            *warnings_section
        ])
    
    @staticmethod
    def _format_time(seconds: int) -> str:
        """Formata tempo em segundos para string legível."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class ProgressCard:
    """
    Card principal para exibição de progresso.
    
    Exemplo:
    ```python
    card = ProgressCard.create(
        status=StatusType.CALCULATING,
        progress=75,
        stage="Calculando ETo",
        location="Latitude: -10.12, Longitude: -55.23"
    )
    ```
    """
    
    @classmethod
    def create(
        cls,
        status: StatusType,
        progress: int,
        stage: str,
        location: str,
        data_points: Optional[int] = None,
        elapsed_time: Optional[int] = None,
        remaining_time: Optional[int] = None,
        warnings: Optional[List[str]] = None,
        collapsible: bool = False
    ) -> dbc.Card:
        """
        Cria card de progresso.
        
        Args:
            status: Tipo de status atual
            progress: Percentual de progresso (0-100)
            stage: Nome do estágio
            location: String com informações de localização
            data_points: Número de pontos processados
            elapsed_time: Tempo decorrido em segundos
            remaining_time: Tempo restante estimado
            warnings: Lista de avisos
            collapsible: Se o card deve ser colapsivelT
            
        Returns:
            dbc.Card: Componente de card
        """
        # Header com status
        header = dbc.CardHeader(
            dbc.Row([
                dbc.Col([
                    StatusBadge.create(status)
                ], width="auto"),
                dbc.Col([
                    html.Small(location, className="text-muted")
                ])
            ], className="align-items-center"),
            className="bg-light"
        )
        
        # Body com progresso
        body_content = ProcessingStatus.create(
            stage=stage,
            progress=progress,
            data_points=data_points,
            elapsed_time=elapsed_time,
            remaining_time=remaining_time,
            warnings=warnings
        )
        
        if collapsible:
            body = dbc.CardBody([
                dcc.Collapse(
                    body_content,
                    id="progress-collapse",
                    is_open=True,
                    className="mt-2"
                )
            ])
        else:
            body = dbc.CardBody(body_content)
        
        return dbc.Card([header, body], className="mb-3 shadow-sm")


class ResultsDisplay:
    """
    Exibe resultados finais em formato tabular.
    
    Exemplo:
    ```python
    results = ResultsDisplay.create(
        results_data={
            "data": ["2024-01-01", "2024-01-02"],
            "eto_mm": [5.23, 4.87],
            "et0_mm": [4.12, 3.98],
            "temperatura": [28.5, 29.1]
        },
        max_rows=20
    )
    ```
    """
    
    @classmethod
    def create(
        cls,
        results_data: Dict[str, List[Any]],
        title: str = "Resultados do Cálculo de ETo",
        max_rows: int = 20
    ) -> html.Div:
        """
        Cria exibição de resultados.
        
        Args:
            results_data: Dicionário com dados dos resultados
            title: Título da seção
            max_rows: Máximo de linhas a exibir
            
        Returns:
            html.Div: Componente de resultados
        """
        if not results_data or len(results_data) == 0:
            return dbc.Alert(
                "Nenhum resultado disponível.",
                color="info"
            )
        
        # Preparar dados para tabela
        keys = list(results_data.keys())
        num_rows = len(results_data[keys[0]]) if keys else 0
        
        # Limitar a linhas máximas
        display_rows = min(num_rows, max_rows)
        
        # Headers
        table_headers = [
            html.Thead(
                html.Tr([
                    html.Th(key, className="fw-bold") for key in keys
                ])
            )
        ]
        
        # Rows
        table_rows = []
        for i in range(display_rows):
            row_data = [
                html.Td(
                    cls._format_value(results_data[key][i]),
                    className=(
                        "text-end"
                        if isinstance(results_data[key][i], (int, float))
                        else ""
                    )
                )
                for key in keys
            ]
            table_rows.append(html.Tr(row_data))
        
        table_body = html.Tbody(table_rows)
        
        # Footer com info
        footer_text = f"Mostrando {display_rows} de {num_rows} registros"
        
        return html.Div([
            html.H5(
                [
                    html.I(className="bi bi-table me-2"),
                    title
                ],
                className="mb-3 fw-bold"
            ),
            dbc.Table(
                [*table_headers, table_body],
                bordered=True,
                hover=True,
                responsive=True,
                className="mb-2"
            ),
            html.Small(footer_text, className="text-muted d-block text-end")
        ], className="mt-3")
    
    @staticmethod
    def _format_value(value: Any) -> str:
        """Formata valor para exibição."""
        if isinstance(value, float):
            return f"{value:.2f}"
        elif isinstance(value, str):
            # Tenta parse de data
            try:
                dt = datetime.fromisoformat(value)
                return dt.strftime("%d/%m/%Y")
            except:
                return value
        else:
            return str(value)


__all__ = [
    "StatusBadge",
    "StatusType",
    "ProgressBar",
    "ProcessingStatus",
    "ProgressCard",
    "ResultsDisplay",
]
