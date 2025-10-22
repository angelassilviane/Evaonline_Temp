"""
Rotas FastAPI para sistema de favoritos de usuários anônimos.

Endpoints:
- GET /api/favorites: Lista todos os favoritos
- POST /api/favorites: Adiciona nova localização aos favoritos
- DELETE /api/favorites/{location_id}: Remove de favoritos
- GET /api/favorites/{location_id}/exists: Verifica se é favorito
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import FavoriteLocation, UserFavorites, WorldLocation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["favorites"])

# Limite máximo de favoritos por usuário
MAX_FAVORITES = 20


@router.get("")
async def list_favorites(
    session_id: str = Header(..., description="Session ID do usuário"),
    db: Session = Depends(get_db)
):
    """
    Lista todas as localizações marcadas como favorito.
    
    Args:
        session_id: ID da sessão do usuário anônimo
        
    Returns:
        [
            {
                "id": 1,
                "location_id": 42,
                "location_name": "Paris",
                "country": "France",
                "lat": 48.856,
                "lon": 2.352,
                "elevation_m": 35,
                "added_at": "2025-10-22T18:00:00",
                "notes": "Visitei em 2023"
            },
            ...
        ]
        
    Example:
        GET /api/favorites
        Headers:
            Session-ID: sess_abc123def456
            
    Response (200):
        [
            {
                "id": 1,
                "location_id": 42,
                "location_name": "Paris",
                "country": "France",
                "lat": 48.856,
                "lon": 2.352,
                "elevation_m": 35,
                "added_at": "2025-10-22T18:00:00"
            }
        ]
    """
    try:
        # Buscar favoritos do usuário
        user_favorites = db.query(UserFavorites).filter(
            UserFavorites.session_id == session_id
        ).first()
        
        if not user_favorites:
            logger.info(f"Favoritos não encontrados para session={session_id[:12]}...")
            return []
        
        # Buscar localizações favoritas com detalhes
        favorites = db.query(
            FavoriteLocation.id,
            FavoriteLocation.location_id,
            FavoriteLocation.added_at,
            FavoriteLocation.notes,
            WorldLocation.location_name,
            WorldLocation.country,
            WorldLocation.lat,
            WorldLocation.lon,
            WorldLocation.elevation_m
        ).join(
            WorldLocation,
            FavoriteLocation.location_id == WorldLocation.id
        ).filter(
            FavoriteLocation.user_favorites_id == user_favorites.id
        ).all()
        
        result = [
            {
                "id": f.id,
                "location_id": f.location_id,
                "location_name": f.location_name,
                "country": f.country,
                "lat": f.lat,
                "lon": f.lon,
                "elevation_m": f.elevation_m,
                "added_at": f.added_at.isoformat() if f.added_at else None,
                "notes": f.notes
            }
            for f in favorites
        ]
        
        logger.info(f"Retornando {len(result)} favoritos para session={session_id[:12]}...")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao listar favoritos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar favoritos: {str(e)}"
        )


@router.post("")
async def add_favorite(
    location_id: int,
    session_id: str = Header(...),
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Adiciona uma localização aos favoritos do usuário.
    
    Validações:
    - location_id deve existir em world_locations
    - Máximo 20 favoritos por usuário
    - Não permite duplicatas
    
    Args:
        location_id: ID da localização a adicionar
        session_id: ID da sessão do usuário
        notes: Anotações opcionais (max 500 chars)
        
    Returns:
        {
            "id": 1,
            "location_id": 42,
            "location_name": "Paris",
            "country": "France",
            "added_at": "2025-10-22T20:30:00",
            "notes": "Visitei em 2023",
            "total_favorites": 1
        }
        
    Example:
        POST /api/favorites?location_id=42
        Headers:
            Session-ID: sess_abc123def456
            
        Body:
            {
                "notes": "Visitei em 2023"
            }
            
    Response (201):
        {
            "id": 1,
            "location_id": 42,
            "location_name": "Paris",
            "country": "France",
            "added_at": "2025-10-22T20:30:00",
            "notes": "Visitei em 2023",
            "total_favorites": 1
        }
    """
    if location_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="location_id deve ser > 0"
        )
    
    if notes and len(notes) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="notes máximo 500 caracteres"
        )
    
    try:
        # Verificar se localização existe
        location = db.query(WorldLocation).filter(
            WorldLocation.id == location_id
        ).first()
        
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Localização {location_id} não encontrada"
            )
        
        # Buscar ou criar favoritos do usuário
        user_favorites = db.query(UserFavorites).filter(
            UserFavorites.session_id == session_id
        ).first()
        
        if not user_favorites:
            user_favorites = UserFavorites(session_id=session_id)
            db.add(user_favorites)
            db.commit()
        
        # Verificar limite de favoritos
        current_count = db.query(FavoriteLocation).filter(
            FavoriteLocation.user_favorites_id == user_favorites.id
        ).count()
        
        if current_count >= MAX_FAVORITES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limite de {MAX_FAVORITES} favoritos atingido"
            )
        
        # Verificar se já é favorito
        existing = db.query(FavoriteLocation).filter(
            FavoriteLocation.user_favorites_id == user_favorites.id,
            FavoriteLocation.location_id == location_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Localização {location_id} já é favorita"
            )
        
        # Adicionar novo favorito
        favorite = FavoriteLocation(
            user_favorites_id=user_favorites.id,
            location_id=location_id,
            notes=notes
        )
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        
        logger.info(f"Favorito adicionado: session={session_id[:12]}..., location_id={location_id}")
        
        return {
            "id": favorite.id,
            "location_id": favorite.location_id,
            "location_name": location.location_name,
            "country": location.country,
            "lat": location.lat,
            "lon": location.lon,
            "elevation_m": location.elevation_m,
            "added_at": favorite.added_at.isoformat() if favorite.added_at else None,
            "notes": favorite.notes,
            "total_favorites": current_count + 1
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar favorito: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao adicionar favorito: {str(e)}"
        )


