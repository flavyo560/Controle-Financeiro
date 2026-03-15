"""Modelo ORM para tabela transferencias."""

from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Transferencia(Base):
    """Transferências entre contas bancárias."""

    __tablename__ = "transferencias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    banco_origem_id = Column(Integer, ForeignKey("bancos.id"))
    banco_destino_id = Column(Integer, ForeignKey("bancos.id"))
    valor = Column(Numeric(15, 2), nullable=False)
    data = Column(Date, nullable=False)
    descricao = Column(Text)

    # Relationships
    usuario = relationship("Usuario", back_populates="transferencias")
    banco_origem = relationship("Banco", back_populates="transferencias_origem", foreign_keys=[banco_origem_id])
    banco_destino = relationship("Banco", back_populates="transferencias_destino", foreign_keys=[banco_destino_id])
