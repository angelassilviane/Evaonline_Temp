# 🚀 PLANO EXECUTÁVEL - FASE 0.2 ROUTES REFACTOR (OPÇÃO B)

**Data**: 22 de Outubro de 2025  
**Opção**: B - Refatoração Moderada  
**Tempo Total**: ~2 horas  
**Objetivo**: Organizar rotas, melhorar qualidade, otimizar performance  

---

## 📋 CRONOGRAMA

```
16:45-17:00 (15 min) - PASSO 1: Criar estrutura schemas/
17:00-17:20 (20 min) - PASSO 2: Criar estrutura services/
17:20-17:50 (30 min) - PASSO 3: Split climate routes (3 arquivos)
17:50-18:35 (45 min) - PASSO 4: Split location routes (3 arquivos)
18:35-18:45 (10 min) - PASSO 5: Merge health endpoints
18:45-19:05 (20 min) - PASSO 6: Fix críticos + imports
19:05-19:35 (30 min) - PASSO 7: Performance (PostGIS + cache)
19:35-19:50 (15 min) - PASSO 8: Testes + validação
19:50-20:00 (10 min) - PASSO 9: Git commit final

TOTAL: 205 minutos ≈ 3h25min (com margem para bugs)
```

---

## 🎯 PASSO 1: Criar Pasta `schemas/` (15 min)

### 1.1 Criar estrutura

```bash
mkdir backend/api/schemas
touch backend/api/schemas/__init__.py
touch backend/api/schemas/climate_schemas.py
touch backend/api/schemas/elevation_schemas.py
touch backend/api/schemas/location_schemas.py
```

### 1.2 Extrair modelos de `climate_sources_routes.py`

**Arquivo**: `backend/api/schemas/climate_schemas.py`

```python
"""
Modelos Pydantic para rotas de fontes climáticas.
Extraído de: backend/api/routes/climate_sources_routes.py
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AvailableSourcesResponse(BaseModel):
    """Resposta com fontes disponíveis."""
    location: Dict[str, float] = Field(
        ..., description="Coordenadas da localização"
    )
    available_sources: List[Dict] = Field(
        ..., description="Lista de fontes disponíveis"
    )
    default_mode: str = Field(
        default="fusion", description="Modo padrão de operação"
    )
    fusion_sources: List[str] = Field(
        ..., description="IDs das fontes para fusão"
    )


class ValidationResponse(BaseModel):
    """Resposta de validação de período."""
    valid: bool = Field(..., description="Se o período é válido")
    message: str | None = Field(
        default=None, description="Mensagem de erro (se inválido)"
    )


class FusionWeightsResponse(BaseModel):
    """Resposta com pesos de fusão."""
    sources: List[str] = Field(..., description="IDs das fontes")
    weights: Dict[str, float] = Field(..., description="Pesos normalizados")
    total: float = Field(default=1.0, description="Soma dos pesos")
```

### 1.3 Criar schemas vazios para elevation e location

**Arquivo**: `backend/api/schemas/elevation_schemas.py`

```python
"""Modelos Pydantic para rotas de elevação."""

from pydantic import BaseModel, Field


class ElevationResponse(BaseModel):
    """Resposta com dados de elevação."""
    elevation: float = Field(..., description="Elevação em metros")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    source: str = Field(..., description="Fonte (database/api)")
```

**Arquivo**: `backend/api/schemas/location_schemas.py`

```python
"""Modelos Pydantic para rotas de localizações."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class LocationResponse(BaseModel):
    """Resposta com dados de localização."""
    id: int = Field(..., description="ID da localização")
    name: str = Field(..., description="Nome da localização")
    country: str = Field(..., description="País")
    country_code: str = Field(..., description="Código do país")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    elevation_m: float = Field(..., description="Elevação em metros")


class LocationDetailResponse(LocationResponse):
    """Detalhes completos de uma localização."""
    pass


class NearestLocationResponse(BaseModel):
    """Resposta com localização mais próxima."""
    query: Dict[str, float] = Field(..., description="Coordenadas da busca")
    nearest: LocationResponse = Field(..., description="Localização mais próxima")
    distance_km: float = Field(..., description="Distância em km")
```

### 1.4 Atualizar `backend/api/schemas/__init__.py`

