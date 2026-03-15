"""Schemas Pydantic para despesas (simples, parceladas, recorrentes)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Despesa simples
# ---------------------------------------------------------------------------

class DespesaCreate(BaseModel):
    """Corpo da requisição para criar despesa simples."""

    descricao: str | None = None
    valor: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    data: date
    categoria_id: int | None = None
    banco_id: int | None = None
    data_vencimento: date | None = None


class DespesaUpdate(BaseModel):
    """Corpo da requisição para atualizar despesa."""

    descricao: str | None = None
    valor: Decimal | None = Field(default=None, gt=0, max_digits=15, decimal_places=2)
    data: date | None = None
    categoria_id: int | None = None
    banco_id: int | None = None
    data_vencimento: date | None = None


class DespesaResponse(BaseModel):
    """Dados da despesa retornados pela API."""

    id: int
    descricao: str | None = None
    valor: Decimal
    data: date
    categoria_id: int | None = None
    banco_id: int | None = None
    pago: bool
    data_vencimento: date | None = None
    data_pagamento: date | None = None
    parcela_numero: int | None = None
    parcela_total: int | None = None
    despesa_parcelada_id: int | None = None
    despesa_recorrente_id: int | None = None
    cartao_id: int | None = None
    mes_fatura: str | None = None
    ativo: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Pagar despesa
# ---------------------------------------------------------------------------

class PagarDespesaRequest(BaseModel):
    """Corpo da requisição para marcar despesa como paga."""

    data_pagamento: date


# ---------------------------------------------------------------------------
# Despesa parcelada
# ---------------------------------------------------------------------------

class DespesaParceladaCreate(BaseModel):
    """Corpo da requisição para criar despesa parcelada."""

    descricao: str = Field(min_length=1, max_length=255)
    valor_total: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    numero_parcelas: int = Field(ge=2, le=120)
    data_primeira_parcela: date
    categoria_id: int | None = None
    banco_id: int | None = None


class DespesaParceladaResponse(BaseModel):
    """Dados da despesa parcelada retornados pela API."""

    id: int
    descricao: str
    valor_total: Decimal
    numero_parcelas: int
    data_primeira_parcela: date
    categoria_id: int | None = None
    banco_id: int | None = None
    criado_em: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Despesa recorrente
# ---------------------------------------------------------------------------

class DespesaRecorrenteCreate(BaseModel):
    """Corpo da requisição para criar despesa recorrente."""

    descricao: str = Field(min_length=1, max_length=255)
    valor: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    dia_mes: int = Field(ge=1, le=31)
    categoria_id: int | None = None
    banco_id: int | None = None
    data_inicio: date
    data_fim: date | None = None


class DespesaRecorrenteUpdate(BaseModel):
    """Corpo da requisição para atualizar despesa recorrente."""

    descricao: str | None = Field(default=None, min_length=1, max_length=255)
    valor: Decimal | None = Field(default=None, gt=0, max_digits=15, decimal_places=2)
    dia_mes: int | None = Field(default=None, ge=1, le=31)
    categoria_id: int | None = None
    banco_id: int | None = None
    data_fim: date | None = None


class DespesaRecorrenteResponse(BaseModel):
    """Dados da despesa recorrente retornados pela API."""

    id: int
    descricao: str
    valor: Decimal
    dia_mes: int
    categoria_id: int | None = None
    banco_id: int | None = None
    data_inicio: date
    data_fim: date | None = None
    ativa: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Editar parcela
# ---------------------------------------------------------------------------

class EditarParcelaRequest(BaseModel):
    """Corpo da requisição para editar uma parcela individual."""

    descricao: str | None = None
    valor: Decimal | None = Field(default=None, gt=0, max_digits=15, decimal_places=2)
    data: date | None = None
    categoria_id: int | None = None
    banco_id: int | None = None
    data_vencimento: date | None = None
    aplicar_futuras: bool = False
