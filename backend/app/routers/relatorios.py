"""Router de relatórios: mensal, anual, veículo, orçamento e exportação CSV."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.schemas.relatorio import (
    RelatorioAnualResponse,
    RelatorioMensalResponse,
    RelatorioOrcamentoAnualResponse,
    RelatorioOrcamentoMensalResponse,
    RelatorioVeiculoResponse,
)
from app.services.relatorio_service import (
    exportar_csv,
    gerar_relatorio_anual,
    gerar_relatorio_mensal,
    gerar_relatorio_orcamento_anual,
    gerar_relatorio_orcamento_mensal,
    gerar_relatorio_veiculo,
)

router = APIRouter()


@router.get("/mensal", response_model=RelatorioMensalResponse)
def relatorio_mensal(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    mes: int = Query(default=None, ge=1, le=12),
    ano: int = Query(default=None, ge=2000, le=2100),
) -> RelatorioMensalResponse:
    """Relatório mensal: receitas e despesas por categoria, saldo."""
    usuario_id = current_user["user_id"]
    hoje = date.today()
    if mes is None:
        mes = hoje.month
    if ano is None:
        ano = hoje.year
    return gerar_relatorio_mensal(db, usuario_id, mes, ano)


@router.get("/anual", response_model=RelatorioAnualResponse)
def relatorio_anual(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: int = Query(default=None, ge=2000, le=2100),
) -> RelatorioAnualResponse:
    """Relatório anual: totais mensais e evolução."""
    usuario_id = current_user["user_id"]
    if ano is None:
        ano = date.today().year
    return gerar_relatorio_anual(db, usuario_id, ano)


@router.get("/veiculo/{veiculo_id}", response_model=RelatorioVeiculoResponse)
def relatorio_veiculo(
    veiculo_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RelatorioVeiculoResponse:
    """Relatório por veículo: custos, consumo médio, custo/km."""
    usuario_id = current_user["user_id"]
    return gerar_relatorio_veiculo(db, usuario_id, veiculo_id)


@router.get("/orcamento/mensal", response_model=RelatorioOrcamentoMensalResponse)
def relatorio_orcamento_mensal(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    mes: int = Query(default=None, ge=1, le=12),
    ano: int = Query(default=None, ge=2000, le=2100),
) -> RelatorioOrcamentoMensalResponse:
    """Relatório de orçamento mensal: planejado vs realizado."""
    usuario_id = current_user["user_id"]
    hoje = date.today()
    if mes is None:
        mes = hoje.month
    if ano is None:
        ano = hoje.year
    return gerar_relatorio_orcamento_mensal(db, usuario_id, mes, ano)


@router.get("/orcamento/anual", response_model=RelatorioOrcamentoAnualResponse)
def relatorio_orcamento_anual(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: int = Query(default=None, ge=2000, le=2100),
) -> RelatorioOrcamentoAnualResponse:
    """Relatório de orçamento anual: planejado vs realizado por mês."""
    usuario_id = current_user["user_id"]
    if ano is None:
        ano = date.today().year
    return gerar_relatorio_orcamento_anual(db, usuario_id, ano)


@router.get("/exportar/csv")
def exportar_relatorio_csv(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    tipo: str = Query(pattern=r"^(mensal|anual)$"),
    ano: int = Query(default=None, ge=2000, le=2100),
    mes: int | None = Query(default=None, ge=1, le=12),
) -> StreamingResponse:
    """Exporta relatório em CSV (UTF-8 BOM, separador ponto-e-vírgula)."""
    usuario_id = current_user["user_id"]
    if ano is None:
        ano = date.today().year

    csv_content = exportar_csv(db, usuario_id, tipo, mes, ano)

    filename = f"relatorio_{tipo}_{ano}"
    if tipo == "mensal" and mes:
        filename += f"_{mes:02d}"
    filename += ".csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
