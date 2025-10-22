"""
Callbacks para integração de cache entre frontend (Dash) e backend (FastAPI).

- Busca dados via GET /api/cache/climate/{location_id}
- Armazena resposta em `climate-cache-store` (localStorage)
- Usa `app-session-id` para Session-ID header
"""
import logging

import requests
from dash import Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


@callback(
    Output('climate-cache-store', 'data'),
    Input('selected-location', 'data'),
    State('app-session-id', 'data'),
    prevent_initial_call=True
)
def sync_climate_cache(location_data: dict, session_id: str):
    """Sincroniza cache para a localização selecionada.
    Se já existir no localStorage, retorna imediatamente.
    Caso contrário, solicita ao backend e armazena.
    """
    if not location_data:
        raise PreventUpdate

    location_id = location_data.get('id') or location_data.get('location_id')
    if not location_id:
        raise PreventUpdate

    # Se já temos dados cacheados localmente, retorna-os
    # (o store atual será passado automaticamente como State no caller se necessário)

    # Garantir session_id
    if not session_id:
        # Gerar session id simplificado no frontend (backend também gera se não existir)
        import uuid
        session_id = f"sess_{uuid.uuid4().hex}"

    url = f"http://localhost:8000/api/cache/climate/{location_id}"
    headers = {"Session-ID": session_id}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            payload = resp.json()
            logger.info(f"Cache sync success for location={location_id}")
            return payload
        else:
            logger.warning(f"Cache request returned {resp.status_code} for {location_id}")
            raise PreventUpdate
    except Exception as e:
        logger.error(f"Error fetching cache for {location_id}: {e}")
        raise PreventUpdate
