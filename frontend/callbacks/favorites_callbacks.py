"""
Callbacks para integração de favoritos entre frontend (Dash) e backend (FastAPI).

- Toggle favorito (POST / DELETE)
- Atualiza `favorites-store` no localStorage
- Atualiza botão visual (★ vs ☆)
"""
import logging

import requests
from dash import ALL, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


@callback(
    Output('favorites-store', 'data'),
    Input({'type': 'favorite-btn', 'index': ALL}, 'n_clicks'),
    State('favorites-store', 'data'),
    State('app-session-id', 'data'),
    prevent_initial_call=True
)
def toggle_favorite(n_clicks_list, current_favorites, session_id):
    """Detecta qual botão foi clicado e alterna favorito no backend.
    Retorna a lista atualizada de favorites.
    """
    if not ctx.triggered_id:
        raise PreventUpdate

    triggered = ctx.triggered_id
    location_id = triggered['index']

    if not session_id:
        import uuid
        session_id = f"sess_{uuid.uuid4().hex}"

    # Ensure list
    if current_favorites is None:
        current_favorites = []

    is_favorited = location_id in current_favorites

    try:
        if is_favorited:
            # DELETE
            url = f"http://localhost:8000/api/favorites/{location_id}"
            resp = requests.delete(url, headers={"Session-ID": session_id}, timeout=10)
            if resp.status_code == 200:
                updated = [f for f in current_favorites if f != location_id]
                return updated
            else:
                logger.warning(f"Failed to delete favorite {location_id}: {resp.status_code}")
                raise PreventUpdate
        else:
            # POST
            url = f"http://localhost:8000/api/favorites"
            resp = requests.post(url, params={"location_id": location_id}, headers={"Session-ID": session_id}, timeout=10)
            if resp.status_code in (200, 201):
                return list(set(current_favorites) | {location_id})
            else:
                logger.warning(f"Failed to add favorite {location_id}: {resp.status_code}")
                raise PreventUpdate
    except Exception as e:
        logger.error(f"Error toggling favorite {location_id}: {e}")
        raise PreventUpdate


@callback(
    Output({'type': 'favorite-btn', 'index': ALL}, 'children'),
    Input('favorites-store', 'data'),
    State({'type': 'favorite-btn', 'index': ALL}, 'id'),
    prevent_initial_call=True
)
def update_favorite_buttons(favorites, button_ids):
    if not button_ids:
        raise PreventUpdate

    favorites_set = set(favorites or [])
    return [ ('★' if btn_id['index'] in favorites_set else '☆') for btn_id in button_ids ]
