"""Serviço de despesas: lógica de negócio para parcelas e recorrentes."""

from __future__ import annotations

import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models.despesa import Despesa
from app.models.despesa_parcelada import DespesaParcelada
from app.models.despesa_recorrente import DespesaRecorrente
from app.schemas.despesa import (
    DespesaParceladaCreate,
    DespesaRecorrenteCreate,
    EditarParcelaRequest,
)


def _add_months(start: date, months: int) -> date:
    """Incrementa *months* meses a partir de *start*, ajustando dia se necessário."""
    month = start.month - 1 + months
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


# ---------------------------------------------------------------------------
# Parcelas
# ---------------------------------------------------------------------------

def criar_despesa_parcelada(
    db: Session,
    data: DespesaParceladaCreate,
    usuario_id: int,
) -> DespesaParcelada:
    """Cria registro pai e gera todas as parcelas na tabela despesas."""

    parcelada = DespesaParcelada(
        usuario_id=usuario_id,
        descricao=data.descricao,
        valor_total=data.valor_total,
        numero_parcelas=data.numero_parcelas,
        data_primeira_parcela=data.data_primeira_parcela,
        categoria_id=data.categoria_id,
        banco_id=data.banco_id,
    )
    db.add(parcelada)
    db.flush()  # garante parcelada.id

    valor_parcela = (data.valor_total / data.numero_parcelas).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP,
    )
    soma_parcelas = valor_parcela * (data.numero_parcelas - 1)
    valor_ultima = data.valor_total - soma_parcelas

    for i in range(1, data.numero_parcelas + 1):
        dt = _add_months(data.data_primeira_parcela, i - 1)
        valor = valor_ultima if i == data.numero_parcelas else valor_parcela
        despesa = Despesa(
            usuario_id=usuario_id,
            descricao=data.descricao,
            valor=valor,
            data=dt,
            categoria_id=data.categoria_id,
            banco_id=data.banco_id,
            pago=False,
            data_vencimento=dt,
            parcela_numero=i,
            parcela_total=data.numero_parcelas,
            despesa_parcelada_id=parcelada.id,
        )
        db.add(despesa)

    db.commit()
    db.refresh(parcelada)
    return parcelada


def editar_parcela(
    db: Session,
    despesa_parcelada_id: int,
    parcela_id: int,
    data: EditarParcelaRequest,
    usuario_id: int,
) -> Despesa | None:
    """Edita uma parcela. Se aplicar_futuras=True, propaga para parcelas seguintes."""

    parcela = (
        db.query(Despesa)
        .filter(
            Despesa.id == parcela_id,
            Despesa.despesa_parcelada_id == despesa_parcelada_id,
            Despesa.usuario_id == usuario_id,
            Despesa.ativo.is_(True),
        )
        .first()
    )
    if not parcela:
        return None

    update_fields = data.model_dump(exclude_unset=True, exclude={"aplicar_futuras"})

    for field, value in update_fields.items():
        setattr(parcela, field, value)

    if data.aplicar_futuras and update_fields:
        futuras = (
            db.query(Despesa)
            .filter(
                Despesa.despesa_parcelada_id == despesa_parcelada_id,
                Despesa.usuario_id == usuario_id,
                Despesa.parcela_numero > parcela.parcela_numero,
                Despesa.ativo.is_(True),
            )
            .all()
        )
        for f in futuras:
            for field, value in update_fields.items():
                setattr(f, field, value)

    db.commit()
    db.refresh(parcela)
    return parcela


def excluir_despesa(db: Session, despesa: Despesa) -> None:
    """Exclui (desativa) uma despesa. Se for última parcela, remove registro pai."""

    despesa.ativo = False

    if despesa.despesa_parcelada_id:
        restantes = (
            db.query(Despesa)
            .filter(
                Despesa.despesa_parcelada_id == despesa.despesa_parcelada_id,
                Despesa.ativo.is_(True),
                Despesa.id != despesa.id,
            )
            .count()
        )
        if restantes == 0:
            parcelada = db.query(DespesaParcelada).get(despesa.despesa_parcelada_id)
            if parcelada:
                db.delete(parcelada)

    db.commit()


# ---------------------------------------------------------------------------
# Recorrentes
# ---------------------------------------------------------------------------

def criar_despesa_recorrente(
    db: Session,
    data: DespesaRecorrenteCreate,
    usuario_id: int,
) -> DespesaRecorrente:
    """Cria uma despesa recorrente."""

    recorrente = DespesaRecorrente(
        usuario_id=usuario_id,
        descricao=data.descricao,
        valor=data.valor,
        dia_mes=data.dia_mes,
        categoria_id=data.categoria_id,
        banco_id=data.banco_id,
        data_inicio=data.data_inicio,
        data_fim=data.data_fim,
        ativa=True,
    )
    db.add(recorrente)
    db.commit()
    db.refresh(recorrente)
    return recorrente


def gerar_lancamentos_recorrentes(
    db: Session,
    usuario_id: int,
) -> list[Despesa]:
    """Gera lançamentos do mês atual para recorrentes ativas sem lançamento."""

    hoje = date.today()

    recorrentes = (
        db.query(DespesaRecorrente)
        .filter(
            DespesaRecorrente.usuario_id == usuario_id,
            DespesaRecorrente.ativa.is_(True),
            DespesaRecorrente.data_inicio <= hoje,
        )
        .all()
    )

    criados: list[Despesa] = []
    for rec in recorrentes:
        if rec.data_fim and rec.data_fim < date(hoje.year, hoje.month, 1):
            continue

        # Verifica se já existe lançamento neste mês
        existe = (
            db.query(Despesa)
            .filter(
                Despesa.despesa_recorrente_id == rec.id,
                Despesa.usuario_id == usuario_id,
                Despesa.ativo.is_(True),
                extract("year", Despesa.data) == hoje.year,
                extract("month", Despesa.data) == hoje.month,
            )
            .first()
        )
        if existe:
            continue

        dia = min(rec.dia_mes, calendar.monthrange(hoje.year, hoje.month)[1])
        data_lancamento = date(hoje.year, hoje.month, dia)

        despesa = Despesa(
            usuario_id=usuario_id,
            descricao=rec.descricao,
            valor=rec.valor,
            data=data_lancamento,
            categoria_id=rec.categoria_id,
            banco_id=rec.banco_id,
            pago=False,
            data_vencimento=data_lancamento,
            despesa_recorrente_id=rec.id,
        )
        db.add(despesa)
        criados.append(despesa)

    if criados:
        db.commit()
        for d in criados:
            db.refresh(d)

    return criados


def desativar_recorrente(
    db: Session,
    recorrente_id: int,
    usuario_id: int,
) -> DespesaRecorrente | None:
    """Desativa uma despesa recorrente, preservando lançamentos existentes."""

    recorrente = (
        db.query(DespesaRecorrente)
        .filter(
            DespesaRecorrente.id == recorrente_id,
            DespesaRecorrente.usuario_id == usuario_id,
        )
        .first()
    )
    if not recorrente:
        return None

    recorrente.ativa = False
    db.commit()
    db.refresh(recorrente)
    return recorrente
