"""Schemas Pydantic para relatórios financeiros."""

from __future__ import annotations

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Relatório Mensal
# ---------------------------------------------------------------------------

class CategoriaTotal(BaseModel):
    """Total de uma categoria em um relatório."""

    categoria_id: int
    categoria_nome: str
    valor: float


class RelatorioMensalResponse(BaseModel):
    """Relatório mensal: receitas e despesas por categoria."""

    mes: int
    ano: int
    receitas: list[CategoriaTotal]
    despesas: list[CategoriaTotal]
    total_receitas: float
    total_despesas: float
    saldo: float


# ---------------------------------------------------------------------------
# Relatório Anual
# ---------------------------------------------------------------------------

class TotalMensalRelatorio(BaseModel):
    """Totais de receitas e despesas de um mês no relatório anual."""

    mes: int
    receitas: float
    despesas: float
    saldo: float


class RelatorioAnualResponse(BaseModel):
    """Relatório anual: totais mensais e evolução."""

    ano: int
    meses: list[TotalMensalRelatorio]
    total_receitas: float
    total_despesas: float
    saldo: float


# ---------------------------------------------------------------------------
# Relatório por Veículo
# ---------------------------------------------------------------------------

class RelatorioVeiculoResponse(BaseModel):
    """Relatório de custos e consumo de um veículo."""

    veiculo_id: int
    nome_identificador: str
    total_abastecimentos: float
    total_manutencoes: float
    total_geral: float
    consumo_medio: float
    custo_por_km: float
    total_km: float
    total_litros: float
    quantidade_abastecimentos: int
    quantidade_manutencoes: int


# ---------------------------------------------------------------------------
# Relatório Orçamento Mensal
# ---------------------------------------------------------------------------

class ItemOrcamentoRelatorio(BaseModel):
    """Item de orçamento com planejado vs realizado."""

    categoria_id: int
    categoria_nome: str
    valor_planejado: float
    valor_realizado: float
    percentual: float


class RelatorioOrcamentoMensalResponse(BaseModel):
    """Relatório de orçamento mensal: planejado vs realizado."""

    mes: int
    ano: int
    itens: list[ItemOrcamentoRelatorio]
    total_planejado: float
    total_realizado: float


# ---------------------------------------------------------------------------
# Relatório Orçamento Anual
# ---------------------------------------------------------------------------

class TotalMensalOrcamento(BaseModel):
    """Totais de orçamento de um mês."""

    mes: int
    planejado: float
    realizado: float
    percentual: float


class RelatorioOrcamentoAnualResponse(BaseModel):
    """Relatório de orçamento anual."""

    ano: int
    meses: list[TotalMensalOrcamento]
    total_planejado: float
    total_realizado: float
