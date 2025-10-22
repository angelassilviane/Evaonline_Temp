from datetime import datetime, timedelta

import jwt
import redis
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.database.models import AdminUser

security = HTTPBearer()
redis_client = redis.from_url("redis://redis:6379")

class AdminAuthManager:
    """Gerencia autenticação de admins"""
    
    SECRET_KEY = "sua-chave-super-secreta-aqui"  # Use env vars!
    ALGORITHM = "HS256"
    TOKEN_EXPIRE = 24 * 3600  # 24h
    
    @classmethod
    def create_token(cls, user_id: int, role: str) -> str:
        """Cria JWT token"""
        payload = {
            "sub": str(user_id),
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
    
    @classmethod
    async def verify_token(cls, token: str) -> dict:
        """Verifica validade do token"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except:
            raise HTTPException(status_code=401, detail="Token inválido")
    
    @classmethod
    def create_session(cls, user_id: int, role: str, token: str):
        """Cria sessão no Redis"""
        session_key = f"admin:session:{user_id}"
        redis_client.setex(
            session_key,
            cls.TOKEN_EXPIRE,
            token
        )
    
    @classmethod
    def get_current_admin(
        cls,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """Dependency para proteger rotas"""
        token = credentials.credentials
        return cls.verify_token(token)
