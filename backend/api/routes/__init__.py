"""
Configuração das rotas da API.
Organiza todas as rotas da aplicação por funcionalidade.
"""
from fastapi import APIRouter

from backend.api.routes.about_routes import about_router
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
