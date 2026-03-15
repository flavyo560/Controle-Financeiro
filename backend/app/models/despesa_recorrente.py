"""Modelo ORM para tabela despesas_recorrentes."""

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime, ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DespesaRecorrente(Base):
    """Despesas recorrentes — geram lançamentos automáticos."""

    __tablename__ = "despesas_recorrentes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    descricao = Column(String(255), nullable=False)
    valor = Column(Numeric(15, 2), nullable=False)
    dia_mes = Column(Integer, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date)
    ativa = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("dia_mes >= 1 AND dia_mes <= 31", name="ck_despesas_recorrentes_dia_mes"),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="despesas_recorrentes")
    categoria = relationship("Categoria", back_populates="despesas_recorrentes")
    banco = relationship("Banco", back_populates="despesas_recorrentes")
    despesas = relationship("Despesa", back_populates="despesa_recorrente")
