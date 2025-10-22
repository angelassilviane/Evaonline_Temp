"""
Serviço de fusão de dados climáticos de múltiplas fontes.
Consolida pesos e cálculos de média ponderada.

Benefício: Permite usar dados de múltiplas fontes com confiabilidade.
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple

from loguru import logger


class ClimateFusionService:
    """Fusão inteligente de dados climáticos de múltiplas fontes."""
    
    # Pesos padrão por fonte (confiabilidade)
    DEFAULT_WEIGHTS = {
        "openmeteo": 0.35,      # Ótima cobertura global
        "nasa_power": 0.30,     # Satélite, boa precisão
        "met_norway": 0.20,     # Regional, moderado
        "nws": 0.15,            # Muito regional
    }
    
    # Variáveis que permitem fusão
    FUSIBLE_VARIABLES = {
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "solar_radiation",
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Inicializa serviço com pesos customizáveis.
        
        Args:
            weights: Dicionário {fonte: peso}
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()
        logger.info(f"ClimateFusionService initialized with weights: {self.weights}")
    
    def _validate_weights(self) -> None:
        """Valida que os pesos são normalizados."""
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):  # Permitir pequeno erro numérico
            logger.warning(
                f"Weights not normalized (sum={total}). "
                f"Will normalize automatically."
            )
    
    def normalize_weights(self) -> Dict[str, float]:
        """Retorna pesos normalizados para soma = 1."""
        total = sum(self.weights.values())
        return {source: w / total for source, w in self.weights.items()}
    
    def fuse_multiple_sources(
        self,
        data_by_source: Dict[str, List[Dict[str, Any]]],
        variable: str,
        date_field: str = "date"
    ) -> List[Dict[str, Any]]:
        """
        Funde dados de múltiplas fontes para uma variável.
        
        Args:
            data_by_source: {fonte: [dados]}
            variable: Variável a fundir (ex: temperature_2m)
            date_field: Campo que contém a data
        
        Returns:
            Lista de dados fundidos: [{"date": ..., "value": ..., "sources": [...]}]
        """
        if variable not in self.FUSIBLE_VARIABLES:
            logger.warning(
                f"Variable {variable} not fusible. "
                f"Available: {self.FUSIBLE_VARIABLES}"
            )
            # Retorna dados da primeira fonte disponível
            for source, data in data_by_source.items():
                if data and variable in data[0]:
                    logger.info(f"Using {source} data for {variable}")
                    return data
            return []
        
        # Construir índice de dados por data
        data_by_date = {}
        
        for source, data_list in data_by_source.items():
            if not data_list:
                continue
            
            weight = self.weights.get(source, 0)
            if weight == 0:
                logger.warning(f"Source {source} has zero weight, skipping")
                continue
            
            for record in data_list:
                date = record.get(date_field)
                if date not in data_by_date:
                    data_by_date[date] = []
                
                value = record.get(variable)
                if value is not None:
                    data_by_date[date].append({
                        "source": source,
                        "value": value,
                        "weight": weight
                    })
        
        # Calcular média ponderada por data
        normalized_weights = self.normalize_weights()
        fused_data = []
        
        for date in sorted(data_by_date.keys()):
            sources_data = data_by_date[date]
            
            if not sources_data:
                continue
            
            # Calcular média ponderada
            weighted_sum = 0
            total_weight = 0
            sources_used = []
            
            for source_data in sources_data:
                source = source_data["source"]
                value = source_data["value"]
                weight = normalized_weights.get(source, 0)
                
                weighted_sum += value * weight
                total_weight += weight
                sources_used.append(source)
            
            if total_weight > 0:
                fused_value = weighted_sum / total_weight
                
                fused_data.append({
                    date_field: date,
                    variable: round(fused_value, 2),
                    f"{variable}_sources": sources_used,
                    f"{variable}_confidence": round(total_weight * 100),
                })
        
        logger.info(
            f"Fused {len(fused_data)} records for {variable} "
            f"from {len(data_by_source)} sources"
        )
        
        return fused_data
    
    def get_best_source(
        self,
        available_sources: List[str]
    ) -> str:
        """
        Retorna melhor fonte entre as disponíveis.
        
        Args:
            available_sources: Lista de fontes disponíveis
        
        Returns:
            Nome da fonte com maior peso
        """
        best_source = None
        best_weight = -1
        
        for source in available_sources:
            weight = self.weights.get(source, 0)
            if weight > best_weight:
                best_weight = weight
                best_source = source
        
        logger.debug(f"Best available source: {best_source}")
        return best_source
    
    def calculate_quality_score(
        self,
        sources_count: int,
        total_records: int,
        coverage_percent: float
    ) -> Dict[str, Any]:
        """
        Calcula score de qualidade dos dados fundidos.
        
        Args:
            sources_count: Número de fontes usadas
            total_records: Total de registros
            coverage_percent: Percentual de cobertura (0-100)
        
        Returns:
            Score de qualidade: {"score": 0-100, "level": "poor"|"fair"|"good"}
        """
        score = 0
        
        # Pontos por número de fontes
        score += min(sources_count * 20, 40)  # Max 40 pontos
        
        # Pontos por cobertura
        score += coverage_percent * 0.6  # Max 60 pontos
        
        level = "poor" if score < 40 else ("fair" if score < 70 else "good")
        
        logger.debug(f"Quality score: {score} ({level})")
        
        return {
            "score": round(score),
            "level": level,
            "sources_count": sources_count,
            "coverage_percent": round(coverage_percent, 1),
        }


# Instância singleton
climate_fusion_service = ClimateFusionService()
