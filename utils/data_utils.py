import logging
import os
from datetime import date, timedelta
from typing import Dict, Optional, Tuple

import pandas as pd

from utils.get_translations import get_translations

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def build_input_data(
    mode: str,
    database: Optional[str],
    data_inicial: Optional[str],
    data_final: Optional[str],
    lat: Optional[float],
    lng: Optional[float],
    elevation: Optional[float],
    estado: Optional[str] = None,
    cidade: Optional[str] = None,
    lang: str = "pt"
) -> Tuple[Dict[str, Optional[object]], list]:
    """
    Build the input data dictionary based on the calculation mode.

    Args:
        mode (str): Calculation mode ("Global").
        database (Optional[str]): Selected database (e.g., "NASA POWER").
        data_inicial (Optional[str]): Start date (DD/MM/YYYY).
        data_final (Optional[str]): End date (DD/MM/YYYY).
        lat (Optional[float]): Latitude.
        lng (Optional[float]): Longitude.
        elevation (Optional[float]): Elevation in meters.
        estado (Optional[str]): State (not used).
        cidade (Optional[str]): City (not used).
        lang (str): Language code ('pt' for Portuguese, 'en' for English).

    Returns:
        Tuple[Dict[str, Optional[object]], list]: Input data dictionary and list of warnings.

    Example:
        >>> input_data, warnings = build_input_data(
        ...     mode="Global", database="NASA POWER", data_inicial="01/01/2023",
        ...     data_final="07/01/2023", lat=-10.0, lng=-45.0, elevation=500.0, lang="en"
        ... )
    """
    t = get_translations(lang)
    warnings = []
    input_data = {
        "mode": mode,
        "database": database,
        "data_inicial": data_inicial,
        "data_final": data_final
    }

    # Validate mode
    if mode != "Global":
        warnings.append(t["invalid_mode"].format(mode))
        logger.error(warnings[-1])
        return input_data, warnings

    # Validate common parameters
    hoje = date.today()
    um_ano_atras = hoje - timedelta(days=365)
    limite_futuro = hoje + timedelta(days=2)

    if not database or database == t["choose_database"]:
        warnings.append(t["no_database_selected"])
        logger.error(warnings[-1])
    if not data_inicial or not data_final:
        warnings.append(t["no_dates_selected"])
        logger.error(warnings[-1])
    else:
        try:
            data_inicial_dt = pd.to_datetime(data_inicial, format="%d/%m/%Y")
            data_final_dt = pd.to_datetime(data_final, format="%d/%m/%Y")
            delta = (data_final_dt - data_inicial_dt).days + 1
            if data_final_dt < data_inicial_dt:
                warnings.append(t["invalid_date_range"])
                logger.error(warnings[-1])
            elif not (7 <= delta <= 15):
                warnings.append(t["invalid_period"].format(delta))
                logger.error(warnings[-1])
            elif data_inicial_dt < um_ano_atras:
                warnings.append(t["date_too_old"].format(um_ano_atras.strftime("%d/%m/%Y")))
                logger.error(warnings[-1])
            elif data_final_dt > limite_futuro:
                warnings.append(t["date_too_future"].format(limite_futuro.strftime("%d/%m/%Y")))
                logger.error(warnings[-1])
        except ValueError as e:
            warnings.append(t["invalid_date_format"].format(str(e)))
            logger.error(warnings[-1])

    # Mode-specific parameters
    if mode == "Global":
        if lat is None or lng is None:
            warnings.append(t["no_coords_global"])
            logger.error(warnings[-1])
        input_data.update({"latitude": lat, "longitude": lng, "elevation": elevation})
    else:
        # Modo não reconhecido - usar coordenadas globais como fallback
        if lat is None or lng is None:
            warnings.append(t["no_coords_global"])
            logger.error(warnings[-1])
        else:
            input_data.update({"latitude": lat, "longitude": lng, "elevation": elevation})

    return input_data, warnings
