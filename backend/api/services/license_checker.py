"""
Serviço de verificação de licenças para acesso a dados climáticos.
Garante que dados/APIs estão licenciados para uso.

Benefício: Previne uso não autorizado de dados, rastreia licenças.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from loguru import logger


class LicenseStatus(str, Enum):
    """Status possível de uma licença."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    UNKNOWN = "unknown"


class License:
    """Representa uma licença de dados."""
    
    def __init__(
        self,
        provider: str,
        license_id: str,
        status: LicenseStatus = LicenseStatus.ACTIVE,
        expires_at: Optional[datetime] = None,
        terms: Optional[Dict] = None,
    ):
        """
        Inicializa licença.
        
        Args:
            provider: Provedor de dados (openmeteo, nasa_power, etc)
            license_id: ID único da licença
            status: Status atual
            expires_at: Data de expiração
            terms: Termos de uso como dict
        """
        self.provider = provider
        self.license_id = license_id
        self.status = status
        self.expires_at = expires_at
        self.terms = terms or {}
        self.created_at = datetime.now()
    
    def is_valid(self) -> bool:
        """Verifica se licença é válida e ativa."""
        if self.status != LicenseStatus.ACTIVE:
            return False
        
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        
        return True
    
    def days_until_expiry(self) -> Optional[int]:
        """Dias até expiração (None se não expira)."""
        if not self.expires_at:
            return None
        
        days = (self.expires_at - datetime.now()).days
        return max(0, days)
    
    def to_dict(self) -> Dict:
        """Converte licença para dict."""
        return {
            "provider": self.provider,
            "license_id": self.license_id,
            "status": self.status.value,
            "valid": self.is_valid(),
            "expires_at": self.expires_at.isoformat()
            if self.expires_at else None,
            "days_until_expiry": self.days_until_expiry(),
            "terms": self.terms,
        }


class LicenseCheckerService:
    """Serviço de verificação centralizado de licenças."""
    
    def __init__(self):
        """Inicializa serviço com licenças padrão."""
        self.licenses: Dict[str, License] = {}
        self._initialize_default_licenses()
    
    def _initialize_default_licenses(self) -> None:
        """Inicializa licenças padrão (open source)."""
        # OpenMeteo - open source, sem restrições
        self.add_license(
            License(
                provider="openmeteo",
                license_id="open-meteo-free",
                status=LicenseStatus.ACTIVE,
                expires_at=None,  # Sem expiração
                terms={
                    "attribution_required": True,
                    "commercial_use": True,
                    "max_requests_per_day": 10000,
                }
            )
        )
        
        # NASA POWER - público, sem restrições
        self.add_license(
            License(
                provider="nasa_power",
                license_id="nasa-power-public",
                status=LicenseStatus.ACTIVE,
                expires_at=None,
                terms={
                    "attribution_required": True,
                    "commercial_use": True,
                    "max_requests_per_day": 5000,
                }
            )
        )
        
        logger.info("Initialized default licenses for openmeteo, nasa_power")
    
    def add_license(self, license: License) -> None:
        """Adiciona nova licença ao serviço."""
        key = f"{license.provider}:{license.license_id}"
        self.licenses[key] = license
        logger.info(f"Added license: {key}")
    
    def check_license(
        self,
        provider: str,
        license_id: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Verifica se licença é válida.
        
        Args:
            provider: Nome do provedor
            license_id: ID da licença (se None, usa padrão)
        
        Returns:
            Tupla (válido, detalhes)
        """
        # Se não especifica license_id, busca qualquer licença ativa do provider
        if license_id is None:
            for key, lic in self.licenses.items():
                if lic.provider == provider and lic.is_valid():
                    return True, lic.to_dict()
            
            logger.warning(f"No valid license found for {provider}")
            return False, {
                "error": f"No valid license for {provider}",
                "provider": provider,
            }
        
        # Busca licença específica
        key = f"{provider}:{license_id}"
        if key not in self.licenses:
            logger.warning(f"License not found: {key}")
            return False, {
                "error": f"License not found",
                "key": key,
            }
        
        license = self.licenses[key]
        
        if not license.is_valid():
            logger.warning(f"License invalid: {key} (status: {license.status})")
            return False, {
                "error": f"License invalid",
                **license.to_dict(),
            }
        
        logger.info(f"License valid: {key}")
        return True, license.to_dict()
    
    def check_terms(
        self,
        provider: str,
        usage_type: str = "research"
    ) -> Tuple[bool, Dict]:
        """
        Verifica se uso está permitido pelos termos da licença.
        
        Args:
            provider: Provedor
            usage_type: Tipo de uso (research, commercial, educational)
        
        Returns:
            Tupla (permitido, detalhes)
        """
        valid, lic_data = self.check_license(provider)
        
        if not valid:
            return False, lic_data
        
        terms = lic_data.get("terms", {})
        
        if usage_type == "commercial" and not terms.get("commercial_use"):
            logger.warning(
                f"Commercial use not permitted for {provider}"
            )
            return False, {
                "error": "Commercial use not permitted",
                "provider": provider,
                "terms": terms,
            }
        
        if terms.get("attribution_required"):
            logger.info(f"Attribution required for {provider}")
        
        logger.info(f"Usage type '{usage_type}' permitted for {provider}")
        return True, {"permitted": True, "terms": terms}
    
    def get_all_licenses(self) -> Dict[str, Dict]:
        """Retorna todas as licenças registradas."""
        return {
            key: lic.to_dict()
            for key, lic in self.licenses.items()
        }
    
    def get_provider_licenses(self, provider: str) -> List[Dict]:
        """Retorna todas as licenças de um provedor."""
        return [
            lic.to_dict()
            for lic in self.licenses.values()
            if lic.provider == provider
        ]
    
    def get_status_report(self) -> Dict:
        """Retorna relatório de status de todas as licenças."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_licenses": len(self.licenses),
            "by_status": {},
            "expiring_soon": [],
        }
        
        for key, lic in self.licenses.items():
            status = lic.status.value
            if status not in report["by_status"]:
                report["by_status"][status] = []
            report["by_status"][status].append(key)
            
            # Avisar sobre licenças expirando em 30 dias
            days = lic.days_until_expiry()
            if days is not None and 0 <= days <= 30:
                report["expiring_soon"].append({
                    "license": key,
                    "expires_at": lic.expires_at.isoformat(),
                    "days": days,
                })
        
        logger.info(f"License report: {len(self.licenses)} licenses")
        return report


# Instância singleton
license_checker_service = LicenseCheckerService()
