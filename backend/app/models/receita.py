"""Modelo ORM para tabela receitas."""

from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Receita(Base):
    """Receitas do usuário."""

    __tablename__ = "receitas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    descricao = Column(Text)
    valor = Column(Numeric(15, 2), nullable=False)
    data = Column(Date, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    ativo = Column(Boolean, default=True)

    # Relationships
    usuario = relationship("Usuario", back_populates="receitas")
    categoria = relationship("Categoria", back_populates="receitas")
    banco = relationship("Banco", back_populates="receitas")
