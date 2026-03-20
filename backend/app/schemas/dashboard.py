"""Schemas Pydantic para dashboard financeiro."""

from __future__ import annotations

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Saldo por Banco
# ---------------------------------------------------------------------------

class SaldoBanco(BaseModel):
    """Saldo calculado de um banco."""

    banco_id: int
    nome: str
    saldo: float


# ---------------------------------------------------------------------------
# Resumo Mensal
# ---------------------------------------------------------------------------

class ResumoMensal(BaseModel):
    """Resumo financeiro de um mês."""

    mes: int
    ano: int
    total_receitas: float
    total_despesas: float
    saldo: float


# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------

class AlertaDespesa(BaseModel):
    """Alerta de despesa vencida ou vencendo."""

    despesa_id: int
    descricao: str | None = None
    valor: float
    data_vencimento: str | None = None
    tipo: str  # "vencida" ou "vencendo"


# ---------------------------------------------------------------------------
# Distribuição por Categoria (gráfico pizza)
# ---------------------------------------------------------------------------

class DistribuicaoCategoria(BaseModel):
    """Despesas agrupadas por categoria para gráfico pizza."""

    categoria_id: int
    categoria_nome: str
    valor: float
    percentual: float


# ---------------------------------------------------------------------------
# Evolução Mensal (gráfico barras)
# ---------------------------------------------------------------------------

class EvolucaoMensal(BaseModel):
    """Receitas e despesas de um mês para gráfico de barras."""

    mes: int
    receitas: float
    despesas: float


# ---------------------------------------------------------------------------
# Dashboard Completo
# ---------------------------------------------------------------------------

class DashboardResponse(BaseModel):
    """Resposta completa do dashboard."""

    patrimonio: float
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
