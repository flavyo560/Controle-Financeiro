"""Modelo ORM para tabela pagamentos_fatura."""

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PagamentoFatura(Base):
    """Pagamentos de fatura de cartão de crédito."""

    __tablename__ = "pagamentos_fatura"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cartao_id = Column(Integer, ForeignKey("cartoes.id"), nullable=False)
    mes_fatura = Column(String(7), nullable=False)
    valor_pago = Column(Numeric(15, 2), nullable=False)
    data_pagamento = Column(Date, nullable=False)
    banco_id = Column(Integer, ForeignKey("bancos.id"), nullable=False)
    despesa_id = Column(Integer, ForeignKey("despesas.id"))
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("valor_pago > 0", name="ck_pagamentos_fatura_valor_pago"),
    )

    # Relationships
    cartao = relationship("Cartao", back_populates="pagamentos_fatura")
    banco = relationship("Banco", back_populates="pagamentos_fatura")
    despesa = relationship("Despesa", back_populates="pagamento_fatura")
