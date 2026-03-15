"""Schemas Pydantic para transferências."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class TransferenciaCreate(BaseModel):
    """Corpo da requisição para criar transferência."""

    banco_origem_id: int
    banco_destino_id: int
    valor: Decimal = Field(gt=0)
    data: date
    descricao: str | None = None


class TransferenciaUpdate(BaseModel):
    """Corpo da requisição para atualizar transferência."""

    banco_origem_id: int | None = None
    banco_destino_id: int | None = None
    valor: Decimal | None = Field(default=None, gt=0)
    data: date | None = None
    descricao: str | None = None


class TransferenciaResponse(BaseModel):
    """Dados da transferência retornados pela API."""

    id: int
    banco_origem_id: int | None = None
    banco_destino_id: int | None = None
    valor: Decimal
    data: date
    descricao: str | None = None

    model_config = {"from_attributes": True}
