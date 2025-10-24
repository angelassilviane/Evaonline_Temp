"""
Rotas de health check e informações da API.
Merged de: about_routes.py + system_routes.py

Responsabilidade: Health, metrics, info (consolidado)
"""

from typing import Dict, List, Union

from fastapi import APIRouter

router = APIRouter(tags=["System"])


# ====== HEALTH ENDPOINTS ======


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Verificação de saúde da API.

    Returns:
        Dict com status da API
    """
    return {
        "status": "ok",
        "service": "evaonline-api",
        "version": "1.0.0"
    }


# ====== INFO ENDPOINTS ======


@router.get("/api/internal/about/info")
async def get_about_info() -> Dict[str, Union[Dict, List]]:
    """
    Informações sobre o software, desenvolvedores e parceiros.

    Returns:
        Dict com software info, desenvolvedores, parceiros
    """
    return {
        "software": {
            "name": "EVAonline",
            "version": "1.0.0",
            "description": "Calculadora online de Evapotranspiração",
            "repository": (
                "https://github.com/angelassilviane/Evaonline_Temp"
            ),
            "license": "MIT"
        },
        "developers": {
            "main": (
                "Angela Cunha Soares "
                "<angelacunhasoares@gmail.com>"
            ),
            "supervisor": (
                "Prof. Dr. Fábio Ricardo Marin "
                "<fabio.marin@usp.br>"
            )
        },
        "partners": [
            {
                "name": "ESALQ/USP",
                "url": "https://www.esalq.usp.br/",
                "logo": "logo_esalq.png"
            },
        ]
    }
