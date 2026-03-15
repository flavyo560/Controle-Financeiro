"""Serviço de relatórios: lógica de negócio para geração de relatórios."""

from __future__ import annotations

import io
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.abastecimento import Abastecimento
from app.models.categoria import Categoria
from app.models.despesa import Despesa
from app.models.item_orcamento import ItemOrcamento
from app.models.manutencao import Manutencao
from app.models.orcamento import Orcamento
from app.models.receita import Receita
from app.models.veiculo import Veiculo
from app.schemas.relatorio import (
    CategoriaTotal,
    ItemOrcamentoRelatorio,
    RelatorioAnualResponse,
    RelatorioMensalResponse,
    RelatorioOrcamentoAnualResponse,
    RelatorioOrcamentoMensalResponse,
    RelatorioVeiculoResponse,
    TotalMensalOrcamento,
    TotalMensalRelatorio,
)

_ZERO = Decimal("0.00")


# ---------------------------------------------------------------------------
# Relatório Mensal
# ---------------------------------------------------------------------------

def gerar_relatorio_mensal(
    db: Session, usuario_id: int, mes: int, ano: int,
) -> RelatorioMensalResponse:
    """Gera relatório mensal com totais por categoria."""
    # Receitas por categoria
    rows_rec = (
        db.query(
            Receita.categoria_id,
            Categoria.nome.label("categoria_nome"),
            func.sum(Receita.valor).label("total"),
        )
        .join(Categoria, Receita.categoria_id == Categoria.id, isouter=True)
        .filter(
            Receita.usuario_id == usuario_id,
            Receita.ativo.is_(True),
            extract("month", Receita.data) == mes,
            extract("year", Receita.data) == ano,
            Receita.categoria_id.isnot(None),
        )
        .group_by(Receita.categoria_id, Categoria.nome)
        .all()
    )
    receitas = [
        CategoriaTotal(
            categoria_id=r.categoria_id,
            categoria_nome=r.categoria_nome or "Sem categoria",
            valor=Decimal(str(r.total)),
        )
        for r in rows_rec
    ]

    # Despesas por categoria
    rows_desp = (
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
    despesas = [
        CategoriaTotal(
            categoria_id=r.categoria_id,
            categoria_nome=r.categoria_nome or "Sem categoria",
            valor=Decimal(str(r.total)),
        )
        for r in rows_desp
    ]

    total_rec = sum(c.valor for c in receitas) if receitas else _ZERO
    total_desp = sum(c.valor for c in despesas) if despesas else _ZERO

    return RelatorioMensalResponse(
        mes=mes,
        ano=ano,
        receitas=receitas,
        despesas=despesas,
        total_receitas=total_rec,
        total_despesas=total_desp,
        saldo=total_rec - total_desp,
    )


# ---------------------------------------------------------------------------
# Relatório Anual
# ---------------------------------------------------------------------------

def gerar_relatorio_anual(
    db: Session, usuario_id: int, ano: int,
) -> RelatorioAnualResponse:
    """Gera relatório anual com totais mensais e evolução."""
    meses: list[TotalMensalRelatorio] = []
    total_rec_ano = _ZERO
    total_desp_ano = _ZERO

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
        meses.append(TotalMensalRelatorio(
            mes=m, receitas=receitas, despesas=despesas, saldo=receitas - despesas,
        ))
        total_rec_ano += receitas
        total_desp_ano += despesas

    return RelatorioAnualResponse(
        ano=ano,
        meses=meses,
        total_receitas=total_rec_ano,
        total_despesas=total_desp_ano,
        saldo=total_rec_ano - total_desp_ano,
    )


# ---------------------------------------------------------------------------
# Relatório por Veículo
# ---------------------------------------------------------------------------

def gerar_relatorio_veiculo(
    db: Session, usuario_id: int, veiculo_id: int,
) -> RelatorioVeiculoResponse:
    """Gera relatório de custos e consumo de um veículo."""
    veiculo = (
        db.query(Veiculo)
        .filter(Veiculo.id == veiculo_id, Veiculo.usuario_id == usuario_id)
        .first()
    )
    if not veiculo:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Veículo não encontrado",
        )

    # Totais de abastecimentos
    abastecimentos = (
        db.query(Abastecimento)
        .filter(Abastecimento.veiculo_id == veiculo_id)
        .all()
    )
    total_abast = sum(Decimal(str(a.valor)) for a in abastecimentos) if abastecimentos else _ZERO
    total_litros = _ZERO
    total_valor_abast = _ZERO
    for a in abastecimentos:
        if a.litros:
            total_litros += Decimal(str(a.litros))
        total_valor_abast += Decimal(str(a.valor))

    # Totais de manutenções
    manutencoes = (
        db.query(Manutencao)
        .filter(Manutencao.veiculo_id == veiculo_id)
        .all()
    )
    total_manut = sum(Decimal(str(m.valor)) for m in manutencoes) if manutencoes else _ZERO

    # Consumo médio (mesma lógica do frota router)
    com_km = [
        a for a in abastecimentos
        if a.km is not None and a.litros is not None and Decimal(str(a.litros)) > 0
    ]
    com_km.sort(key=lambda a: Decimal(str(a.km)))

    consumo_medio = _ZERO
    total_km = _ZERO
    if len(com_km) >= 2:
        consumos = []
        for i in range(len(com_km) - 1):
            km_diff = Decimal(str(com_km[i + 1].km)) - Decimal(str(com_km[i].km))
            litros_next = Decimal(str(com_km[i + 1].litros))
            if km_diff > 0 and litros_next > 0:
                consumos.append(km_diff / litros_next)
        if consumos:
            consumo_medio = (sum(consumos) / len(consumos)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP,
            )
        total_km = Decimal(str(com_km[-1].km)) - Decimal(str(com_km[0].km))

    # Custo por km
    custo_km = _ZERO
    if total_km > 0:
        custo_km = ((total_abast + total_manut) / total_km).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )

    return RelatorioVeiculoResponse(
        veiculo_id=veiculo_id,
        nome_identificador=veiculo.nome_identificador,
        total_abastecimentos=total_abast,
        total_manutencoes=total_manut,
        total_geral=total_abast + total_manut,
        consumo_medio=consumo_medio,
        custo_por_km=custo_km,
        total_km=total_km,
        total_litros=total_litros,
        quantidade_abastecimentos=len(abastecimentos),
        quantidade_manutencoes=len(manutencoes),
    )


