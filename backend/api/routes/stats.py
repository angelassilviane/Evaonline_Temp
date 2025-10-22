import redis
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.analytics.visitor_counter_service import VisitorCounterService
from backend.database.connection import get_db

router = APIRouter(prefix="/stats", tags=["stats"])


def get_visitor_service(
    db: Session = Depends(get_db),
) -> VisitorCounterService:
    """Dependency para obter o serviço de visitantes"""
    redis_client = redis.from_url("redis://:evaonline@redis:6379/0")
    return VisitorCounterService(redis_client, db)


@router.get("/visitors")
async def get_visitor_count(
    service: VisitorCounterService = Depends(get_visitor_service),
):
    """
    Retorna contagem de visitantes em tempo real.
    
    Response:
    {
        "total_visitors": 15342,
        "current_hour_visitors": 48,
        "current_hour": "14:00",
        "peak_hour": "14:00",
        "timestamp": "2025-10-18T14:30:00"
    }
    """
    return service.get_stats()


@router.post("/visitors/increment")
async def increment_visitor_count(
    service: VisitorCounterService = Depends(get_visitor_service),
):
    """
    Incrementa contador de visitantes.
    Chamado quando página carrega.
    
    Response:
    {
        "total_visitors": 15343,
        "current_hour_visitors": 49,
        "current_hour": "14:00",
        "timestamp": "2025-10-18T14:30:00"
    }
    """
    return service.increment_visitor()


@router.get("/visitors/database")
async def get_database_stats(
    service: VisitorCounterService = Depends(get_visitor_service),
):
    """
    Retorna estatísticas persistidas no banco de dados.
    Útil para histórico de longo prazo.
    """
    return service.get_database_stats()


@router.post("/visitors/sync")
async def sync_to_database(
    service: VisitorCounterService = Depends(get_visitor_service),
) -> dict:
    """
    Sincroniza dados de Redis para PostgreSQL.
    Útil para executar periodicamente (ex: a cada hora).
    """
    return service.sync_to_database()
