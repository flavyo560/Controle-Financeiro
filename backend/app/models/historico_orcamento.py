"""Modelo ORM para tabela historico_orcamento."""

from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class HistoricoOrcamento(Base):
    """Histórico de alterações em itens de orçamento."""

    __tablename__ = "historico_orcamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_orcamento_id = Column(Integer, ForeignKey("itens_orcamento.id", ondelete="CASCADE"), nullable=False)
    data_alteracao = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    valor_anterior = Column(Numeric(15, 2), nullable=False)
    valor_novo = Column(Numeric(15, 2), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))

    # Relationships
    item_orcamento = relationship("ItemOrcamento", back_populates="historico")
    usuario = relationship("Usuario")