# ---------------------------------------------------------------------------
# Relatório Orçamento Mensal
# ---------------------------------------------------------------------------

def gerar_relatorio_orcamento_mensal(
    db: Session, usuario_id: int, mes: int, ano: int,
) -> RelatorioOrcamentoMensalResponse:
    """Gera relatório de orçamento mensal: planejado vs realizado."""
    orcamento = (
        db.query(Orcamento)
        .filter(Orcamento.usuario_id == usuario_id, Orcamento.ano == ano)
        .first()
    )
    if not orcamento:
        return RelatorioOrcamentoMensalResponse(
            mes=mes, ano=ano, itens=[], total_planejado=_ZERO, total_realizado=_ZERO,
        )

    itens_orc = (
        db.query(ItemOrcamento)
        .join(Categoria, ItemOrcamento.categoria_id == Categoria.id)
        .filter(ItemOrcamento.orcamento_id == orcamento.id, ItemOrcamento.mes == mes)
        .all()
    )

    # Realizados: receitas + despesas por categoria no mês
    realizados_rec = dict(
        db.query(Receita.categoria_id, func.sum(Receita.valor))
        .filter(
            Receita.usuario_id == usuario_id,
            Receita.ativo.is_(True),
            extract("month", Receita.data) == mes,
            extract("year", Receita.data) == ano,
            Receita.categoria_id.isnot(None),
        )
        .group_by(Receita.categoria_id)
        .all()
    )
    realizados_desp = dict(
        db.query(Despesa.categoria_id, func.sum(Despesa.valor))
        .filter(
            Despesa.usuario_id == usuario_id,
            Despesa.ativo.is_(True),
            extract("month", Despesa.data) == mes,
            extract("year", Despesa.data) == ano,
            Despesa.categoria_id.isnot(None),
        )
        .group_by(Despesa.categoria_id)
        .all()
    )

    # Buscar nomes das categorias
    cat_nomes = dict(
        db.query(Categoria.id, Categoria.nome)
        .filter(Categoria.usuario_id == usuario_id)
        .all()
    )

    itens: list[ItemOrcamentoRelatorio] = []
    total_plan = _ZERO
    total_real = _ZERO
    for item in itens_orc:
        planejado = Decimal(str(item.valor_planejado))
        realizado = Decimal(str(realizados_rec.get(item.categoria_id, 0))) + \
                    Decimal(str(realizados_desp.get(item.categoria_id, 0)))
        pct = (realizado / planejado * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        ) if planejado > 0 else _ZERO
        itens.append(ItemOrcamentoRelatorio(
            categoria_id=item.categoria_id,
            categoria_nome=cat_nomes.get(item.categoria_id, "Sem categoria"),
            valor_planejado=planejado,
            valor_realizado=realizado,
            percentual=pct,
        ))
        total_plan += planejado
        total_real += realizado

    return RelatorioOrcamentoMensalResponse(
        mes=mes, ano=ano, itens=itens,
        total_planejado=total_plan, total_realizado=total_real,
    )


