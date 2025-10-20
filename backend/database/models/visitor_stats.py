from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped

from backend.database.connection import Base


class VisitorStats(Base):
    """
    Estatísticas persistentes de visitantes.
    
    Dados:
    - total_visitors: Contagem total acumulada
    - unique_visitors_today: Visitantes únicos hoje
    - last_sync: Última sincronização com Redis
    - peak_hour: Hora de pico
    """
    __tablename__ = "visitor_stats"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    total_visitors: Mapped[int] = Column(Integer, default=0)
    unique_visitors_today: Mapped[int] = Column(Integer, default=0)
    last_sync: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    peak_hour: Mapped[str] = Column(String(5), nullable=True)  # "14:30"
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<VisitorStats(total={self.total_visitors}, today={self.unique_visitors_today})>"
