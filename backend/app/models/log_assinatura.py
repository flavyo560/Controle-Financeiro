"""Modelo ORM para tabela logs_assinatura."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class LogAssinatura(Base):
    """Log de eventos e alterações de status de assinaturas."""

    __tablename__ = "logs_assinatura"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    evento = Column(String(100), nullable=False)
    status_anterior = Column(String(20))
    status_novo = Column(String(20))
    detalhes = Column(Text)
    stripe_event_id = Column(String(255))
    admin_id = Column(Integer, ForeignKey("usuarios.id"))
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
