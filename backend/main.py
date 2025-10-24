import logging

from asgiref.wsgi import WsgiToAsgi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from backend.api.routes import api_router
from backend.api.websocket.websocket_service import router as websocket_router
from config.settings import get_settings
from frontend.app import create_dash_app

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar configurações
settings = get_settings()

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Adicionar middleware Prometheus
    from backend.api.middleware.prometheus import PrometheusMiddleware
    app.add_middleware(PrometheusMiddleware)

    # Montar rotas
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(websocket_router)

    # Configurar métricas Prometheus
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app


def mount_dash(app: FastAPI) -> FastAPI:
    dash_app = create_dash_app()
    # Converter WSGI app para ASGI app
    asgi_app = WsgiToAsgi(dash_app.server)
    
    # IMPORTANTE: Criar sub-application para evitar conflito de rotas
    # Solução: Montar Dash apenas em paths que NÃO começam com /api ou /metrics
    from fastapi import Request, Response
    from starlette.types import Receive, Scope, Send
    
    class DashApp:
        """Wrapper que só encaminha para Dash se não for rota da API."""
        def __init__(self, asgi_app):
            self.asgi_app = asgi_app
        
        async def __call__(self, scope: Scope, receive: Receive, send: Send):
            path = scope.get("path", "")
            
            # Não interceptar rotas da API, WebSocket, ou métricas
            if (path.startswith("/api/") or 
                path.startswith("/metrics") or
                path.startswith("/ws")):
                # Deixar FastAPI processar
                # (Isto nunca deve ser alcançado se rotas estão registradas)
                response = Response("Not Found", status_code=404)
                await response(scope, receive, send)
                return
            
            # Encaminhar para Dash
            await self.asgi_app(scope, receive, send)
    
    app.mount(
        settings.DASH_URL_BASE_PATHNAME,
        DashApp(asgi_app),
        name="dash_app"
    )
    return app


# Criar aplicação FastAPI primeiro
app = create_application()

# Montar Dash POR ÚLTIMO (após todas as rotas da API estarem registradas)
app = mount_dash(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
