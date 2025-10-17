"""
Funções para formatação de coordenadas geográficas.
"""


def format_coordinates(lat: float, lng: float) -> tuple[str, str]:
    """
    Formata coordenadas no formato geográfico com direções cardeais.
    
    Args:
        lat: Latitude em graus decimais
        lng: Longitude em graus decimais
        
    Returns:
        tuple: (latitude_formatada, longitude_formatada)
        
    Example:
        >>> format_coordinates(-23.5505, -46.6333)
        ('23.5505° S', '46.6333° W')
    """
    lat_dir = 'N' if lat >= 0 else 'S'
    lng_dir = 'E' if lng >= 0 else 'W'
    
    lat_formatted = f"{abs(lat):.4f}° {lat_dir}"
    lng_formatted = f"{abs(lng):.4f}° {lng_dir}"
    
    return lat_formatted, lng_formatted
