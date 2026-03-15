"""Modelo ORM para tabela investimentos."""

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Investimento(Base):
    """Investimentos do usuário."""

    __tablename__ = "investimentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(255), nullable=False)
    tipo = Column(String(100))
    valor_investido = Column(Numeric(15, 2), nullable=False)
    valor_atual = Column(Numeric(15, 2))
    data = Column(Date, nullable=False)
    ativo = Column(Boolean, default=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    usuario = relationship("Usuario", back_populates="investimentos")
    categoria = relationship("Categoria", back_populates="investimentos")
    banco = relationship("Banco", back_populates="investimentos")
    dividendos = relationship("Dividendo", back_populates="investimento", cascade="all, delete-orphan")
