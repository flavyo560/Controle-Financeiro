"""Modelo ORM para tabela abastecimentos."""

from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Abastecimento(Base):
    """Registros de abastecimento de veículos."""

    __tablename__ = "abastecimentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id", ondelete="CASCADE"), nullable=False)
    data = Column(Date, nullable=False)
    litros = Column(Numeric(10, 2))
    valor = Column(Numeric(15, 2), nullable=False)
    km = Column(Numeric(10, 1))
    posto = Column(String(255))
    tipo = Column(String(50))
    litros_gasolina = Column(Numeric(10, 2))
    litros_etanol = Column(Numeric(10, 2))

    # Relationships
    veiculo = relationship("Veiculo", back_populates="abastecimentos")
