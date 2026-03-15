"""Modelo ORM para tabela cartoes."""

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey,
    CheckConstraint, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Cartao(Base):
    """Cartões de crédito do usuário."""

    __tablename__ = "cartoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(255), nullable=False)
    bandeira = Column(String(50))
    limite_total = Column(Numeric(15, 2), nullable=False)
    dia_fechamento = Column(Integer, nullable=False)
    dia_vencimento = Column(Integer, nullable=False)
    status = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("limite_total > 0", name="ck_cartoes_limite_total"),
        CheckConstraint("dia_fechamento >= 1 AND dia_fechamento <= 31", name="ck_cartoes_dia_fechamento"),
        CheckConstraint("dia_vencimento >= 1 AND dia_vencimento <= 31", name="ck_cartoes_dia_vencimento"),
        UniqueConstraint("usuario_id", "nome", name="uq_cartoes_usuario_nome"),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="cartoes")
    compras = relationship("CompraCartao", back_populates="cartao")
    pagamentos_fatura = relationship("PagamentoFatura", back_populates="cartao")
    despesas = relationship("Despesa", back_populates="cartao")
