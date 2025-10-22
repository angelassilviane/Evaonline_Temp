"""
Configuração das rotas da API.
Organiza todas as rotas da aplicação por funcionalidade.
"""
from fastapi import APIRouter

from backend.api.routes.about_routes import about_router
from backend.api.routes.climate_download import router as climate_download_router

# ✅ NOVAS ROTAS (PASSO 3 - Climate split)
from backend.api.routes.climate_sources import router as climate_sources_router
from backend.api.routes.climate_validation import router as climate_validation_router
from backend.api.routes.eto_routes import eto_router
from backend.api.routes.stats import router as stats_router
from backend.api.routes.system_routes import router as system_router
from backend.api.routes.world_locations import router as world_locations_router

# Criar router principal
api_router = APIRouter()

# Incluir rotas específicas
api_router.include_router(eto_router)
api_router.include_router(about_router)
api_router.include_router(stats_router)
api_router.include_router(system_router)
api_router.include_router(world_locations_router)

# ✅ Registrar novas rotas de clima
api_router.include_router(climate_sources_router)
api_router.include_router(climate_validation_router)
api_router.include_router(climate_download_router)

