"""Modelo ORM para tabela manutencoes."""

from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Manutencao(Base):
    """Registros de manutenção de veículos."""

    __tablename__ = "manutencoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id", ondelete="CASCADE"), nullable=False)
    data = Column(Date, nullable=False)
    servico = Column(Text)
    valor = Column(Numeric(15, 2), nullable=False)
    km = Column(Numeric(10, 1))

    # Relationships
    veiculo = relationship("Veiculo", back_populates="manutencoes")
