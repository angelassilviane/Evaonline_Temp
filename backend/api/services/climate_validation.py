"""
Serviço de validação centralizado para dados climáticos.
Consolidação de validações espalhadas em climate_sources_routes e eto_routes.

Benefício: DRY - validações em um único lugar, reutilizáveis.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

from loguru import logger


class ClimateValidationService:
    """Centraliza validações de coordenadas e datas climáticas."""
    
    # Constantes de validação
    LAT_MIN, LAT_MAX = -90.0, 90.0
    LON_MIN, LON_MAX = -180.0, 180.0
    
    # Variáveis válidas
    VALID_CLIMATE_VARIABLES = {
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "solar_radiation",
        "pressure_msl",
        "evapotranspiration",
    }
    
    # Fontes válidas
    VALID_SOURCES = {"openmeteo", "nasa_power", "met_norway", "nws"}
    
    @staticmethod
    def validate_coordinates(
        lat: float,
        lon: float,
        location_name: str = "Location"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida coordenadas geográficas.
        
        Args:
            lat: Latitude
            lon: Longitude
            location_name: Nome do local (para mensagens de erro)
        
        Returns:
            Tupla (válido, detalhes)
        """
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            return False, {"error": "Invalid coordinates format"}
        
        errors = []
        
        lat_min = ClimateValidationService.LAT_MIN
        lat_max = ClimateValidationService.LAT_MAX
        lon_min = ClimateValidationService.LON_MIN
        lon_max = ClimateValidationService.LON_MAX
        
        if not lat_min <= lat <= lat_max:
            errors.append(
                f"Latitude {lat} out of range "
                f"({lat_min}~{lat_max})"
            )
        
        if not lon_min <= lon <= lon_max:
            errors.append(
                f"Longitude {lon} out of range "
                f"({lon_min}~{lon_max})"
            )
        
        if errors:
            logger.warning(
                f"Coordinate validation failed "
                f"for {location_name}: {errors}"
            )
            return False, {"errors": errors}
        
        logger.debug(f"Coordinates validated: {location_name} ({lat}, {lon})")
        return True, {"lat": lat, "lon": lon, "valid": True}
    
    @staticmethod
    def validate_date_range(
        start_date: str,
        end_date: str,
        allow_future: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida intervalo de datas.
        
        Args:
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            allow_future: Se permite datas futuras
        
        Returns:
            Tupla (válido, detalhes)
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            return False, {"error": f"Invalid date format: {e}"}
        
        errors = []
        today = datetime.now().date()
        
        if start > end:
            errors.append(f"Start date {start} > end date {end}")
        
        if not allow_future:
            if start > today:
                errors.append(f"Start date {start} is in the future")
            if end > today:
                errors.append(f"End date {end} is in the future")
        
        # Verificar span máximo (5 anos)
        max_span = timedelta(days=365 * 5)
        if end - start > max_span:
            errors.append(
                f"Date range too long (max 5 years, got {end - start})"
            )
        
        if errors:
            logger.warning(f"Date range validation failed: {errors}")
            return False, {"errors": errors}
        
        logger.debug(f"Date range validated: {start} to {end}")
        return True, {"start": start, "end": end, "valid": True}
    
    @staticmethod
    def validate_variables(
        variables: list
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida lista de variáveis climáticas.
        
        Args:
            variables: Lista de variáveis desejadas
        
        Returns:
            Tupla (válido, detalhes)
        """
        if not variables:
            return False, {"error": "At least one variable is required"}
        
        invalid_vars = (
            set(variables) -
            ClimateValidationService.VALID_CLIMATE_VARIABLES
        )
        
        if invalid_vars:
            logger.warning(f"Invalid climate variables: {invalid_vars}")
            return False, {
                "error": f"Invalid variables: {invalid_vars}",
                "valid_options": list(
                    ClimateValidationService.VALID_CLIMATE_VARIABLES
                )
            }
        
        logger.debug(f"Variables validated: {variables}")
        return True, {"variables": variables, "valid": True}
    
    @staticmethod
    def validate_source(source: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida fonte de dados.
        
        Args:
            source: Nome da fonte
        
        Returns:
            Tupla (válido, detalhes)
        """
        if source not in ClimateValidationService.VALID_SOURCES:
            logger.warning(f"Invalid source: {source}")
            return False, {
                "error": f"Invalid source: {source}",
                "valid_options": list(
                    ClimateValidationService.VALID_SOURCES
                )
            }
        
        logger.debug(f"Source validated: {source}")
        return True, {"source": source, "valid": True}
    
    @staticmethod
    def validate_all(
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        variables: list,
        source: str = "openmeteo",
        allow_future: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida todos os parâmetros de uma vez.
        
        Args:
            lat, lon: Coordenadas
            start_date, end_date: Intervalo de datas
            variables: Variáveis climáticas
            source: Fonte de dados
            allow_future: Permite datas futuras
        
        Returns:
            Tupla (válido, detalhes)
        """
        validations = [
            ("coordinates", ClimateValidationService.validate_coordinates(
                lat, lon
            )),
            ("date_range", ClimateValidationService.validate_date_range(
                start_date, end_date, allow_future
            )),
            ("variables", ClimateValidationService.validate_variables(variables)),
            ("source", ClimateValidationService.validate_source(source)),
        ]
        
        errors = {}
        details = {}
        
        for name, (valid, detail) in validations:
            if not valid:
                errors[name] = detail
            else:
                details[name] = detail
        
        if errors:
            logger.warning(f"Validation errors: {errors}")
            return False, {"errors": errors, "details": details}
        
        logger.info(f"All validations passed for ({lat}, {lon})")
        return True, {"all_valid": True, "details": details}


# Instância singleton
climate_validation_service = ClimateValidationService()
