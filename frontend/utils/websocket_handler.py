"""
Gerenciador de conexões WebSocket para callbacks Dash.

Este módulo fornece abstrações para trabalhar com WebSocket em um contexto
de callbacks síncronos do Dash, usando threading para receber mensagens
em background.

Classes:
    WebSocketConnectionManager: Gerencia conexões WebSocket por task_id
    WebSocketMessage: Estrutura de dados para mensagens WebSocket
"""

import asyncio
import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import websockets
from loguru import logger
from websockets.exceptions import ConnectionClosed


class MessageType(Enum):
    """Tipos de mensagens do WebSocket."""
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class WebSocketMessage:
    """Estrutura de mensagem WebSocket."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp
        }


class WebSocketConnectionManager:
    """
    Gerencia conexões WebSocket para múltiplas tarefas em paralelo.
    
    Usa threading para receber mensagens em background, permitindo
    que callbacks Dash síncronos acessem dados sem bloquear.
    
    Exemplo:
        ```python
        manager = WebSocketConnectionManager()
        
        # Conectar a uma tarefa
        await manager.connect(task_id="abc123", 
                             on_message=lambda msg: print(f"Msg: {msg}"))
        
        # Acessar mensagens recebidas
        messages = manager.get_messages(task_id="abc123")
        
        # Desconectar
        manager.disconnect(task_id="abc123")
        ```
    """
    
    def __init__(self, ws_base_url: str = "ws://localhost:8000/ws/task_status"):
        """
        Inicializa o gerenciador.
        
        Args:
            ws_base_url: URL base para conexão WebSocket (sem task_id)
        """
        self.ws_base_url = ws_base_url
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        logger.info(f"📊 WebSocketConnectionManager inicializado: {ws_base_url}")
    
    def connect_sync(self, task_id: str, 
                     on_message: Optional[Callable[[WebSocketMessage], None]] = None) -> Dict[str, Any]:
        """
        Conecta a um WebSocket (bloqueante, executa em thread separada).
        
        Args:
            task_id: ID da tarefa para conectar
            on_message: Callback chamado ao receber mensagens
            
        Returns:
            Dict com status da conexão
        """
        with self.lock:
            if task_id in self.connections:
                logger.warning(f"⚠️ Conexão {task_id} já existe")
                return {"status": "already_connected", "task_id": task_id}
            
            # Iniciar thread de conexão
            thread = threading.Thread(
                target=self._connect_thread,
                args=(task_id, on_message),
                daemon=True,
                name=f"WS-{task_id[:8]}"
            )
            
            self.connections[task_id] = {
                "thread": thread,
                "messages": [],
                "status": "connecting",
                "on_message": on_message
            }
            
            thread.start()
            logger.info(f"🔗 Thread de conexão WebSocket iniciada: {task_id}")
        
        return {"status": "connecting", "task_id": task_id}
    
    def _connect_thread(self, task_id: str, 
                        on_message: Optional[Callable[[WebSocketMessage], None]]):
        """
        Executa em thread separada para receber mensagens.
        
        Args:
            task_id: ID da tarefa
            on_message: Callback para mensagens
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                self._receive_messages(task_id, on_message)
            )
        except Exception as e:
            logger.error(f"❌ Erro em thread WebSocket {task_id}: {e}")
            with self.lock:
                if task_id in self.connections:
                    self.connections[task_id]["status"] = "error"
                    self.connections[task_id]["error"] = str(e)
        finally:
            loop.close()
    
    async def _receive_messages(self, task_id: str, 
                               on_message: Optional[Callable[[WebSocketMessage], None]]):
        """
        Conecta e recebe mensagens do WebSocket.
        
        Args:
            task_id: ID da tarefa
            on_message: Callback para mensagens
        """
        url = f"{self.ws_base_url}/{task_id}"
        logger.info(f"🔗 Conectando WebSocket: {url}")
        
        try:
            async with websockets.connect(url) as websocket:
                with self.lock:
                    if task_id in self.connections:
                        self.connections[task_id]["status"] = "connected"
                
                logger.info(f"✅ WebSocket conectado: {task_id}")
                
                # Receber mensagens
                async for message_str in websocket:
                    try:
                        # Parse JSON
                        data = json.loads(message_str)
                        
                        # Criar estrutura de mensagem
                        msg_type = MessageType(data.get("type", "PROGRESS"))
                        msg = WebSocketMessage(
                            type=msg_type,
                            data=data.get("data", {})
                        )
                        
                        # Armazenar mensagem
                        with self.lock:
                            if task_id in self.connections:
                                self.connections[task_id]["messages"].append(msg)
                        
                        # Chamar callback
                        if on_message:
                            try:
                                on_message(msg)
                            except Exception as e:
                                logger.error(f"Erro no callback de mensagem: {e}")
                        
                        # Log de debug
                        logger.debug(
                            f"📨 Mensagem {msg_type.value}: {task_id} "
                            f"(step: {msg.data.get('step', 'N/A')}, "
                            f"progress: {msg.data.get('progress', 'N/A')})"
                        )
                        
                        # Se for SUCCESS/ERROR/TIMEOUT, parar loop
                        if msg_type in [MessageType.SUCCESS, MessageType.ERROR, 
                                       MessageType.TIMEOUT]:
                            logger.info(f"✅ Tarefa finalizada: {task_id} ({msg_type.value})")
                            with self.lock:
                                if task_id in self.connections:
                                    self.connections[task_id]["status"] = msg_type.value
                            break
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"Erro ao fazer parse JSON: {e}")
                    except Exception as e:
                        logger.error(f"Erro ao processar mensagem: {e}")
        
        except ConnectionClosed:
            logger.info(f"🔴 WebSocket desconectado: {task_id}")
            with self.lock:
                if task_id in self.connections:
                    self.connections[task_id]["status"] = "closed"
        
        except Exception as e:
            logger.error(f"❌ Erro na conexão WebSocket {task_id}: {e}")
            with self.lock:
                if task_id in self.connections:
                    self.connections[task_id]["status"] = "error"
                    self.connections[task_id]["error"] = str(e)
    
    def get_messages(self, task_id: str) -> List[WebSocketMessage]:
        """
        Retorna todas as mensagens recebidas para uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Lista de mensagens recebidas
        """
        with self.lock:
            if task_id in self.connections:
                return self.connections[task_id].get("messages", []).copy()
        return []
    
    def get_status(self, task_id: str) -> str:
        """
        Retorna status da conexão.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Status: "connecting", "connected", "SUCCESS", "ERROR", "closed", etc
        """
        with self.lock:
            if task_id in self.connections:
                return self.connections[task_id].get("status", "unknown")
        return "not_found"
    
    def get_latest_message(self, task_id: str) -> Optional[WebSocketMessage]:
        """
        Retorna a última mensagem recebida.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Última mensagem ou None
        """
        messages = self.get_messages(task_id)
        return messages[-1] if messages else None
    
    def disconnect(self, task_id: str) -> Dict[str, Any]:
        """
        Desconecta de um WebSocket.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Dict com resumo da desconexão
        """
        with self.lock:
            if task_id not in self.connections:
                return {"status": "not_found", "task_id": task_id}
            
            conn_data = self.connections[task_id]
            messages = conn_data.get("messages", [])
            status = conn_data.get("status", "unknown")
            
            # Remover do dicionário
            del self.connections[task_id]
            
            logger.info(
                f"🔌 Desconectado {task_id}: "
                f"status={status}, mensagens={len(messages)}"
            )
        
        return {
            "task_id": task_id,
            "status": status,
            "message_count": len(messages),
            "last_message": messages[-1].to_dict() if messages else None
        }
    
    def disconnect_all(self) -> Dict[str, Any]:
        """Desconecta todos os WebSockets."""
        with self.lock:
            count = len(self.connections)
            self.connections.clear()
        
        logger.info(f"🔌 Desconectados {count} WebSockets")
        return {"disconnected_count": count}
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de conexões."""
        with self.lock:
            stats = {
                "active_connections": len(self.connections),
                "connections_by_status": {},
                "total_messages": 0
            }
            
            for task_id, conn_data in self.connections.items():
                status = conn_data.get("status", "unknown")
                stats["connections_by_status"][status] = \
                    stats["connections_by_status"].get(status, 0) + 1
                stats["total_messages"] += len(conn_data.get("messages", []))
            
            return stats
