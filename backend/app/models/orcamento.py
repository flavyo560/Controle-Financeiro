"""Modelo ORM para tabela orcamentos."""

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Orcamento(Base):
    """Orçamentos anuais do usuário."""

    __tablename__ = "orcamentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    ano = Column(Integer, nullable=False)
    status = Column(String(10), nullable=False, default="ativo")
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("ano >= 2000 AND ano <= 2100", name="ck_orcamentos_ano"),
        CheckConstraint("status IN ('ativo', 'inativo')", name="ck_orcamentos_status"),
        UniqueConstraint("usuario_id", "ano", name="uq_orcamentos_usuario_ano"),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="orcamentos")
    itens = relationship("ItemOrcamento", back_populates="orcamento", cascade="all, delete-orphan")
