"""Modelo ORM para tabela compras_cartao."""

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, BigInteger, ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CompraCartao(Base):
    """Compras realizadas no cartão de crédito."""

    __tablename__ = "compras_cartao"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cartao_id = Column(Integer, ForeignKey("cartoes.id"), nullable=False)
    descricao = Column(String(255), nullable=False)
    valor = Column(Numeric(15, 2), nullable=False)
    data_compra = Column(Date, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    mes_fatura = Column(String(7), nullable=False)
    parcela_atual = Column(Integer)
    total_parcelas = Column(Integer)
    compra_parcelada_id = Column(BigInteger)
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_compras_cartao_valor"),
        CheckConstraint(
            "parcela_atual IS NULL OR parcela_atual > 0",
            name="ck_compras_cartao_parcela_atual",
        ),
        CheckConstraint(
            "total_parcelas IS NULL OR total_parcelas >= 1",
            name="ck_compras_cartao_total_parcelas",
        ),
    )

    # Relationships
    cartao = relationship("Cartao", back_populates="compras")
    categoria = relationship("Categoria", back_populates="compras_cartao")
