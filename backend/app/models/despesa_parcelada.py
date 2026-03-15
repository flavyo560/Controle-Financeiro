"""Modelo ORM para tabela despesas_parceladas."""

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, ForeignKey, CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DespesaParcelada(Base):
    """Despesas parceladas — registro pai das parcelas."""

    __tablename__ = "despesas_parceladas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    descricao = Column(String(255), nullable=False)
    valor_total = Column(Numeric(15, 2), nullable=False)
    numero_parcelas = Column(Integer, nullable=False)
    data_primeira_parcela = Column(Date, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "numero_parcelas > 1 AND numero_parcelas <= 120",
            name="ck_despesas_parceladas_numero_parcelas",
        ),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="despesas_parceladas")
    categoria = relationship("Categoria", back_populates="despesas_parceladas")
    banco = relationship("Banco", back_populates="despesas_parceladas")
    despesas = relationship("Despesa", back_populates="despesa_parcelada")
