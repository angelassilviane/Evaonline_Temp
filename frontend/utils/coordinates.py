"""
Funções para formatação de coordenadas geográficas com validação e cache.
"""
from functools import lru_cache
from typing import Tuple


@lru_cache(maxsize=1000)
def format_coordinates(lat: float, lng: float) -> Tuple[str, str]:
    """
    Formata coordenadas no formato geográfico com direções cardeais.
    Com cache para melhor performance em requisições repetidas.
    
    Args:
        lat: Latitude em grais decimais (-90 a 90)
        lng: Longitude em graus decimais (-180 a 180)
        
    Returns:
        tuple: (latitude_formatada, longitude_formatada)
        
    Raises:
        ValueError: Se coordenadas fora do range válido
        
    Example:
        >>> format_coordinates(-23.5505, -46.6333)
        ('23.5505° S', '46.6333° W')
    """
    # Validação rigorosa das coordenadas
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude {lat} fora do range válido (-90 a 90)")
    if not (-180 <= lng <= 180):
        raise ValueError(f"Longitude {lng} fora do range válido (-180 a 180)")
    
    lat_dir = 'N' if lat >= 0 else 'S'
    lng_dir = 'E' if lng >= 0 else 'W'
    
    # Formatação com precisão otimizada
    lat_formatted = f"{abs(lat):.6f}° {lat_dir}"  # Aumentei precisão
    lng_formatted = f"{abs(lng):.6f}° {lng_dir}"
    
    return lat_formatted, lng_formatted


def format_coordinates_safe(lat: float, lng: float) -> Tuple[str, str]:
    """
    Versão segura que não levanta exceções.
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        tuple: Coordenadas formatadas ou mensagem de erro
    """
    try:
        return format_coordinates(lat, lng)
    except (ValueError, TypeError) as e:
        return f"Lat: {lat} (inválida)", f"Lng: {lng} (inválida)"


def parse_coordinate_string(coord_str: str) -> float:
    """
    Converte string de coordenada para float.
    
    Args:
        coord_str: String no formato "23.5505° S"
        
    Returns:
        float: Valor da coordenada
    """
    try:
        # Remove símbolos de grau e direção, converte para float
        value = float(coord_str.replace('°', '').split()[0])
        direction = coord_str.split()[-1]
        
        if direction in ['S', 'W']:
            return -value
        return value
    except (ValueError, IndexError):
        raise ValueError(f"Formato de coordenada inválido: {coord_str}")
