"""Modelo ORM para tabela assinaturas."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Assinatura(Base):
    """Assinatura de plano do usuário."""

    __tablename__ = "assinaturas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    plano = Column(String(20), nullable=False)  # 'simples' | 'plus'
    ciclo = Column(String(10), nullable=False)  # 'mensal' | 'anual'
    status = Column(String(20), nullable=False, server_default="ativa")
    data_inicio = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    data_renovacao = Column(DateTime(timezone=True))
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    stripe_price_id = Column(String(255))
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    usuario = relationship("Usuario", back_populates="assinatura")
