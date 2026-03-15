"""Serviço de dashboard: lógica de negócio para painel financeiro."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.banco import Banco
from app.models.categoria import Categoria
from app.models.despesa import Despesa
from app.models.receita import Receita
from app.schemas.dashboard import (
    AlertaDespesa,
    DashboardResponse,
    DistribuicaoCategoria,
    DistribuicaoCategoriaResponse,
    EvolucaoMensal,
    EvolucaoMensalResponse,
    ResumoMensal,
    SaldoBanco,
)

_ZERO = Decimal("0.00")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _calcular_saldo_banco(db: Session, banco: Banco, usuario_id: int) -> Decimal:
    """Calcula saldo de um banco: saldo_inicial + receitas - despesas pagas."""
    total_receitas = Decimal(str(
        db.query(func.coalesce(func.sum(Receita.valor), 0))
        .filter(
            Receita.banco_id == banco.id,
            Receita.usuario_id == usuario_id,
            Receita.ativo.is_(True),
        )
        .scalar()
    ))
    total_despesas = Decimal(str(
        db.query(func.coalesce(func.sum(Despesa.valor), 0))
        .filter(
            Despesa.banco_id == banco.id,
            Despesa.usuario_id == usuario_id,
            Despesa.pago.is_(True),
            Despesa.ativo.is_(True),
        )
        .scalar()
    ))
    saldo_inicial = Decimal(str(banco.saldo_inicial or 0))
    return saldo_inicial + total_receitas - total_despesas


# ---------------------------------------------------------------------------
# Dashboard Completo
# ---------------------------------------------------------------------------

def obter_dashboard(
    db: Session, usuario_id: int, mes: int, ano: int,
) -> DashboardResponse:
    """Retorna dados completos do dashboard."""
    # Saldos dos bancos ativos
    bancos = (
        db.query(Banco)
        .filter(Banco.usuario_id == usuario_id, Banco.ativo.is_(True))
        .all()
    )
    saldos: list[SaldoBanco] = []
    patrimonio = _ZERO
    for banco in bancos:
        saldo = _calcular_saldo_banco(db, banco, usuario_id)
        saldos.append(SaldoBanco(banco_id=banco.id, nome=banco.nome, saldo=saldo))
        patrimonio += saldo

    # Resumo mensal
    total_receitas = Decimal(str(
        db.query(func.coalesce(func.sum(Receita.valor), 0))
        .filter(
            Receita.usuario_id == usuario_id,
            Receita.ativo.is_(True),
            extract("month", Receita.data) == mes,
            extract("year", Receita.data) == ano,
        )
        .scalar()
    ))
    total_despesas = Decimal(str(
        db.query(func.coalesce(func.sum(Despesa.valor), 0))
        .filter(
            Despesa.usuario_id == usuario_id,
            Despesa.ativo.is_(True),
            extract("month", Despesa.data) == mes,
            extract("year", Despesa.data) == ano,
        )
        .scalar()
    ))
    resumo = ResumoMensal(
        mes=mes,
        ano=ano,
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        saldo=total_receitas - total_despesas,
    )

    # Alertas
    hoje = date.today()
    alertas = _obter_alertas(db, usuario_id, hoje)

    return DashboardResponse(
        patrimonio=patrimonio,
        saldos_bancos=saldos,
        resumo_mensal=resumo,
        alertas=alertas,
    )


def _obter_alertas(
    db: Session, usuario_id: int, hoje: date,
) -> list[AlertaDespesa]:
    """Retorna alertas de despesas vencidas e vencendo no mês."""
    alertas: list[AlertaDespesa] = []

    # Despesas vencidas (data_vencimento < hoje, pago=false)
    vencidas = (
        db.query(Despesa)
        .filter(
            Despesa.usuario_id == usuario_id,
            Despesa.ativo.is_(True),
            Despesa.pago.is_(False),
            Despesa.data_vencimento.isnot(None),
            Despesa.data_vencimento < hoje,
        )
        .all()
    )
    for d in vencidas:
        alertas.append(AlertaDespesa(
            despesa_id=d.id,
            descricao=d.descricao,
            valor=Decimal(str(d.valor)),
            data_vencimento=str(d.data_vencimento) if d.data_vencimento else None,
            tipo="vencida",
        ))

    # Despesas vencendo no mês atual (data_vencimento no mês corrente, pago=false)
    vencendo = (
        db.query(Despesa)
        .filter(
            Despesa.usuario_id == usuario_id,
            Despesa.ativo.is_(True),
            Despesa.pago.is_(False),
            Despesa.data_vencimento.isnot(None),
            Despesa.data_vencimento >= hoje,
            extract("month", Despesa.data_vencimento) == hoje.month,
            extract("year", Despesa.data_vencimento) == hoje.year,
        )
        .all()
    )
    for d in vencendo:
        alertas.append(AlertaDespesa(
            despesa_id=d.id,
            descricao=d.descricao,
            valor=Decimal(str(d.valor)),
            data_vencimento=str(d.data_vencimento) if d.data_vencimento else None,
            tipo="vencendo",
        ))

    return alertas


# ---------------------------------------------------------------------------
# Distribuição por Categoria
# ---------------------------------------------------------------------------

def obter_despesas_por_categoria(
    db: Session, usuario_id: int, mes: int, ano: int,
) -> DistribuicaoCategoriaResponse:
    """Retorna distribuição de despesas por categoria para gráfico pizza."""
    rows = (
        db.query(
            Despesa.categoria_id,
            Categoria.nome.label("categoria_nome"),
            func.sum(Despesa.valor).label("total"),
        )
        .join(Categoria, Despesa.categoria_id == Categoria.id, isouter=True)
        .filter(
            Despesa.usuario_id == usuario_id,
            Despesa.ativo.is_(True),
            extract("month", Despesa.data) == mes,
            extract("year", Despesa.data) == ano,
            Despesa.categoria_id.isnot(None),
        )
        .group_by(Despesa.categoria_id, Categoria.nome)
        .all()
    )

    total_geral = sum(Decimal(str(r.total)) for r in rows) if rows else _ZERO
    categorias: list[DistribuicaoCategoria] = []
    for r in rows:
        valor = Decimal(str(r.total))
        pct = (valor / total_geral * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        ) if total_geral > 0 else _ZERO
        categorias.append(DistribuicaoCategoria(
            categoria_id=r.categoria_id,
            categoria_nome=r.categoria_nome or "Sem categoria",
            valor=valor,
            percentual=pct,
        ))

    return DistribuicaoCategoriaResponse(mes=mes, ano=ano, categorias=categorias)


# ---------------------------------------------------------------------------
# Evolução Mensal
# ---------------------------------------------------------------------------

def obter_evolucao_mensal(
    db: Session, usuario_id: int, ano: int,
) -> EvolucaoMensalResponse:
    """Retorna evolução de receitas/despesas por mês para gráfico de barras."""
    meses: list[EvolucaoMensal] = []
    for m in range(1, 13):
        receitas = Decimal(str(
            db.query(func.coalesce(func.sum(Receita.valor), 0))
            .filter(
                Receita.usuario_id == usuario_id,
                Receita.ativo.is_(True),
                extract("month", Receita.data) == m,
                extract("year", Receita.data) == ano,
            )
            .scalar()
        ))
        despesas = Decimal(str(
            db.query(func.coalesce(func.sum(Despesa.valor), 0))
            .filter(
                Despesa.usuario_id == usuario_id,
                Despesa.ativo.is_(True),
                extract("month", Despesa.data) == m,
                extract("year", Despesa.data) == ano,
            )
            .scalar()
        ))
        meses.append(EvolucaoMensal(mes=m, receitas=receitas, despesas=despesas))

    return EvolucaoMensalResponse(ano=ano, meses=meses)
