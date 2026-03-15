"""Modelo ORM para tabela itens_orcamento."""

from sqlalchemy import (
    Column, Integer, Numeric, DateTime, ForeignKey, CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ItemOrcamento(Base):
    """Itens individuais de um orçamento (categoria × mês)."""

    __tablename__ = "itens_orcamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    orcamento_id = Column(Integer, ForeignKey("orcamentos.id", ondelete="CASCADE"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="CASCADE"), nullable=False)
    mes = Column(Integer, nullable=False)
    valor_planejado = Column(Numeric(15, 2), nullable=False)
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("mes >= 1 AND mes <= 12", name="ck_itens_orcamento_mes"),
        CheckConstraint("valor_planejado >= 0", name="ck_itens_orcamento_valor_planejado"),
        UniqueConstraint("orcamento_id", "categoria_id", "mes", name="uq_itens_orcamento_composto"),
    )

    # Relationships
    orcamento = relationship("Orcamento", back_populates="itens")
    categoria = relationship("Categoria", back_populates="itens_orcamento")
    historico = relationship("HistoricoOrcamento", back_populates="item_orcamento", cascade="all, delete-orphan")
