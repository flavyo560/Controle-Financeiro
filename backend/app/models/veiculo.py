"""Modelo ORM para tabela veiculos."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Veiculo(Base):
    """Veículos da frota do usuário."""

    __tablename__ = "veiculos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nome_identificador = Column(String(255), nullable=False)
    placa = Column(String(10))
    modelo = Column(String(255))
    status = Column(Boolean, default=True)

    # Relationships
    usuario = relationship("Usuario", back_populates="veiculos")
    abastecimentos = relationship("Abastecimento", back_populates="veiculo", cascade="all, delete-orphan")
    manutencoes = relationship("Manutencao", back_populates="veiculo", cascade="all, delete-orphan")
