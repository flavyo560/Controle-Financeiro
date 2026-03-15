"""Modelo ORM para tabela despesas."""

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, ForeignKey, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Despesa(Base):
    """Despesas do usuário (simples, parcelas e recorrentes)."""

    __tablename__ = "despesas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    descricao = Column(Text)
    valor = Column(Numeric(15, 2), nullable=False)
    data = Column(Date, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    pago = Column(Boolean, default=False)
    data_vencimento = Column(Date)
    data_pagamento = Column(Date)
    parcela_numero = Column(Integer)
    parcela_total = Column(Integer)
    despesa_parcelada_id = Column(Integer, ForeignKey("despesas_parceladas.id"))
    despesa_recorrente_id = Column(Integer, ForeignKey("despesas_recorrentes.id"))
    cartao_id = Column(Integer, ForeignKey("cartoes.id"))
    mes_fatura = Column(String(7))
    ativo = Column(Boolean, default=True)

    # Relationships
    usuario = relationship("Usuario", back_populates="despesas")
    categoria = relationship("Categoria", back_populates="despesas")
    banco = relationship("Banco", back_populates="despesas")
    despesa_parcelada = relationship("DespesaParcelada", back_populates="despesas")
    despesa_recorrente = relationship("DespesaRecorrente", back_populates="despesas")
    cartao = relationship("Cartao", back_populates="despesas")
    pagamento_fatura = relationship("PagamentoFatura", back_populates="despesa")
