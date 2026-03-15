"""Modelo ORM para tabela configuracoes."""

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Configuracao(Base):
    """Configurações por usuário (chave-valor)."""

    __tablename__ = "configuracoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    chave = Column(String(255), nullable=False)
    valor = Column(Text)

    __table_args__ = (
        UniqueConstraint("usuario_id", "chave", name="uq_configuracoes_usuario_chave"),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="configuracoes")