```python
"""
Schemas (modelos Pydantic) para API.
"""

from backend.api.schemas.climate_schemas import (
    AvailableSourcesResponse,
    ValidationResponse,
    FusionWeightsResponse,
)
from backend.api.schemas.elevation_schemas import ElevationResponse
from backend.api.schemas.location_schemas import (
    LocationResponse,
    LocationDetailResponse,
    NearestLocationResponse,
)

__all__ = [
    "AvailableSourcesResponse",
    "ValidationResponse",
    "FusionWeightsResponse",
    "ElevationResponse",
    "LocationResponse",
    "LocationDetailResponse",
    "NearestLocationResponse",
]
```

### ✅ Resultado PASSO 1

```
backend/api/schemas/
├── __init__.py (14L)
├── climate_schemas.py (40L)
├── elevation_schemas.py (10L)
└── location_schemas.py (35L)
```

---

## 🎯 PASSO 2: Criar Pasta `services/` (20 min)

### 2.1 Criar estrutura

```bash
touch backend/api/services/climate_validation.py
touch backend/api/services/climate_fusion.py
touch backend/api/services/license_checker.py
```

### 2.2 Extrair validação de período

**Arquivo**: `backend/api/services/climate_validation.py`

```python
"""
Serviço de validação para dados climáticos.
Extraído de: backend/api/routes/eto_routes.py
"""

from datetime import datetime, timedelta
from typing import Tuple


class ClimateValidationService:
    """Validação centralizada para dados climáticos."""
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str | None]:
        """Valida latitude e longitude."""
        if not (-90 <= lat <= 90):
            return False, "Latitude deve estar entre -90 e 90 graus."
        if not (-180 <= lon <= 180):
            return False, "Longitude deve estar entre -180 e 180 graus."
        return True, None
    
    @staticmethod
    def validate_period(
        start_date: str,
        end_date: str,
        min_days: int = 7,
        max_days: int = 15
    ) -> Tuple[bool, str | None]:
        """
        Valida período de datas.
        
        Args:
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            min_days: Mínimo de dias (default: 7)
            max_days: Máximo de dias (default: 15)
        
        Returns:
            Tuple[bool, str]: (válido, mensagem de erro se inválido)
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            hoje = datetime.now()
        except ValueError:
            return False, "Formato de data inválido. Use YYYY-MM-DD."
        
        # Verificar limite de 1 ano para trás e 1 dia para frente
        um_ano_atras = hoje - timedelta(days=365)
        amanha = hoje + timedelta(days=1)
        
        if start < um_ano_atras:
            return False, "Data inicial não pode ser anterior a 1 ano atrás."
        if end > amanha:
            return False, "Data final não pode ser posterior a amanhã."
        if end < start:
            return False, "Data final deve ser posterior à data inicial."
        
        period_days = (end - start).days + 1
        if period_days < min_days or period_days > max_days:
            return False, f"Período deve ser entre {min_days} e {max_days} dias."
        
        return True, None
    
    @staticmethod
    def validate_database(database: str, valid_dbs: list = None) -> Tuple[bool, str | None]:
        """Valida fonte de dados."""
        if valid_dbs is None:
            valid_dbs = ["nasa_power", "openmeteo_archive", "met_norway", "nws"]
        
        if database not in valid_dbs:
            return False, f"Base de dados inválida. Use: {valid_dbs}"
        return True, None
```

### 2.3 Extrair cálculo de pesos

**Arquivo**: `backend/api/services/climate_fusion.py`

```python
"""
Serviço de fusão de dados climáticos.
Extraído de: backend/api/routes/climate_sources_routes.py
"""

from typing import Dict, List


class ClimateFusionService:
    """Serviço para cálculo de pesos de fusão."""
    
    @staticmethod
    def get_fusion_weights(
        sources: List[str],
        location: tuple
    ) -> Dict[str, float]:
        """
        Calcula pesos normalizados para fusão de dados.
        
        Args:
            sources: Lista de IDs de fontes
            location: Tuple (lat, lon) da localização
        
        Returns:
            Dict com pesos normalizados por fonte
        
        Raises:
            ValueError: Se licença não permite fusão
        """
        # Prioridades padrão
        priorities = {
            "nasa_power": 0.3,      # Confiável, global
            "openmeteo_archive": 0.25,  # Bom historical
            "met_norway": 0.25,     # Europa excelente
            "nws": 0.2,             # USA apenas
        }
        
        # Calcular pesos por fonte
        weights = {}
        total_priority = 0
        
        for source in sources:
            if source not in priorities:
                raise ValueError(f"Fonte desconhecida: {source}")
            
            weights[source] = priorities[source]
            total_priority += priorities[source]
        
        # Normalizar para somar 1.0
        normalized = {}
        for source, weight in weights.items():
            normalized[source] = round(weight / total_priority, 4)
        
        return normalized
```

