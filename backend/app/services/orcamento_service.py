"""Serviço de orçamento: lógica de negócio para planejamento financeiro."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.categoria import Categoria
from app.models.despesa import Despesa
from app.models.historico_orcamento import HistoricoOrcamento
from app.models.item_orcamento import ItemOrcamento
from app.models.orcamento import Orcamento
from app.models.receita import Receita
from app.schemas.orcamento import (
    ItemOrcamentoCreate,
    PercentualItem,
    ProjecaoCategoria,
    RealizadoItem,
    SugestaoItem,
    TotalMensal,
)

_ZERO = Decimal("0.00")


# ---------------------------------------------------------------------------
# Criar / Atualizar Item (com histórico automático)
# ---------------------------------------------------------------------------

def criar_ou_atualizar_item(
    db: Session,
    orcamento: Orcamento,
    data: ItemOrcamentoCreate,
    usuario_id: int,
) -> ItemOrcamento:
    """Cria ou atualiza um item de orçamento.

    Se o item já existe e o valor_planejado mudou, registra histórico.
    """
    item = (
        db.query(ItemOrcamento)
        .filter(
            ItemOrcamento.orcamento_id == orcamento.id,
            ItemOrcamento.categoria_id == data.categoria_id,
            ItemOrcamento.mes == data.mes,
        )
        .first()
    )

    if item is not None:
        valor_anterior = Decimal(str(item.valor_planejado))
        valor_novo = Decimal(str(data.valor_planejado))
        if valor_anterior != valor_novo:
            historico = HistoricoOrcamento(
                item_orcamento_id=item.id,
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
                usuario_id=usuario_id,
            )
            db.add(historico)
            item.valor_planejado = data.valor_planejado
        db.commit()
        db.refresh(item)
        return item

    item = ItemOrcamento(
        orcamento_id=orcamento.id,
        categoria_id=data.categoria_id,
        mes=data.mes,
        valor_planejado=data.valor_planejado,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Valores Realizados
# ---------------------------------------------------------------------------

def _obter_realizados_receitas(
    db: Session, usuario_id: int, ano: int,
) -> dict[tuple[int, int], Decimal]:
    """Agrega receitas por (categoria_id, mês) para o ano."""
    rows = (
        db.query(
            Receita.categoria_id,
            extract("month", Receita.data).label("mes"),
            func.sum(Receita.valor).label("total"),
        )
        .filter(
            Receita.usuario_id == usuario_id,
            Receita.ativo.is_(True),
            extract("year", Receita.data) == ano,
            Receita.categoria_id.isnot(None),
        )
        .group_by(Receita.categoria_id, extract("month", Receita.data))
        .all()
    )
    return {(int(r.categoria_id), int(r.mes)): Decimal(str(r.total)) for r in rows}


def _obter_realizados_despesas(
    db: Session, usuario_id: int, ano: int,
) -> dict[tuple[int, int], Decimal]:
    """Agrega despesas por (categoria_id, mês) para o ano."""
    rows = (
        db.query(
            Despesa.categoria_id,
            extract("month", Despesa.data).label("mes"),
            func.sum(Despesa.valor).label("total"),
        )
        .filter(
            Despesa.usuario_id == usuario_id,
            Despesa.ativo.is_(True),
            extract("year", Despesa.data) == ano,
            Despesa.categoria_id.isnot(None),
        )
        .group_by(Despesa.categoria_id, extract("month", Despesa.data))
        .all()
    )
    return {(int(r.categoria_id), int(r.mes)): Decimal(str(r.total)) for r in rows}


def calcular_realizados(
    db: Session, orcamento: Orcamento, usuario_id: int,
) -> list[RealizadoItem]:
    """Retorna valores realizados por categoria e mês."""
    receitas = _obter_realizados_receitas(db, usuario_id, orcamento.ano)
    despesas = _obter_realizados_despesas(db, usuario_id, orcamento.ano)

    # Merge all keys
    all_keys = set(receitas.keys()) | set(despesas.keys())
    result: list[RealizadoItem] = []
    for cat_id, mes in sorted(all_keys):
        valor = receitas.get((cat_id, mes), _ZERO) + despesas.get((cat_id, mes), _ZERO)
        result.append(RealizadoItem(categoria_id=cat_id, mes=mes, valor_realizado=valor))
    return result


def _obter_mapa_realizados(
    db: Session, usuario_id: int, ano: int,
) -> dict[tuple[int, int], Decimal]:
    """Retorna mapa (categoria_id, mes) -> valor_realizado combinando receitas e despesas."""
    receitas = _obter_realizados_receitas(db, usuario_id, ano)
    despesas = _obter_realizados_despesas(db, usuario_id, ano)
    mapa: dict[tuple[int, int], Decimal] = {}
    for key in set(receitas.keys()) | set(despesas.keys()):
        mapa[key] = receitas.get(key, _ZERO) + despesas.get(key, _ZERO)
    return mapa


# ---------------------------------------------------------------------------
# Percentuais de Execução
# ---------------------------------------------------------------------------

def calcular_percentuais(
    db: Session, orcamento: Orcamento, usuario_id: int,
) -> list[PercentualItem]:
    """Calcula percentual de execução (realizado/planejado * 100) para cada item."""
    itens = (
        db.query(ItemOrcamento)
        .filter(ItemOrcamento.orcamento_id == orcamento.id)
        .all()
    )
    realizados = _obter_mapa_realizados(db, usuario_id, orcamento.ano)

    result: list[PercentualItem] = []
    for item in itens:
        planejado = Decimal(str(item.valor_planejado))
        realizado = realizados.get((item.categoria_id, item.mes), _ZERO)
        if planejado > 0:
            percentual = (realizado / planejado * 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP,
            )
        else:
            percentual = Decimal("0.00")
        result.append(PercentualItem(
            categoria_id=item.categoria_id,
            mes=item.mes,
            valor_planejado=planejado,
            valor_realizado=realizado,
            percentual=percentual,
        ))
    return result


# ---------------------------------------------------------------------------
# Totais Mensais
# ---------------------------------------------------------------------------

def _obter_categorias_por_tipo(
    db: Session, usuario_id: int,
) -> tuple[set[int], set[int]]:
    """Retorna conjuntos de IDs de categorias de receita e despesa."""
    cats = (
        db.query(Categoria.id, Categoria.tipo)
        .filter(Categoria.usuario_id == usuario_id)
        .all()
    )
    receita_ids = {c.id for c in cats if c.tipo == "receita"}
    despesa_ids = {c.id for c in cats if c.tipo == "despesa"}
    return receita_ids, despesa_ids


def calcular_totais_mensais(
    db: Session, orcamento: Orcamento, usuario_id: int,
) -> list[TotalMensal]:
    """Calcula totais planejados vs realizados por mês (1-12)."""
    itens = (
        db.query(ItemOrcamento)
        .filter(ItemOrcamento.orcamento_id == orcamento.id)
        .all()
    )
    realizados = _obter_mapa_realizados(db, usuario_id, orcamento.ano)
    receita_ids, despesa_ids = _obter_categorias_por_tipo(db, usuario_id)

    # Build planejado maps
    planejado_rec: dict[int, Decimal] = {}
    planejado_desp: dict[int, Decimal] = {}
    for item in itens:
        val = Decimal(str(item.valor_planejado))
        if item.categoria_id in receita_ids:
            planejado_rec[item.mes] = planejado_rec.get(item.mes, _ZERO) + val
        elif item.categoria_id in despesa_ids:
            planejado_desp[item.mes] = planejado_desp.get(item.mes, _ZERO) + val

    # Build realizado maps from receitas/despesas separately
    real_receitas = _obter_realizados_receitas(db, usuario_id, orcamento.ano)
    real_despesas = _obter_realizados_despesas(db, usuario_id, orcamento.ano)

    result: list[TotalMensal] = []
    for mes in range(1, 13):
        pr = planejado_rec.get(mes, _ZERO)
        pd = planejado_desp.get(mes, _ZERO)
        rr = sum(
            (v for (c, m), v in real_receitas.items() if m == mes),
            _ZERO,
        )
        rd = sum(
            (v for (c, m), v in real_despesas.items() if m == mes),
            _ZERO,
        )
        result.append(TotalMensal(
            mes=mes,
            planejado_receitas=pr,
            planejado_despesas=pd,
            realizado_receitas=rr,
            realizado_despesas=rd,
            saldo_planejado=pr - pd,
            saldo_realizado=rr - rd,
        ))
    return result


# ---------------------------------------------------------------------------
# Projeções
# ---------------------------------------------------------------------------

def calcular_projecoes(
    db: Session, orcamento: Orcamento, usuario_id: int,
) -> tuple[int, list[ProjecaoCategoria]]:
    """Calcula projeções anuais por categoria.

    Projeção = soma_realizada + (média_mensal × meses_restantes).
    Risco = projeção > planejado_anual.

    Returns:
        Tuple of (mes_atual, list of ProjecaoCategoria).
    """
    hoje = date.today()
    mes_atual = hoje.month if hoje.year == orcamento.ano else (12 if hoje.year > orcamento.ano else 0)
    meses_restantes = max(0, 12 - mes_atual)

    itens = (
        db.query(ItemOrcamento)
        .filter(ItemOrcamento.orcamento_id == orcamento.id)
        .all()
    )
    realizados = _obter_mapa_realizados(db, usuario_id, orcamento.ano)

    # Aggregate planejado anual per category
    planejado_anual: dict[int, Decimal] = {}
    for item in itens:
        cat = item.categoria_id
        planejado_anual[cat] = planejado_anual.get(cat, _ZERO) + Decimal(str(item.valor_planejado))

    # Aggregate realizado per category
    realizado_por_cat: dict[int, Decimal] = {}
    for (cat_id, _mes), val in realizados.items():
        realizado_por_cat[cat_id] = realizado_por_cat.get(cat_id, _ZERO) + val

    categorias_ids = set(planejado_anual.keys()) | set(realizado_por_cat.keys())
    result: list[ProjecaoCategoria] = []
    for cat_id in sorted(categorias_ids):
        soma_real = realizado_por_cat.get(cat_id, _ZERO)
        if mes_atual > 0:
            media_mensal = (soma_real / mes_atual).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP,
            )
        else:
            media_mensal = _ZERO
        projecao = soma_real + media_mensal * meses_restantes
        plan_anual = planejado_anual.get(cat_id, _ZERO)
        risco = projecao > plan_anual if plan_anual > 0 else False

        result.append(ProjecaoCategoria(
            categoria_id=cat_id,
            soma_realizada=soma_real,
            media_mensal=media_mensal,
            projecao_anual=projecao,
            planejado_anual=plan_anual,
            risco=risco,
        ))

    return mes_atual, result


# ---------------------------------------------------------------------------
# Sugestões
# ---------------------------------------------------------------------------

def calcular_sugestoes(
    db: Session, orcamento: Orcamento, usuario_id: int,
) -> list[SugestaoItem]:
    """Gera sugestões de ajuste para categorias fora dos limites.

    - >100% de execução consistentemente → sugerir reduzir gasto
    - <50% de execução consistentemente → sugerir realocar
    """
    hoje = date.today()
    mes_atual = hoje.month if hoje.year == orcamento.ano else (12 if hoje.year > orcamento.ano else 0)
    if mes_atual < 2:
        return []  # Need at least 2 months of data

    itens = (
        db.query(ItemOrcamento)
        .filter(ItemOrcamento.orcamento_id == orcamento.id)
        .all()
    )
    realizados = _obter_mapa_realizados(db, usuario_id, orcamento.ano)

    # Group percentuais by category
    cat_percentuais: dict[int, list[Decimal]] = {}
    for item in itens:
        if item.mes > mes_atual:
            continue
        planejado = Decimal(str(item.valor_planejado))
        if planejado <= 0:
            continue
        realizado = realizados.get((item.categoria_id, item.mes), _ZERO)
        pct = (realizado / planejado * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )
        cat_percentuais.setdefault(item.categoria_id, []).append(pct)

    sugestoes: list[SugestaoItem] = []
    for cat_id, pcts in cat_percentuais.items():
        if len(pcts) < 2:
            continue
        media = sum(pcts) / len(pcts)
        media_q = media.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Consistently above 100%
        acima = sum(1 for p in pcts if p > 100)
        if acima >= len(pcts) * 0.5:
            sugestoes.append(SugestaoItem(
                categoria_id=cat_id,
                tipo="reduzir_gasto",
                percentual_medio=media_q,
                mensagem=f"Categoria com execução média de {media_q}%. Considere reduzir gastos ou aumentar o planejado.",
            ))
            continue

        # Consistently below 50%
        abaixo = sum(1 for p in pcts if p < 50)
        if abaixo >= len(pcts) * 0.5:
            sugestoes.append(SugestaoItem(
                categoria_id=cat_id,
                tipo="realocar",
                percentual_medio=media_q,
                mensagem=f"Categoria com execução média de {media_q}%. Considere realocar o orçamento para outras categorias.",
            ))

    return sugestoes


# ---------------------------------------------------------------------------
# Cópia de Orçamento
# ---------------------------------------------------------------------------

def copiar_orcamento(
    db: Session,
    orcamento_origem: Orcamento,
    ano_destino: int,
    usuario_id: int,
) -> Orcamento:
    """Copia orçamento para outro ano, verificando existência de categorias."""
    # Create new orcamento
    novo = Orcamento(
        usuario_id=usuario_id,
        ano=ano_destino,
        status="ativo",
    )
    db.add(novo)
    db.flush()

    # Get active category IDs for the user
    categorias_ativas = {
        c.id
        for c in db.query(Categoria.id).filter(
            Categoria.usuario_id == usuario_id,
            Categoria.ativo.is_(True),
        ).all()
    }

    # Copy items, skipping categories that no longer exist
    itens_origem = (
        db.query(ItemOrcamento)
        .filter(ItemOrcamento.orcamento_id == orcamento_origem.id)
        .all()
    )
    for item in itens_origem:
        if item.categoria_id not in categorias_ativas:
            continue
        novo_item = ItemOrcamento(
            orcamento_id=novo.id,
            categoria_id=item.categoria_id,
            mes=item.mes,
            valor_planejado=item.valor_planejado,
        )
        db.add(novo_item)

    db.commit()
    db.refresh(novo)
    return novo
