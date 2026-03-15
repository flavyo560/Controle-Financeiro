"""Schemas Pydantic para receitas."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ReceitaCreate(BaseModel):
    """Corpo da requisição para criar receita."""

    descricao: str | None = None
    valor: Decimal = Field(gt=0)
    data: date
    categoria_id: int | None = None
    banco_id: int | None = None


class ReceitaUpdate(BaseModel):
    """Corpo da requisição para atualizar receita."""

    descricao: str | None = None
    valor: Decimal | None = Field(default=None, gt=0)
    data: date | None = None
    categoria_id: int | None = None
    banco_id: int | None = None


class ReceitaResponse(BaseModel):
    """Dados da receita retornados pela API."""

    id: int
    descricao: str | None = None
    valor: Decimal
    data: date
    categoria_id: int | None = None
    banco_id: int | None = None
    ativo: bool

    model_config = {"from_attributes": True}
