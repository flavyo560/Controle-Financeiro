"""Modelo ORM para tabela categorias."""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Categoria(Base):
    """Categorias de receitas e despesas."""

    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("tipo IN ('receita', 'despesa')", name="ck_categorias_tipo"),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="categorias")
    receitas = relationship("Receita", back_populates="categoria")
    despesas = relationship("Despesa", back_populates="categoria")
    despesas_parceladas = relationship("DespesaParcelada", back_populates="categoria")
    despesas_recorrentes = relationship("DespesaRecorrente", back_populates="categoria")
    compras_cartao = relationship("CompraCartao", back_populates="categoria")
    investimentos = relationship("Investimento", back_populates="categoria")
    itens_orcamento = relationship("ItemOrcamento", back_populates="categoria", cascade="all, delete-orphan")
