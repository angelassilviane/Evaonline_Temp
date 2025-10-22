"""
Componente pequeno para botão de favorito (★/☆) usado em cards de localização.
"""
from dash import html


def create_favorite_button(location_id: int):
    """Returna um botão com id parametrizado para toggle de favorito."""
    return html.Button(
        id={"type": "favorite-btn", "index": location_id},
        children='☆',
        title='Adicionar/remover favorito',
        n_clicks=0,
        className='btn btn-light favorite-btn'
    )
