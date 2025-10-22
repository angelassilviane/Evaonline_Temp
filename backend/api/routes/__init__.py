"""
Configuração das rotas da API.
Organiza todas as rotas da aplicação por funcionalidade.
"""
from fastapi import APIRouter

from backend.api.routes.about_routes import about_router
from backend.api.routes.cache_routes import router as cache_router
from backend.api.routes.climate_download import router as climate_download_router
from backend.api.routes.climate_sources import router as climate_sources_router
from backend.api.routes.climate_validation import router as climate_validation_router
from backend.api.routes.eto_routes import eto_router
from backend.api.routes.favorites_routes import router as favorites_router
from backend.api.routes.health import router as health_router
from backend.api.routes.locations_detail import router as locations_detail_router
from backend.api.routes.locations_list import router as locations_list_router
from backend.api.routes.locations_search import router as locations_search_router
from backend.api.routes.stats import router as stats_router
from backend.api.routes.system_routes import router as system_router
from backend.api.routes.world_locations import router as world_locations_router

# Criar router principal
api_router = APIRouter()

# ✅ Incluir rotas específicas (em ordem lógica)
api_router.include_router(health_router)
api_router.include_router(eto_router)
api_router.include_router(about_router)
api_router.include_router(stats_router)
api_router.include_router(system_router)

# ✅ Incluir rotas de clima (PASSO 3)
api_router.include_router(climate_sources_router)
api_router.include_router(climate_validation_router)
api_router.include_router(climate_download_router)

# ✅ Incluir rotas de localizações (PASSO 4)
api_router.include_router(locations_list_router)
api_router.include_router(locations_detail_router)
api_router.include_router(locations_search_router)

# ✅ Incluir rotas de cache + favoritos (PASSO 7-10)
api_router.include_router(cache_router)
api_router.include_router(favorites_router)

# ⚠️ MANTER (será deletado em PASSO 5.1 após validação)
api_router.include_router(world_locations_router)