### 2.4 Extrair proteção de licença

**Arquivo**: `backend/api/services/license_checker.py`

```python
"""
Serviço para verificação de licenças de dados.
Extraído de: backend/api/routes/climate_sources_routes.py
"""

from typing import List


class LicenseChecker:
    """Verificador de licenças para dados climáticos."""
    
    # Licenças por fonte
    LICENSES = {
        "nasa_power": {
            "name": "Domínio Público",
            "code": "PUBLIC_DOMAIN",
            "allows_fusion": True,
            "allows_download": True,
            "allows_commercial": True,
        },
        "openmeteo_archive": {
            "name": "CC-BY-NC 4.0",
            "code": "CC_BY_NC_4",
            "allows_fusion": False,  # ❌ NÃO permite fusão
            "allows_download": False,  # ❌ NÃO permite download
            "allows_commercial": False,
        },
        "met_norway": {
            "name": "CC-BY 4.0",
            "code": "CC_BY_4",
            "allows_fusion": True,
            "allows_download": True,
            "allows_commercial": True,
        },
        "nws": {
            "name": "Domínio Público",
            "code": "PUBLIC_DOMAIN",
            "allows_fusion": True,
            "allows_download": True,
            "allows_commercial": True,
        },
    }
    
    @staticmethod
    def check_fusion_allowed(sources: List[str]) -> None:
        """
        Verifica se todas as fontes permitem fusão.
        
        Raises:
            ValueError: Se alguma fonte não permite fusão
        """
        for source in sources:
            license_info = LicenseChecker.LICENSES.get(source)
            if not license_info:
                raise ValueError(f"Fonte desconhecida: {source}")
            
            if not license_info["allows_fusion"]:
                raise ValueError(
                    f"Fonte '{source}' ({license_info['name']}) "
                    f"NÃO permite fusão de dados. "
                    f"Usar como fonte única ou escolher outra."
                )
    
    @staticmethod
    def check_download_allowed(sources: List[str]) -> None:
        """
        Verifica se todas as fontes permitem download.
        
        Raises:
            ValueError: Se alguma fonte não permite download
        """
        for source in sources:
            license_info = LicenseChecker.LICENSES.get(source)
            if not license_info:
                raise ValueError(f"Fonte desconhecida: {source}")
            
            if not license_info["allows_download"]:
                raise ValueError(
                    f"Fonte '{source}' ({license_info['name']}) "
                    f"NÃO permite download. "
                    f"Dados disponíveis apenas para visualização."
                )
    
    @staticmethod
    def get_license_info(source: str) -> dict:
        """Retorna informações de licença de uma fonte."""
        return LicenseChecker.LICENSES.get(
            source,
            {"error": f"Fonte '{source}' desconhecida"}
        )
```

### ✅ Resultado PASSO 2

```
backend/api/services/
├── climate_validation.py (70L)
├── climate_fusion.py (60L)
└── license_checker.py (100L)
```

---

## 🎯 PASSO 3: Split Climate Routes (30 min)

### 3.1 Criar `backend/api/routes/climate_sources.py`

```python
"""
Rotas para metadata de fontes climáticas.
Extraído e refatorado de: climate_sources_routes.py
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas.climate_schemas import AvailableSourcesResponse
from backend.api.services.climate_source_manager import ClimateSourceManager

router = APIRouter(
    prefix="/api/v1/climate/sources",
    tags=["Climate Sources"]
)


@router.get(
    "/available",
    response_model=AvailableSourcesResponse,
    summary="Lista fontes disponíveis para localização",
)
async def get_available_sources(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    long: float = Query(..., ge=-180, le=180, description="Longitude")
) -> Dict:
    """Lista fontes disponíveis para uma localização."""
    manager = ClimateSourceManager()
    sources = manager.get_available_sources(lat, long)
    realtime_sources = [s["id"] for s in sources if s.get("realtime", False)]
    
    return {
        "location": {"lat": lat, "long": long},
        "available_sources": sources,
        "default_mode": "fusion",
        "fusion_sources": realtime_sources
    }


@router.get(
    "/validation-info",
    summary="Informações sobre validação científica",
)
async def get_validation_info() -> Dict:
    """Retorna informações sobre datasets de validação."""
    manager = ClimateSourceManager()
    return manager.get_validation_info()


@router.get(
    "/info/{source_id}",
    summary="Detalhes de uma fonte específica",
)
async def get_source_info(source_id: str) -> Dict[str, Any]:
    """Retorna informações detalhadas de uma fonte."""
    manager = ClimateSourceManager()
    
    if source_id not in manager.SOURCES_CONFIG:
        raise HTTPException(
            status_code=404,
            detail=f"Fonte '{source_id}' não encontrada"
        )
    
    return manager.SOURCES_CONFIG[source_id]
```

