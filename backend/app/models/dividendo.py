"""Modelo ORM para tabela dividendos."""

from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Dividendo(Base):
    """Dividendos recebidos de investimentos."""

    __tablename__ = "dividendos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investimento_id = Column(Integer, ForeignKey("investimentos.id", ondelete="CASCADE"), nullable=False)
    valor = Column(Numeric(15, 2), nullable=False)
    data = Column(Date, nullable=False)

    # Relationships
    investimento = relationship("Investimento", back_populates="dividendos")
