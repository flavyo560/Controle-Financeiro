"""Schemas Pydantic para orçamento e planejamento financeiro."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Orçamento
# ---------------------------------------------------------------------------

class OrcamentoCreate(BaseModel):
    """Corpo da requisição para criar orçamento anual."""

    ano: int = Field(ge=2000, le=2100)


class OrcamentoStatusUpdate(BaseModel):
    """Corpo da requisição para atualizar status do orçamento."""

    status: str = Field(pattern=r"^(ativo|inativo)$")


class OrcamentoResponse(BaseModel):
    """Dados do orçamento retornados pela API."""

    id: int
    usuario_id: int
    ano: int
    status: str
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Item de Orçamento
# ---------------------------------------------------------------------------

class ItemOrcamentoCreate(BaseModel):
    """Corpo da requisição para criar/atualizar item de orçamento."""

    categoria_id: int
    mes: int = Field(ge=1, le=12)
    valor_planejado: Decimal = Field(ge=0)


class ItemOrcamentoResponse(BaseModel):
    """Dados do item de orçamento retornados pela API."""

    id: int
    orcamento_id: int
    categoria_id: int
    mes: int
    valor_planejado: Decimal
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Histórico de Orçamento
# ---------------------------------------------------------------------------

class HistoricoOrcamentoResponse(BaseModel):
    """Registro de alteração de item de orçamento."""

    id: int
    item_orcamento_id: int
    data_alteracao: datetime
    valor_anterior: Decimal
    valor_novo: Decimal
    usuario_id: int | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Valores Realizados
# ---------------------------------------------------------------------------

class RealizadoItem(BaseModel):
    """Valor realizado de uma categoria em um mês."""

    categoria_id: int
    mes: int
    valor_realizado: Decimal


class RealizadosResponse(BaseModel):
    """Valores realizados por categoria e mês."""

    orcamento_id: int
    ano: int
    itens: list[RealizadoItem]


# ---------------------------------------------------------------------------
# Percentuais de Execução
# ---------------------------------------------------------------------------

class PercentualItem(BaseModel):
    """Percentual de execução de um item de orçamento."""

    categoria_id: int
    mes: int
    valor_planejado: Decimal
    valor_realizado: Decimal
    percentual: Decimal


class PercentuaisResponse(BaseModel):
    """Percentuais de execução por categoria e mês."""

    orcamento_id: int
    ano: int
    itens: list[PercentualItem]


# ---------------------------------------------------------------------------
# Totais Mensais
# ---------------------------------------------------------------------------

class TotalMensal(BaseModel):
    """Totais planejados e realizados de um mês."""

    mes: int
    planejado_receitas: Decimal
    planejado_despesas: Decimal
    realizado_receitas: Decimal
    realizado_despesas: Decimal
    saldo_planejado: Decimal
    saldo_realizado: Decimal


class TotaisMensaisResponse(BaseModel):
    """Totais planejados vs realizados por mês."""

    orcamento_id: int
    ano: int
    meses: list[TotalMensal]


# ---------------------------------------------------------------------------
# Projeções
# ---------------------------------------------------------------------------

class ProjecaoCategoria(BaseModel):
    """Projeção de gasto anual para uma categoria."""

    categoria_id: int
    soma_realizada: Decimal
    media_mensal: Decimal
    projecao_anual: Decimal
    planejado_anual: Decimal
    risco: bool


class ProjecaoResponse(BaseModel):
    """Projeções de gastos futuros por categoria."""

    orcamento_id: int
    ano: int
    mes_atual: int
    categorias: list[ProjecaoCategoria]


# ---------------------------------------------------------------------------
# Sugestões
# ---------------------------------------------------------------------------

class SugestaoItem(BaseModel):
    """Sugestão de ajuste para uma categoria."""

    categoria_id: int
    tipo: str  # "reduzir_gasto" ou "realocar"
    percentual_medio: Decimal
    mensagem: str


class SugestaoResponse(BaseModel):
    """Sugestões de ajuste de orçamento."""

    orcamento_id: int
    ano: int
    sugestoes: list[SugestaoItem]