### 3.2 Criar `backend/api/routes/climate_validation.py`

```python
"""
Rotas para validação de dados climáticos.
Extraído e refatorado de: climate_sources_routes.py
"""

from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Query

from backend.api.schemas.climate_schemas import ValidationResponse
from backend.api.services.climate_validation import ClimateValidationService

router = APIRouter(
    prefix="/api/v1/climate",
    tags=["Climate Validation"]
)


@router.get(
    "/validate-period",
    response_model=ValidationResponse,
    summary="Valida período de datas",
)
async def validate_period(
    start_date: str = Query(..., description="Data inicial (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Data final (YYYY-MM-DD)")
) -> Dict:
    """Valida período de datas."""
    valid, message = ClimateValidationService.validate_period(
        start_date, end_date
    )
    
    return {
        "valid": valid,
        "message": message if not valid else "Período válido"
    }
```

### 3.3 Criar `backend/api/routes/climate_download.py`

```python
"""
Rotas para download de dados climáticos.
Extraído e refatorado de: climate_sources_routes.py
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException, Query

from backend.api.services.climate_source_manager import ClimateSourceManager
from backend.api.services.license_checker import LicenseChecker

router = APIRouter(
    prefix="/api/v1/climate",
    tags=["Climate Download"]
)


@router.post(
    "/download",
    summary="Baixar dados climáticos processados",
)
async def download_climate_data(
    sources: List[str] = Query(..., description="IDs das fontes"),
    format: str = Query(
        default="csv",
        regex="^(csv|json|netcdf)$",
        description="Formato de saída"
    )
) -> Dict:
    """
    Prepara download de dados climáticos.
    
    Validações:
    - Open-Meteo é BLOQUEADO (CC-BY-NC 4.0)
    """
    # 🔒 Verificar licenças
    try:
        LicenseChecker.check_download_allowed(sources)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    # Validar fontes existem
    manager = ClimateSourceManager()
    invalid = [s for s in sources if s not in manager.SOURCES_CONFIG]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Fontes inválidas: {invalid}"
        )
    
    # TODO: Implementar geração real de arquivo
    return {
        "status": "ready",
        "sources": sources,
        "format": format,
        "download_url": "/api/v1/climate/download/file?id=placeholder",
        "expires_in": 3600,
    }
```

### ✅ Resultado PASSO 3

```
backend/api/routes/
├── climate_sources.py (60L)   ← NEW
├── climate_validation.py (40L) ← NEW
├── climate_download.py (70L)   ← NEW
└── climate_sources_routes.py (280L) ← DELETE DEPOIS
```

---

## 🎯 PASSO 4: Split Location Routes (45 min)

Similar ao PASSO 3, split `world_locations.py` em 3 arquivos...

*[Devido ao tamanho, vou criar documento separado para PASSO 4-9]*

---

## 📋 Próximos Passos

Para continuar este plano detalhado:

**Arquivo separado será criado**: `PLANO_FASE_0.2_PASSOS_4_A_9.md`

Com:
- PASSO 4: Split location routes (45 min)
- PASSO 5: Merge health endpoints (10 min)
- PASSO 6: Fix críticos + imports (20 min)
- PASSO 7: Performance PostGIS (30 min)
- PASSO 8: Testes (15 min)
- PASSO 9: Git commit (10 min)

---

**Status**: PASSO 1-3 documentado ✅

Próxima mensagem: confirmar que quer continuar com PASSOS 4-9

**Tempo acumulado até aqui**: 65 min de 120 min

Pronto para continuar? 🚀
