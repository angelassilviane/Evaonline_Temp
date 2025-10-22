"""
Rotas para download de dados climáticos com proteção de licença.
Extraído de: backend/api/routes/climate_sources_routes.py (linhas 150-280)

Responsabilidade: POST /download (com bloqueio CC-BY-NC)
"""

from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from backend.api.services.climate_source_manager import ClimateSourceManager
from backend.api.services.license_checker import license_checker_service

router = APIRouter(
    prefix="/api/v1/climate",
    tags=["Climate Download"]
)


@router.post(
    "/sources/download",
    summary="Baixar dados climáticos processados",
    description="""
    Endpoint para download de dados climáticos.
    
    ⚠️ RESTRIÇÃO DE LICENÇA:
    - Open-Meteo (CC-BY-NC 4.0) NÃO permite download
    - Apenas fontes com licenças comerciais permitidas
    - Atribuição requerida para todas as fontes
    """
)
async def download_climate_data(
    sources: List[str] = Query(
        ..., description="IDs das fontes"
    ),
    format: str = Query(
        default="csv",
        regex="^(csv|json|netcdf)$",
        description="Formato de saída (csv, json, netcdf)"
    )
) -> Dict:
    """
    Prepara download de dados climáticos com validação de licença.
    
    🔒 PROTEÇÃO CC-BY-NC 4.0:
    Open-Meteo não permite download de dados brutos ou processados.
    Redistribuição e uso comercial são proibidos.
    
    Args:
        sources: Lista de IDs de fontes
        format: Formato de saída (csv, json, netcdf)
    
    Returns:
        Dict com URL de download e atribuições
    
    Raises:
        HTTPException 403: Se Open-Meteo incluído (CC-BY-NC restrição)
        HTTPException 400: Se formato inválido
        HTTPException 404: Se fonte não existir
    """
    try:
        logger.info(f"Download request: {sources}, format={format}")
        
        # 🔒 PROTEÇÃO CC-BY-NC: Bloqueia Open-Meteo
        if "openmeteo" in sources:
            logger.warning(
                "Download blocked: Open-Meteo CC-BY-NC 4.0 restriction"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "download_not_allowed",
                    "message": (
                        "Open-Meteo não permite download de dados. "
                        "Licença CC-BY-NC 4.0 restringe redistribuição "
                        "e uso comercial. Dados disponíveis apenas para "
                        "visualização na interface."
                    ),
                    "license": "CC-BY-NC 4.0",
                    "license_url": (
                        "https://creativecommons.org/licenses/"
                        "by-nc/4.0/"
                    ),
                    "allowed_uses": [
                        "Visualização na interface web",
                        "Pesquisa acadêmica (sem redistribuição)",
                        "Publicações científicas (com citação)",
                    ],
                    "prohibited_uses": [
                        "Download de dados brutos ou processados",
                        "Fusão com outras fontes (data fusion)",
                        "Redistribuição ou venda de dados",
                        "Integração em produtos comerciais",
                    ],
                    "citation": (
                        "Weather data by Open-Meteo.com "
                        "(https://open-meteo.com) - CC-BY-NC 4.0"
                    ),
                    "alternative_sources": [
                        "nasa_power (Domínio Público)",
                        "met_norway (CC-BY 4.0 - comercial OK)",
                        "nws_usa (Domínio Público)",
                    ]
                }
            )
        
        # Validar fontes existem
        manager = ClimateSourceManager()
        invalid = [
            s for s in sources
            if s not in manager.SOURCES_CONFIG
        ]
        if invalid:
            logger.error(f"Invalid sources: {invalid}")
            raise HTTPException(
                status_code=404,
                detail=f"Unknown sources: {invalid}"
            )
        
        # Validar licenças das fontes
        for source_id in sources:
            valid, lic_data = license_checker_service.check_license(
                source_id
            )
            if not valid:
                logger.warning(
                    f"License check failed for {source_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"License invalid for {source_id}: {lic_data}"
                )
        
        # Colectar atribuições requeridas
        attribution_required = []
        for s in sources:
            config = manager.SOURCES_CONFIG[s]
            if config.get("attribution"):
                attribution_required.append({
                    "source": s,
                    "attribution": config["attribution"],
                    "license": config.get("license", ""),
                    "license_url": config.get("license_url", ""),
                })
        
        logger.info(
            f"Download ready: {sources}, format={format}, "
            f"attributions={len(attribution_required)}"
        )
        
        # TODO: Implementar geração de arquivo de download
        # Por enquanto, retorna URL placeholder
        return {
            "status": "ready",
            "sources": sources,
            "format": format,
            "download_url": (
                "/api/v1/climate/download/file?id=placeholder"
            ),
            "expires_in": 3600,  # 1 hora
            "attribution_required": attribution_required,
            "message": (
                "By downloading, you agree to respect the licenses "
                "of all data sources."
            ),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing download: {e}")
        raise HTTPException(status_code=500, detail=str(e))
