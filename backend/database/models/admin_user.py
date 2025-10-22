import secrets
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped

from backend.database.connection import Base


class AdminUser(Base):
    """
    Usuários administradores.
    
    Roles:
    - SUPER_ADMIN: Acesso total
    - ADMIN: Grafana + Prometheus
    - DEVELOPER: Logs + Health check
    """
    __tablename__ = "admin_users"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    username: Mapped[str] = Column(String(255), unique=True, nullable=False)
    email: Mapped[str] = Column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = Column(String(255), nullable=False)
    role: Mapped[str] = Column(
        String(50), 
        default="DEVELOPER",
        nullable=False
        # "SUPER_ADMIN", "ADMIN", "DEVELOPER"
    )
    is_active: Mapped[bool] = Column(Boolean, default=True)
    last_login: Mapped[datetime] = Column(DateTime, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    api_token: Mapped[str] = Column(
        String(255), 
        default=lambda: secrets.token_urlsafe(32),
        unique=True
    )
    
    def verify_password(self, password: str) -> bool:
        """Verifica senha (bcrypt)"""
        import bcrypt
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def __repr__(self):
        return f"<AdminUser({self.username}, role={self.role})>"
