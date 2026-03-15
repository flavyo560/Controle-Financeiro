"""Modelo ORM para tabela usuarios."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Usuario(Base):
    """Tabela de usuários — base para RLS."""

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255))
    senha_hash_bcrypt = Column(String(255))
    cpf = Column(String(14))
    telefone = Column(String(20))
    perfil = Column(String(50), default="admin")
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    bancos = relationship("Banco", back_populates="usuario", cascade="all, delete-orphan")
    categorias = relationship("Categoria", back_populates="usuario", cascade="all, delete-orphan")
    receitas = relationship("Receita", back_populates="usuario", cascade="all, delete-orphan")
    despesas = relationship("Despesa", back_populates="usuario", cascade="all, delete-orphan")
    despesas_parceladas = relationship("DespesaParcelada", back_populates="usuario", cascade="all, delete-orphan")
    despesas_recorrentes = relationship("DespesaRecorrente", back_populates="usuario", cascade="all, delete-orphan")
    cartoes = relationship("Cartao", back_populates="usuario", cascade="all, delete-orphan")
    investimentos = relationship("Investimento", back_populates="usuario", cascade="all, delete-orphan")
    transferencias = relationship("Transferencia", back_populates="usuario", cascade="all, delete-orphan")
    veiculos = relationship("Veiculo", back_populates="usuario", cascade="all, delete-orphan")
    orcamentos = relationship("Orcamento", back_populates="usuario", cascade="all, delete-orphan")
    configuracoes = relationship("Configuracao", back_populates="usuario", cascade="all, delete-orphan")
