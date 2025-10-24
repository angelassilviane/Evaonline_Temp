"""
Callbacks da página ETo - Cálculos e integração com WebSocket em tempo real.

Este módulo integra:
- WebSocket client para receber atualizações em tempo real
- Comunicação com API /internal/eto/eto_calculate
- Componentes de ProgressCard para exibir progresso em tempo real
- Tratamento de mensagens (PROGRESS, SUCCESS, ERROR, TIMEOUT)
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import dash
import dash_bootstrap_components as dbc
import requests
from dash import dcc, html
from dash.dependencies import Input, Output, State
from loguru import logger

from frontend.components.progress_card import ProgressCard
from frontend.utils.coordinates import format_coordinates
from frontend.utils.websocket_handler import MessageType, WebSocketConnectionManager

# Configurar logging
logger.enable("frontend.callbacks.eto_callbacks")

# Gerenciador global de conexões WebSocket
_ws_manager = WebSocketConnectionManager()


def register_eto_callbacks(app: dash.Dash):
    """
    Registra todos os callbacks relacionados à página ETo com integração WebSocket.
    
    Callbacks:
    1. Cálculo de ETo do dia atual com WebSocket (abre modal)
    2. Recebimento de mensagens WebSocket em tempo real
    3. Cálculo de ETo do período (redireciona para página ETo)
    
    Args:
        app: Instância do aplicativo Dash
    """
    
    # =========================================================================
    # CALLBACK 1: Calcular ETo do dia atual com WebSocket
    # =========================================================================
    @app.callback(
        [Output('result-modal', 'is_open'),
         Output('modal-title', 'children'),
         Output('modal-body', 'children'),
         Output('calculation-state', 'data')],
        [Input('calc-eto-today-btn', 'n_clicks'),
         Input('close-modal', 'n_clicks'),
         Input('websocket-interval', 'n_intervals')],
        [State('selected-location', 'data'),
         State('result-modal', 'is_open'),
         State('calculation-state', 'data')],
        prevent_initial_call=True
    )
    def calc_eto_today(calc_clicks, close_clicks, n_intervals, location_data, 
                       is_open, calc_state):
        """
        Inicia cálculo de ETo do dia atual com WebSocket para atualizações em tempo real.
        
        Fluxo:
        1. Usuário clica em "Calcular ETo Hoje"
        2. POST para /internal/eto/eto_calculate
        3. Recebe task_id
        4. Abre modal com ProgressCard
        5. Cria conexão WebSocket em ws/task_status/{task_id}
        6. WebSocket recebe mensagens em background
        7. Intervalo (2s) verifica novas mensagens e atualiza UI
        8. Ao fim: exibe resultados ou erro
        
        Args:
            calc_clicks: Cliques no botão calcular
            close_clicks: Cliques no botão fechar
            n_intervals: Intervalo para atualizar WebSocket (2s)
            location_data: Localização selecionada (lat, lng, elevation)
            is_open: Modal aberto?
            calc_state: Estado do cálculo (task_id, status, messages, etc)
            
        Returns:
            (is_open, title, body, calc_state)
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # =====================================================================
        # CASO 1: Fechar modal
        # =====================================================================
        if button_id == 'close-modal':
            logger.info("🔴 Usuário fechou modal")
            if calc_state and calc_state.get('task_id'):
                task_id = calc_state['task_id']
                _ws_manager.disconnect(task_id)
            
            return False, dash.no_update, dash.no_update, None
        
        # =====================================================================
        # CASO 2: Iniciar novo cálculo
        # =====================================================================
        if (button_id == 'calc-eto-today-btn' and 
            calc_clicks and calc_clicks > 0 and location_data):
            
            logger.info(f"🟢 Iniciando cálculo ETo hoje")
            
            try:
                # 1. POST para iniciar cálculo
                payload = {
                    "lat": location_data['lat'],
                    "lng": location_data['lng'],
                    "elevation": location_data.get('elevation', 0),
                    "database": "nasa_power",
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": datetime.now().strftime("%Y-%m-%d"),
                }
                
                logger.info(f"📡 POST /internal/eto/eto_calculate")
                response = requests.post(
                    "http://localhost:8000/internal/eto/eto_calculate",
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                task_id = result.get('task_id')
                
                if not task_id:
                    raise ValueError(f"API retornou sem task_id: {result}")
                
                logger.info(f"✅ Task criada: task_id={task_id}")
                
                # 2. Inicializar estado
                calc_state = {
                    'task_id': task_id,
                    'status': 'QUEUED',
                    'step': 'Iniciando cálculo...',
                    'progress': 0,
                    'results': None,
                    'error': None
                }
                
                # 3. Conectar WebSocket
                def on_ws_message(msg):
                    """Callback para mensagens WebSocket (não faz nada aqui, apenas loga)."""
                    logger.debug(
                        f"📨 WebSocket {msg.type.value}: "
                        f"step={msg.data.get('step')}, "
                        f"progress={msg.data.get('progress')}"
                    )
                
                _ws_manager.connect_sync(task_id, on_message=on_ws_message)
                logger.info(f"🔗 WebSocket conectado: {task_id}")
                
                # 4. Preparar UI
                lat = location_data['lat']
                lng = location_data['lng']
                lat_fmt, lng_fmt = format_coordinates(lat, lng)
                
                title = [
                    html.I(className="fas fa-calculator me-2"),
                    "Cálculo de ETo - Hoje (Em Tempo Real)"
                ]
                
                body = ProgressCard.create(
                    task_id=task_id,
                    status='PROCESSING',
                    step='Iniciando...',
                    progress=5,
                    location_lat=lat_fmt,
                    location_lng=lng_fmt,
                    results=None
                )
                
                logger.info(f"📊 Modal aberto com ProgressCard")
                
                return True, title, body, calc_state
                
            except requests.RequestException as e:
                logger.error(f"❌ Erro na requisição: {e}")
                title = [html.I(className="fas fa-exclamation-triangle me-2"),
                         "Erro no Cálculo"]
                body = dbc.Alert(
                    f"Erro ao conectar com o servidor: {str(e)}",
                    color="danger"
                )
                return True, title, body, None
            
            except Exception as e:
                logger.error(f"❌ Erro inesperado: {e}")
                title = [html.I(className="fas fa-exclamation-triangle me-2"),
                         "Erro no Cálculo"]
                body = dbc.Alert(
                    f"Erro inesperado: {str(e)}",
                    color="danger"
                )
                return True, title, body, None
        
        # =====================================================================
        # CASO 3: Atualizar via WebSocket (intervalo)
        # =====================================================================
        if button_id == 'websocket-interval' and calc_state and is_open:
            task_id = calc_state.get('task_id')
            
            if not task_id:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            # Obter status e mensagens
            ws_status = _ws_manager.get_status(task_id)
            latest_msg = _ws_manager.get_latest_message(task_id)
            
            logger.debug(f"🔄 Verificando WebSocket {task_id}: status={ws_status}")
            
            # Se não há mensagens ainda, não atualizar
            if not latest_msg:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            # Atualizar calc_state com dados da mensagem
            new_calc_state = calc_state.copy()
            new_calc_state['status'] = latest_msg.type.value
            new_calc_state['step'] = latest_msg.data.get('step', 'Processando...')
            new_calc_state['progress'] = latest_msg.data.get('progress', 0)
            
            # Se for resultado final, armazenar
            if latest_msg.type in [MessageType.SUCCESS, MessageType.ERROR]:
                if latest_msg.type == MessageType.SUCCESS:
                    new_calc_state['results'] = latest_msg.data.get('results')
                else:
                    new_calc_state['error'] = latest_msg.data.get('error')
            
            # Atualizar ProgressCard
            lat = calc_state.get('location_lat', '?')
            lng = calc_state.get('location_lng', '?')
            
            body = ProgressCard.create(
                task_id=task_id,
                status=new_calc_state['status'],
                step=new_calc_state['step'],
                progress=new_calc_state['progress'],
                location_lat=lat,
                location_lng=lng,
                results=new_calc_state.get('results'),
                error=new_calc_state.get('error')
            )
            
            logger.info(
                f"📊 Atualizado: status={new_calc_state['status']}, "
                f"progress={new_calc_state['progress']}%"
            )
            
            # Se finalizou, fechar WebSocket após alguns ciclos
            if new_calc_state['status'] in ['SUCCESS', 'ERROR', 'TIMEOUT']:
                logger.info(f"✅ Tarefa finalizada: {task_id}")
                # Nota: desconectar seria aqui, mas deixamos para quando o usuário fecha
            
            return True, dash.no_update, body, new_calc_state
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # =========================================================================
    # CALLBACK 2: Calcular ETo do período (redireciona para página ETo)
    # =========================================================================
    @app.callback(
        [Output('url', 'pathname', allow_duplicate=True),
         Output('selected-location', 'data', allow_duplicate=True)],
        [Input('calc-eto-period-btn', 'n_clicks')],
        [State('selected-location', 'data')],
        prevent_initial_call=True
    )
    def calc_eto_period(n_clicks, location_data):
        """
        Redireciona para a página ETo com os dados da localização selecionada.
        
        Args:
            n_clicks: Número de cliques no botão
            location_data: Dados da localização selecionada
            
        Returns:
            Tupla (pathname, location_data) para redirecionamento
        """
        if not n_clicks or not location_data:
            return dash.no_update, dash.no_update
        
        logger.info(f"📍 Redirecionando para /eto")
        
        # Adicionar flag indicando que veio do mapa
        location_data['from_map'] = True
        
        # Redirecionar para a página ETo
        return '/eto', location_data
