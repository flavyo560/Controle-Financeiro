"""Schemas Pydantic para investimentos e dividendos."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class InvestimentoCreate(BaseModel):
    """Corpo da requisição para criar investimento."""

    nome: str = Field(min_length=1, max_length=255)
    tipo: str | None = Field(default=None, max_length=100)
    valor_investido: Decimal = Field(ge=0)
    valor_atual: Decimal | None = None
    data: date
    ativo: bool = True
    categoria_id: int | None = None
    banco_id: int | None = None


class InvestimentoUpdate(BaseModel):
    """Corpo da requisição para atualizar investimento."""

    nome: str | None = Field(default=None, min_length=1, max_length=255)
    tipo: str | None = Field(default=None, max_length=100)
    valor_investido: Decimal | None = Field(default=None, ge=0)
    valor_atual: Decimal | None = None
    data: date | None = None
    ativo: bool | None = None
    categoria_id: int | None = None
    banco_id: int | None = None


class InvestimentoResponse(BaseModel):
    """Dados do investimento retornados pela API."""

    id: int
    usuario_id: int
    nome: str
    tipo: str | None = None
    valor_investido: Decimal
    valor_atual: Decimal | None = None
    data: date
    ativo: bool
    categoria_id: int | None = None
    banco_id: int | None = None
    criado_em: datetime | None = None
    rentabilidade: Decimal = Decimal("0")

    model_config = {"from_attributes": True}


class ValorAtualUpdate(BaseModel):
    """Corpo da requisição para atualizar valor atual do investimento."""

    valor_atual: Decimal


class DividendoCreate(BaseModel):
    """Corpo da requisição para registrar dividendo."""

    valor: Decimal = Field(gt=0)
    data: date


class DividendoResponse(BaseModel):
    """Dados do dividendo retornados pela API."""

    id: int
    investimento_id: int
    valor: Decimal
    data: date

    model_config = {"from_attributes": True}
