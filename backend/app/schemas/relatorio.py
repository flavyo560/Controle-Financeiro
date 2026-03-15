"""Schemas Pydantic para relatórios financeiros."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Relatório Mensal
# ---------------------------------------------------------------------------

class CategoriaTotal(BaseModel):
    """Total de uma categoria em um relatório."""

    categoria_id: int
    categoria_nome: str
    valor: Decimal


class RelatorioMensalResponse(BaseModel):
    """Relatório mensal: receitas e despesas por categoria."""

    mes: int
    ano: int
    receitas: list[CategoriaTotal]
    despesas: list[CategoriaTotal]
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal


# ---------------------------------------------------------------------------
# Relatório Anual
# ---------------------------------------------------------------------------

class TotalMensalRelatorio(BaseModel):
    """Totais de receitas e despesas de um mês no relatório anual."""

    mes: int
    receitas: Decimal
    despesas: Decimal
    saldo: Decimal


class RelatorioAnualResponse(BaseModel):
    """Relatório anual: totais mensais e evolução."""

    ano: int
    meses: list[TotalMensalRelatorio]
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal


# ---------------------------------------------------------------------------
# Relatório por Veículo
# ---------------------------------------------------------------------------

class RelatorioVeiculoResponse(BaseModel):
    """Relatório de custos e consumo de um veículo."""

    veiculo_id: int
    nome_identificador: str
    total_abastecimentos: Decimal
    total_manutencoes: Decimal
    total_geral: Decimal
    consumo_medio: Decimal
    custo_por_km: Decimal
    total_km: Decimal
    total_litros: Decimal
    quantidade_abastecimentos: int
    quantidade_manutencoes: int


# ---------------------------------------------------------------------------
# Relatório Orçamento Mensal
# ---------------------------------------------------------------------------

class ItemOrcamentoRelatorio(BaseModel):
    """Item de orçamento com planejado vs realizado."""

    categoria_id: int
    categoria_nome: str
    valor_planejado: Decimal
    valor_realizado: Decimal
    percentual: Decimal


class RelatorioOrcamentoMensalResponse(BaseModel):
    """Relatório de orçamento mensal: planejado vs realizado."""

    mes: int
    ano: int
    itens: list[ItemOrcamentoRelatorio]
    total_planejado: Decimal
    total_realizado: Decimal


# ---------------------------------------------------------------------------
# Relatório Orçamento Anual
# ---------------------------------------------------------------------------

class TotalMensalOrcamento(BaseModel):
    """Totais de orçamento de um mês."""

    mes: int
    planejado: Decimal
    realizado: Decimal
    percentual: Decimal


class RelatorioOrcamentoAnualResponse(BaseModel):
    """Relatório de orçamento anual."""

    ano: int
    meses: list[TotalMensalOrcamento]
    total_planejado: Decimal
    total_realizado: Decimal
