"""
Rotas FastAPI para gerenciamento de cache de dados climáticos.

Endpoints:
- GET /api/cache/climate/{location_id}: Busca dados climáticos (cache-first)
- POST /api/cache/prefetch: Pré-carrega dados para múltiplas localizações
- GET /api/cache/stats: Estatísticas de cache
- DELETE /api/cache/clear: Limpa cache
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.services.cache_manager import SessionCache
from backend.database.connection import get_db
from backend.database.redis_pool import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/climate/{location_id}")
async def get_cached_climate(
    location_id: int,
    session_id: str = Header(None, description="Session ID do usuário anônimo"),
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Busca dados climáticos com estratégia cache-first.
    
    Strategy:
    1. Se force_refresh=true, ignora cache e busca API
    2. Se em cache (Redis), retorna (HIT)
    3. Se não em cache, busca API e armazena (MISS)
    
    Args:
        location_id: ID da localização (world_locations.id)
        session_id: ID da sessão (opcional, gerado se não fornecido)
        force_refresh: Forçar busca na API, ignorando cache
        
    Returns:
        {
            "source": "cache" | "api",
            "data": {...dados climáticos...},
            "timestamp": "2025-10-22T20:30:00",
            "ttl": 3600
        }
        
    Example:
        GET /api/cache/climate/42?force_refresh=false
        Headers:
            Session-ID: sess_abc123def456
            
    Response (200):
        {
            "source": "cache",
            "data": {
                "temperature": 25.5,
                "humidity": 60,
                "wind_speed": 5.2
            },
            "timestamp": "2025-10-22T20:30:00",
            "ttl": 3600
        }
    """
    if location_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="location_id deve ser > 0"
        )
    
    # Gerar session_id se não fornecido
    if not session_id:
        session_id = SessionCache.generate_session_id()
    
    try:
        redis_client = get_redis_client()
        cache = SessionCache(redis_client, db)
        
        # Buscar dados (cache-first)
        data = await cache.get_or_fetch_climate(
            location_id=location_id,
            session_id=session_id,
            force_refresh=force_refresh
        )
        
        return {
            "source": "api" if force_refresh else "cache",
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "ttl": cache.ttl,
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro buscar dados climáticos: {str(e)}"
        )


@router.post("/prefetch")
async def prefetch_climate_data(
    location_ids: List[int],
    session_id: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Pré-carrega dados climáticos para múltiplas localizações.
    
    Útil para:
    - Preparar dados antes de navegação
    - Reduzir latência em buscas futuras
    - Sincronizar com favoritos do usuário
    
    Args:
        location_ids: Lista de IDs de localização
        session_id: ID da sessão
        
    Returns:
        {
            "prefetched": 5,
            "failed": 0,
            "session_id": "sess_...",
            "timestamp": "2025-10-22T20:30:00"
        }
        
    Example:
        POST /api/cache/prefetch
        Headers:
            Session-ID: sess_abc123def456
            
        Body:
            {
                "location_ids": [1, 2, 42, 100]
            }
            
    Response (200):
        {
            "prefetched": 4,
            "failed": 0,
            "session_id": "sess_abc123def456",
            "timestamp": "2025-10-22T20:30:00"
        }
    """
    if not location_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="location_ids vazio"
        )
    
    if len(location_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 50 localizações por prefetch"
        )
    
    # Gerar session_id se não fornecido
    if not session_id:
        session_id = SessionCache.generate_session_id()
    
    try:
        redis_client = get_redis_client()
        cache = SessionCache(redis_client, db)
        
        prefetched = 0
        failed = 0
        
        for location_id in location_ids:
            try:
                await cache.get_or_fetch_climate(
                    location_id=location_id,
                    session_id=session_id
                )
                prefetched += 1
            except Exception as e:
                failed += 1
                logger.error(f"Erro prefetch location_id={location_id}: {e}")
        
        return {
            "prefetched": prefetched,
            "failed": failed,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro em prefetch: {str(e)}"
        )


@router.get("/stats")
async def get_cache_stats(
    session_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas de cache.
    
    Args:
        session_id: Se fornecido, retorna stats apenas dessa sessão
        
    Returns:
        {
            "hits": 42,
            "misses": 8,
            "hit_ratio": 0.84,
            "total_requests": 50,
            "session_locations_cached": 12,
            "timestamp": "2025-10-22T20:30:00"
        }
        
    Example:
        GET /api/cache/stats
        Headers:
            Session-ID: sess_abc123def456
            
    Response (200):
        {
            "hits": 42,
            "misses": 8,
            "hit_ratio": 0.84,
            "total_requests": 50,
            "session_locations_cached": 12,
            "timestamp": "2025-10-22T20:30:00"
        }
    """
    try:
        redis_client = get_redis_client()
        cache = SessionCache(redis_client, db)
        
        stats = cache.get_cache_stats(session_id=session_id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter stats: {str(e)}"
        )


@router.delete("/clear")
async def clear_cache(
    location_id: Optional[int] = None,
    session_id: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Limpa cache de dados climáticos.
    
    Args:
        location_id: Se fornecido, limpa apenas essa localização
        session_id: ID da sessão (para audit log)
        
    Returns:
        {
            "removed": 5,
            "session_id": "sess_...",
            "timestamp": "2025-10-22T20:30:00"
        }
        
    Example:
        DELETE /api/cache/clear?location_id=42
        Headers:
            Session-ID: sess_abc123def456
            
    Response (200):
        {
            "removed": 1,
            "session_id": "sess_abc123def456",
            "timestamp": "2025-10-22T20:30:00"
        }
    """
    try:
        redis_client = get_redis_client()
        cache = SessionCache(redis_client, db)
        
        removed = await cache.clear_cache(location_id=location_id)
        
        return {
            "removed": removed,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar cache: {str(e)}"
        )


__all__ = ["router"]
