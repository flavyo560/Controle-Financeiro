"""Schemas Pydantic para dashboard financeiro."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Saldo por Banco
# ---------------------------------------------------------------------------

class SaldoBanco(BaseModel):
    """Saldo calculado de um banco."""

    banco_id: int
    nome: str
    saldo: Decimal


# ---------------------------------------------------------------------------
# Resumo Mensal
# ---------------------------------------------------------------------------

class ResumoMensal(BaseModel):
    """Resumo financeiro de um mês."""

    mes: int
    ano: int
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal


# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------

class AlertaDespesa(BaseModel):
    """Alerta de despesa vencida ou vencendo."""

    despesa_id: int
    descricao: str | None = None
    valor: Decimal
    data_vencimento: str | None = None
    tipo: str  # "vencida" ou "vencendo"


# ---------------------------------------------------------------------------
# Distribuição por Categoria (gráfico pizza)
# ---------------------------------------------------------------------------

class DistribuicaoCategoria(BaseModel):
    """Despesas agrupadas por categoria para gráfico pizza."""

    categoria_id: int
    categoria_nome: str
    valor: Decimal
    percentual: Decimal


# ---------------------------------------------------------------------------
# Evolução Mensal (gráfico barras)
# ---------------------------------------------------------------------------

class EvolucaoMensal(BaseModel):
    """Receitas e despesas de um mês para gráfico de barras."""

    mes: int
    receitas: Decimal
    despesas: Decimal


# ---------------------------------------------------------------------------
# Dashboard Completo
# ---------------------------------------------------------------------------

class DashboardResponse(BaseModel):
    """Resposta completa do dashboard."""

    patrimonio: Decimal
    saldos_bancos: list[SaldoBanco]
    resumo_mensal: ResumoMensal
    alertas: list[AlertaDespesa]


class DistribuicaoCategoriaResponse(BaseModel):
    """Resposta de distribuição de despesas por categoria."""

    mes: int
    ano: int
    categorias: list[DistribuicaoCategoria]


class EvolucaoMensalResponse(BaseModel):
    """Resposta de evolução mensal de receitas/despesas."""

    ano: int
    meses: list[EvolucaoMensal]
