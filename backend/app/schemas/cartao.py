"""Schemas Pydantic para cartões de crédito, compras, faturas e pagamentos."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Cartão
# ---------------------------------------------------------------------------

class CartaoCreate(BaseModel):
    """Corpo da requisição para criar cartão de crédito."""

    nome: str = Field(min_length=1, max_length=255)
    limite_total: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    dia_fechamento: int = Field(ge=1, le=31)
    dia_vencimento: int = Field(ge=1, le=31)
    bandeira: str | None = Field(default=None, max_length=50)


class CartaoUpdate(BaseModel):
    """Corpo da requisição para atualizar cartão de crédito."""

    nome: str | None = Field(default=None, min_length=1, max_length=255)
    limite_total: Decimal | None = Field(default=None, gt=0, max_digits=15, decimal_places=2)
    dia_fechamento: int | None = Field(default=None, ge=1, le=31)
    dia_vencimento: int | None = Field(default=None, ge=1, le=31)
    bandeira: str | None = Field(default=None, max_length=50)


class CartaoResponse(BaseModel):
    """Dados do cartão retornados pela API."""

    id: int
    nome: str
    bandeira: str | None = None
    limite_total: Decimal
    dia_fechamento: int
    dia_vencimento: int
    status: bool
    limite_utilizado: Decimal = Decimal("0")
    limite_disponivel: Decimal = Decimal("0")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Compra no cartão
# ---------------------------------------------------------------------------

class CompraCartaoCreate(BaseModel):
    """Corpo da requisição para registrar compra à vista no cartão."""

    descricao: str = Field(min_length=1, max_length=255)
    valor: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    data_compra: date
    categoria_id: int | None = None


class CompraParceladaCreate(BaseModel):
    """Corpo da requisição para registrar compra parcelada no cartão."""

    descricao: str = Field(min_length=1, max_length=255)
    valor_total: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    total_parcelas: int = Field(ge=2, le=120)
    data_compra: date
    categoria_id: int | None = None


class CompraCartaoResponse(BaseModel):
    """Dados da compra no cartão retornados pela API."""

    id: int
    cartao_id: int
    descricao: str
    valor: Decimal
    data_compra: date
    categoria_id: int | None = None
    mes_fatura: str
    parcela_atual: int | None = None
    total_parcelas: int | None = None
    compra_parcelada_id: int | None = None
    criado_em: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Fatura
# ---------------------------------------------------------------------------

class FaturaResponse(BaseModel):
    """Detalhes de uma fatura mensal do cartão."""

    compras: list[CompraCartaoResponse]
    valor_total: Decimal
    valor_pago: Decimal
    saldo_devedor: Decimal
    data_vencimento: date
    status: str  # pendente, paga_parcial, paga_total, vencida


# ---------------------------------------------------------------------------
# Pagamento de fatura
# ---------------------------------------------------------------------------

class PagamentoFaturaCreate(BaseModel):
    """Corpo da requisição para registrar pagamento de fatura."""

    valor_pago: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    data_pagamento: date
    banco_id: int


class PagamentoFaturaResponse(BaseModel):
    """Dados do pagamento de fatura retornados pela API."""

    id: int
    cartao_id: int
    mes_fatura: str
    valor_pago: Decimal
    data_pagamento: date
    banco_id: int
    despesa_id: int | None = None
    criado_em: datetime

    model_config = {"from_attributes": True}
