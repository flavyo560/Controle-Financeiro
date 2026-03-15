"""Schemas Pydantic para bancos."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BancoCreate(BaseModel):
    """Corpo da requisição para criar banco."""

    nome: str = Field(min_length=1, max_length=255)
    saldo_inicial: Decimal = Field(default=Decimal("0"))


class BancoUpdate(BaseModel):
    """Corpo da requisição para atualizar banco."""

    nome: str | None = Field(default=None, min_length=1, max_length=255)
    saldo_inicial: Decimal | None = None
    ativo: bool | None = None


class BancoResponse(BaseModel):
    """Dados do banco retornados pela API."""

    id: int
    nome: str
    saldo_inicial: Decimal
    ativo: bool
    criado_em: datetime | None = None
    saldo_calculado: Decimal = Decimal("0")

    model_config = {"from_attributes": True}


class SaldoDetalhadoResponse(BaseModel):
    """Saldo detalhado de um banco."""

    banco_id: int
    nome: str
    saldo_inicial: Decimal
    total_receitas: Decimal
    total_despesas_pagas: Decimal
    total_transferencias_entrada: Decimal
    total_transferencias_saida: Decimal
    saldo_calculado: Decimal
