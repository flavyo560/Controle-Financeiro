"""Modelo ORM para tabela bancos."""

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Banco(Base):
    """Contas bancárias do usuário."""

    __tablename__ = "bancos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(255), nullable=False)
    saldo_inicial = Column(Numeric(15, 2), default=0)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("usuario_id", "nome", name="uq_bancos_usuario_nome"),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="bancos")
    receitas = relationship("Receita", back_populates="banco")
    despesas = relationship("Despesa", back_populates="banco")
    despesas_parceladas = relationship("DespesaParcelada", back_populates="banco")
    despesas_recorrentes = relationship("DespesaRecorrente", back_populates="banco")
    pagamentos_fatura = relationship("PagamentoFatura", back_populates="banco")
    investimentos = relationship("Investimento", back_populates="banco")
    transferencias_origem = relationship(
        "Transferencia", back_populates="banco_origem", foreign_keys="Transferencia.banco_origem_id"
    )
    transferencias_destino = relationship(
        "Transferencia", back_populates="banco_destino", foreign_keys="Transferencia.banco_destino_id"
    )