@router.delete("/{location_id}")
async def remove_favorite(
    location_id: int,
    session_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Remove uma localização dos favoritos do usuário.
    
    Args:
        location_id: ID da localização a remover
        session_id: ID da sessão do usuário
        
    Returns:
        {
            "removed": true,
            "location_id": 42,
            "total_favorites": 0,
            "timestamp": "2025-10-22T20:30:00"
        }
        
    Example:
        DELETE /api/favorites/42
        Headers:
            Session-ID: sess_abc123def456
            
    Response (200):
        {
            "removed": true,
            "location_id": 42,
            "total_favorites": 0,
            "timestamp": "2025-10-22T20:30:00"
        }
    """
    try:
        # Buscar favoritos do usuário
        user_favorites = db.query(UserFavorites).filter(
            UserFavorites.session_id == session_id
        ).first()
        
        if not user_favorites:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não possui favoritos"
            )
        
        # Buscar favorito
        favorite = db.query(FavoriteLocation).filter(
            FavoriteLocation.user_favorites_id == user_favorites.id,
            FavoriteLocation.location_id == location_id
        ).first()
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Localização {location_id} não é favorita"
            )
        
        # Remover
        db.delete(favorite)
        db.commit()
        
        # Contar favoritos restantes
        remaining = db.query(FavoriteLocation).filter(
            FavoriteLocation.user_favorites_id == user_favorites.id
        ).count()
        
        logger.info(f"Favorito removido: session={session_id[:12]}..., location_id={location_id}")
        
        return {
            "removed": True,
            "location_id": location_id,
            "total_favorites": remaining,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover favorito: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover favorito: {str(e)}"
        )


@router.get("/{location_id}/exists")
async def check_favorite_exists(
    location_id: int,
    session_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Verifica se uma localização é favorita do usuário.
    
    Útil para atualizar UI (mostrar/esconder estrela).
    
    Args:
        location_id: ID da localização
        session_id: ID da sessão do usuário
        
    Returns:
        {
            "exists": true,
            "location_id": 42
        }
        
    Example:
        GET /api/favorites/42/exists
        Headers:
            Session-ID: sess_abc123def456
            
    Response (200):
        {
            "exists": true,
            "location_id": 42
        }
    """
    try:
        # Buscar favoritos do usuário
        user_favorites = db.query(UserFavorites).filter(
            UserFavorites.session_id == session_id
        ).first()
        
        if not user_favorites:
            return {
                "exists": False,
                "location_id": location_id
            }
        
        # Verificar se é favorito
        exists = db.query(FavoriteLocation).filter(
            FavoriteLocation.user_favorites_id == user_favorites.id,
            FavoriteLocation.location_id == location_id
        ).first() is not None
        
        return {
            "exists": exists,
            "location_id": location_id
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar favorito: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar favorito: {str(e)}"
        )


__all__ = ["router"]