# ---------------------------------------------------------------------------
# Relatório Orçamento Anual
# ---------------------------------------------------------------------------

def gerar_relatorio_orcamento_anual(
    db: Session, usuario_id: int, ano: int,
) -> RelatorioOrcamentoAnualResponse:
    """Gera relatório de orçamento anual: planejado vs realizado por mês."""
    orcamento = (
        db.query(Orcamento)
        .filter(Orcamento.usuario_id == usuario_id, Orcamento.ano == ano)
        .first()
    )
    if not orcamento:
        return RelatorioOrcamentoAnualResponse(
            ano=ano, meses=[], total_planejado=_ZERO, total_realizado=_ZERO,
        )

    # Planejado por mês
    planejado_por_mes: dict[int, Decimal] = {}
    itens_orc = (
        db.query(ItemOrcamento)
        .filter(ItemOrcamento.orcamento_id == orcamento.id)
        .all()
    )
    for item in itens_orc:
        planejado_por_mes[item.mes] = planejado_por_mes.get(item.mes, _ZERO) + Decimal(str(item.valor_planejado))

    # Realizado por mês (receitas + despesas)
    realizado_por_mes: dict[int, Decimal] = {}
    for m in range(1, 13):
        rec = Decimal(str(
            db.query(func.coalesce(func.sum(Receita.valor), 0))
            .filter(
                Receita.usuario_id == usuario_id,
                Receita.ativo.is_(True),
                extract("month", Receita.data) == m,
                extract("year", Receita.data) == ano,
            )
            .scalar()
        ))
        desp = Decimal(str(
            db.query(func.coalesce(func.sum(Despesa.valor), 0))
            .filter(
                Despesa.usuario_id == usuario_id,
                Despesa.ativo.is_(True),
                extract("month", Despesa.data) == m,
                extract("year", Despesa.data) == ano,
            )
            .scalar()
        ))
        realizado_por_mes[m] = rec + desp

    meses: list[TotalMensalOrcamento] = []
    total_plan = _ZERO
    total_real = _ZERO
    for m in range(1, 13):
        plan = planejado_por_mes.get(m, _ZERO)
        real = realizado_por_mes.get(m, _ZERO)
        pct = (real / plan * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        ) if plan > 0 else _ZERO
        meses.append(TotalMensalOrcamento(
            mes=m, planejado=plan, realizado=real, percentual=pct,
        ))
        total_plan += plan
        total_real += real

    return RelatorioOrcamentoAnualResponse(
        ano=ano, meses=meses,
        total_planejado=total_plan, total_realizado=total_real,
    )


# ---------------------------------------------------------------------------
# Exportação CSV
# ---------------------------------------------------------------------------

def exportar_csv(
    db: Session, usuario_id: int, tipo: str, mes: int | None, ano: int,
) -> str:
    """Exporta relatório em CSV com UTF-8 BOM e separador ponto-e-vírgula.

    Args:
        tipo: "mensal" ou "anual"
        mes: obrigatório se tipo == "mensal"
        ano: ano do relatório
    """
    BOM = "\ufeff"
    sep = ";"

    if tipo == "mensal":
        if mes is None:
            mes = 1
        rel = gerar_relatorio_mensal(db, usuario_id, mes, ano)
        lines = [BOM + sep.join(["Tipo", "Categoria", "Valor"])]
        for r in rel.receitas:
            lines.append(sep.join(["Receita", r.categoria_nome, str(r.valor)]))
        for d in rel.despesas:
            lines.append(sep.join(["Despesa", d.categoria_nome, str(d.valor)]))
        lines.append(sep.join(["", "Total Receitas", str(rel.total_receitas)]))
        lines.append(sep.join(["", "Total Despesas", str(rel.total_despesas)]))
        lines.append(sep.join(["", "Saldo", str(rel.saldo)]))
    else:
        rel_anual = gerar_relatorio_anual(db, usuario_id, ano)
        lines = [BOM + sep.join(["Mês", "Receitas", "Despesas", "Saldo"])]
        for m in rel_anual.meses:
            lines.append(sep.join([str(m.mes), str(m.receitas), str(m.despesas), str(m.saldo)]))
        lines.append(sep.join(["Total", str(rel_anual.total_receitas), str(rel_anual.total_despesas), str(rel_anual.saldo)]))

    return "\n".join(lines)
