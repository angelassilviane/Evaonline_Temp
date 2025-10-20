from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.security.auth import AdminAuthManager
from backend.database.connection import get_db
from backend.database.models import AdminUser

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.post("/login")
async def admin_login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    Login para administradores.
    
    Retorna JWT token para acessar dashboards.
    """
    user = db.query(AdminUser).filter_by(username=username).first()
    
    if not user or not user.verify_password(password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    
    token = AdminAuthManager.create_token(user.id, user.role)
    AdminAuthManager.create_session(user.id, user.role, token)
    
    # Atualizar last_login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "dashboards": {
            "grafana": "http://localhost:3000",
            "prometheus": "http://localhost:9090",
            "logs": "http://localhost:8000/logs"
        }
    }

@router.get("/grafana-proxy")
async def grafana_proxy(
    current_admin: dict = Depends(AdminAuthManager.get_current_admin)
):
    """Proxy para Grafana (com autenticação)"""
    return {"url": "http://grafana:3000"}

@router.get("/prometheus-proxy")
async def prometheus_proxy(
    current_admin: dict = Depends(AdminAuthManager.get_current_admin)
):
    """Proxy para Prometheus"""
    return {"url": "http://prometheus:9090"}
