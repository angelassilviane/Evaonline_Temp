"""
Callbacks para integração de cache entre frontend (Dash) e backend (FastAPI).

Features:
- Busca dados via GET /api/cache/climate/{location_id}
- Armazena resposta em `climate-cache-store` (localStorage)
- Usa `app-session-id` para Session-ID header
- Gerencia TTL de cache (expiração automática)
- Sincroniza estado entre stores
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests
from dash import Input, Output, State, callback, ctx, dcc, html
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)

# Constantes de Cache
CACHE_TTL_MINUTES = 60
MAX_CACHE_ENTRIES = 50


def _is_cache_expired(entry: Dict[str, Any]) -> bool:
    """Verifica se uma entrada de cache expirou."""
    if "timestamp" not in entry or "ttl_minutes" not in entry:
        return True
    
    entry_time = datetime.fromisoformat(entry["timestamp"])
    ttl = timedelta(minutes=entry["ttl_minutes"])
    return datetime.now() > entry_time + ttl


@callback(
    Output('climate-cache-store', 'data'),
    Input('selected-location', 'data'),
    State('app-session-id', 'data'),
    State('climate-cache-store', 'data'),
    prevent_initial_call=True
)
def sync_climate_cache(location_data: dict, session_id: str, cache_data: dict):
    """
    Sincroniza cache para a localização selecionada.
    
    Lógica:
    1. Se já existir no localStorage e não expirado → usar
    2. Caso contrário → buscar do backend e armazenar
    3. Adicionar timestamp e TTL
    """
    if not location_data:
        raise PreventUpdate

    location_id = location_data.get('id') or location_data.get('location_id')
    if not location_id:
        raise PreventUpdate

    # Chave do cache
    cache_key = f"location_{location_id}"
    
    # Verificar se já temos no cache (e não expirou)
    if cache_data and isinstance(cache_data, dict):
        if cache_key in cache_data:
            entry = cache_data[cache_key]
            if not _is_cache_expired(entry):
                logger.info(f"✅ Cache HIT para {location_id} (não expirado)")
                return cache_data
            else:
                logger.info(f"⏰ Cache EXPIRED para {location_id} (removendo)")
                del cache_data[cache_key]
    
    # Garantir session_id
    if not session_id:
        import uuid
        session_id = f"sess_{uuid.uuid4().hex}"

    # Cache miss → buscar do backend
    url = f"http://localhost:8000/api/cache/climate/{location_id}"
    headers = {"Session-ID": session_id}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            payload = resp.json()
            
            # Armazenar com metadata
            cache_entry = {
                "timestamp": datetime.now().isoformat(),
                "ttl_minutes": CACHE_TTL_MINUTES,
                "data": payload
            }
            
            # Adicionar ao cache
            if not isinstance(cache_data, dict):
                cache_data = {}
            
            cache_data[cache_key] = cache_entry
            
            # Limitar tamanho do cache
            if len(cache_data) > MAX_CACHE_ENTRIES:
                # Remover entrada mais antiga
                oldest_key = min(
                    cache_data,
                    key=lambda k: cache_data[k].get("timestamp", "")
                )
                del cache_data[oldest_key]
                logger.info(f"🗑️ Removido cache antigo: {oldest_key}")
            
            logger.info(f"💾 Cache MISS → armazenado para {location_id}")
            return cache_data
        else:
            logger.warning(f"Cache request returned {resp.status_code} for {location_id}")
            raise PreventUpdate
    except Exception as e:
        logger.error(f"Error fetching cache for {location_id}: {e}")
        raise PreventUpdate


@callback(
    Output('app-session-id', 'data'),
    Input('app-session-id', 'id'),
    prevent_initial_call=True
)
def initialize_session_id(session_id_trigger):
    """Inicializa session ID se não existir."""
    import uuid
    return f"sess_{uuid.uuid4().hex}"


@callback(
    Output('cache-stats', 'children'),
    Input('climate-cache-store', 'data'),
    prevent_initial_call=True
)
def update_cache_stats(cache_data):
    """Exibe estatísticas do cache."""
    if not cache_data or not isinstance(cache_data, dict):
        return html.Small("💾 Cache: vazio", className="text-muted")
    
    count = len(cache_data)
    return html.Small(f"💾 Cache: {count}/{MAX_CACHE_ENTRIES} entradas", className="text-info")
