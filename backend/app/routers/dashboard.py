"""Router de dashboard: painel financeiro com patrimônio, alertas e gráficos."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.schemas.dashboard import (
    DashboardResponse,
    DistribuicaoCategoriaResponse,
    EvolucaoMensalResponse,
)
from app.services.dashboard_service import (
    obter_dashboard,
    obter_despesas_por_categoria,
    obter_evolucao_mensal,
)

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
def dashboard(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    mes: int = Query(default=None, ge=1, le=12),
    ano: int = Query(default=None, ge=2000, le=2100),
) -> DashboardResponse:
    """Retorna dashboard completo: patrimônio, saldos, resumo mensal, alertas."""
    usuario_id = current_user["user_id"]
    hoje = date.today()
    if mes is None:
        mes = hoje.month
    if ano is None:
        ano = hoje.year
    return obter_dashboard(db, usuario_id, mes, ano)


@router.get("/despesas-por-categoria", response_model=DistribuicaoCategoriaResponse)
def despesas_por_categoria(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    mes: int = Query(default=None, ge=1, le=12),
    ano: int = Query(default=None, ge=2000, le=2100),
) -> DistribuicaoCategoriaResponse:
    """Retorna distribuição de despesas por categoria (gráfico pizza)."""
    usuario_id = current_user["user_id"]
    hoje = date.today()
    if mes is None:
        mes = hoje.month
    if ano is None:
        ano = hoje.year
    return obter_despesas_por_categoria(db, usuario_id, mes, ano)


@router.get("/evolucao-mensal", response_model=EvolucaoMensalResponse)
def evolucao_mensal(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: int = Query(default=None, ge=2000, le=2100),
) -> EvolucaoMensalResponse:
    """Retorna evolução de receitas/despesas por mês (gráfico barras)."""
    usuario_id = current_user["user_id"]
    if ano is None:
        ano = date.today().year
    return obter_evolucao_mensal(db, usuario_id, ano)
