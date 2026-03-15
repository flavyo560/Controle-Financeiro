"""Serviço de cartões de crédito: lógica de negócio para compras, faturas e limites."""

from __future__ import annotations

import calendar
import time
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from app.models.cartao import Cartao
from app.models.compra_cartao import CompraCartao
from app.models.despesa import Despesa
from app.models.pagamento_fatura import PagamentoFatura
from app.schemas.cartao import (
    CartaoUpdate,
    CompraCartaoCreate,
    CompraParceladaCreate,
    PagamentoFaturaCreate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_months(year: int, month: int, months: int) -> tuple[int, int]:
    """Incrementa *months* meses a partir de (year, month). Retorna (new_year, new_month)."""
    m = month - 1 + months
    new_year = year + m // 12
    new_month = m % 12 + 1
    return new_year, new_month


def calcular_mes_fatura(data_compra: date, dia_fechamento: int) -> str:
    """Calcula o mes_fatura no formato 'YYYY-MM'.

    Se data_compra.day <= dia_fechamento → fatura do mesmo mês.
    Se data_compra.day > dia_fechamento → fatura do mês seguinte.
    """
    if data_compra.day <= dia_fechamento:
        return f"{data_compra.year:04d}-{data_compra.month:02d}"
    else:
        year, month = _add_months(data_compra.year, data_compra.month, 1)
        return f"{year:04d}-{month:02d}"


def calcular_limite_utilizado(db: Session, cartao_id: int) -> Decimal:
    """Calcula limite_utilizado = SUM(compras) - SUM(pagamentos)."""
    total_compras = (
        db.query(sqlfunc.coalesce(sqlfunc.sum(CompraCartao.valor), 0))
        .filter(CompraCartao.cartao_id == cartao_id)
        .scalar()
    )
    total_pagamentos = (
        db.query(sqlfunc.coalesce(sqlfunc.sum(PagamentoFatura.valor_pago), 0))
        .filter(PagamentoFatura.cartao_id == cartao_id)
        .scalar()
    )
    utilizado = Decimal(str(total_compras)) - Decimal(str(total_pagamentos))
    return max(utilizado, Decimal("0"))


# ---------------------------------------------------------------------------
# Atualização de cartão (com validação de limite)
# ---------------------------------------------------------------------------

def atualizar_cartao(
    db: Session,
    cartao: Cartao,
    data: CartaoUpdate,
) -> Cartao:
    """Atualiza cartão, rejeitando redução de limite abaixo do utilizado."""
    update_data = data.model_dump(exclude_unset=True)

    if "limite_total" in update_data:
        novo_limite = update_data["limite_total"]
        limite_utilizado = calcular_limite_utilizado(db, cartao.id)
        if novo_limite < limite_utilizado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Novo limite (R$ {novo_limite}) não pode ser menor "
                    f"que o utilizado (R$ {limite_utilizado})"
                ),
            )

    for field, value in update_data.items():
        setattr(cartao, field, value)

    db.commit()
    db.refresh(cartao)
    return cartao


# ---------------------------------------------------------------------------
# Compra à vista
# ---------------------------------------------------------------------------

def registrar_compra_avista(
    db: Session,
    cartao: Cartao,
    data: CompraCartaoCreate,
) -> CompraCartao:
    """Registra compra à vista no cartão, calculando mes_fatura automaticamente."""
    mes_fatura = calcular_mes_fatura(data.data_compra, cartao.dia_fechamento)

    compra = CompraCartao(
        cartao_id=cartao.id,
        descricao=data.descricao,
        valor=data.valor,
        data_compra=data.data_compra,
        categoria_id=data.categoria_id,
        mes_fatura=mes_fatura,
    )
    db.add(compra)
    db.commit()
    db.refresh(compra)
    return compra


# ---------------------------------------------------------------------------
# Compra parcelada
# ---------------------------------------------------------------------------

def registrar_compra_parcelada(
    db: Session,
    cartao: Cartao,
    data: CompraParceladaCreate,
) -> list[CompraCartao]:
    """Registra compra parcelada, gerando parcelas em meses consecutivos."""
    mes_fatura_inicial = calcular_mes_fatura(data.data_compra, cartao.dia_fechamento)
    ano_ini, mes_ini = (int(x) for x in mes_fatura_inicial.split("-"))

    valor_parcela = (data.valor_total / data.total_parcelas).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP,
    )
    soma_parcelas = valor_parcela * (data.total_parcelas - 1)
    valor_ultima = data.valor_total - soma_parcelas

    # Identificador único para agrupar parcelas da mesma compra
    compra_parcelada_id = int(time.time() * 1000)

    compras: list[CompraCartao] = []
    for i in range(1, data.total_parcelas + 1):
        year, month = _add_months(ano_ini, mes_ini, i - 1)
        mf = f"{year:04d}-{month:02d}"
        valor = valor_ultima if i == data.total_parcelas else valor_parcela

        compra = CompraCartao(
            cartao_id=cartao.id,
            descricao=data.descricao,
            valor=valor,
            data_compra=data.data_compra,
            categoria_id=data.categoria_id,
            mes_fatura=mf,
            parcela_atual=i,
            total_parcelas=data.total_parcelas,
            compra_parcelada_id=compra_parcelada_id,
        )
        db.add(compra)
        compras.append(compra)

    db.commit()
    for c in compras:
        db.refresh(c)
    return compras


# ---------------------------------------------------------------------------
# Fatura
# ---------------------------------------------------------------------------

def obter_fatura(
    db: Session,
    cartao: Cartao,
    mes_fatura: str,
) -> dict:
    """Retorna detalhes da fatura de um mês específico."""
    compras = (
        db.query(CompraCartao)
        .filter(
            CompraCartao.cartao_id == cartao.id,
            CompraCartao.mes_fatura == mes_fatura,
        )
        .order_by(CompraCartao.data_compra)
        .all()
    )

    valor_total = sum(c.valor for c in compras) if compras else Decimal("0")

    total_pago = (
        db.query(sqlfunc.coalesce(sqlfunc.sum(PagamentoFatura.valor_pago), 0))
        .filter(
            PagamentoFatura.cartao_id == cartao.id,
            PagamentoFatura.mes_fatura == mes_fatura,
        )
        .scalar()
    )
    valor_pago = Decimal(str(total_pago))
    saldo_devedor = max(valor_total - valor_pago, Decimal("0"))

    # Data de vencimento: dia_vencimento no mês da fatura
    ano_f, mes_f = (int(x) for x in mes_fatura.split("-"))
    dia_venc = min(cartao.dia_vencimento, calendar.monthrange(ano_f, mes_f)[1])
    data_vencimento = date(ano_f, mes_f, dia_venc)

    # Status
    if valor_total == 0:
        fatura_status = "paga_total"
    elif saldo_devedor == 0:
        fatura_status = "paga_total"
    elif valor_pago > 0:
        if date.today() > data_vencimento:
            fatura_status = "vencida"
        else:
            fatura_status = "paga_parcial"
    else:
        if date.today() > data_vencimento:
            fatura_status = "vencida"
        else:
            fatura_status = "pendente"

    return {
        "compras": compras,
        "valor_total": valor_total,
        "valor_pago": valor_pago,
        "saldo_devedor": saldo_devedor,
        "data_vencimento": data_vencimento,
        "status": fatura_status,
    }


def listar_faturas(
    db: Session,
    cartao: Cartao,
) -> list[str]:
    """Lista todos os meses de fatura distintos para um cartão."""
    meses = (
        db.query(CompraCartao.mes_fatura)
        .filter(CompraCartao.cartao_id == cartao.id)
        .distinct()
        .order_by(CompraCartao.mes_fatura.desc())
        .all()
    )
    return [m[0] for m in meses]


# ---------------------------------------------------------------------------
# Pagamento de fatura
# ---------------------------------------------------------------------------

def pagar_fatura(
    db: Session,
    cartao: Cartao,
    mes_fatura: str,
    data: PagamentoFaturaCreate,
    usuario_id: int,
) -> PagamentoFatura:
    """Registra pagamento de fatura e cria despesa correspondente no banco."""
    # Criar despesa correspondente no banco selecionado
    despesa = Despesa(
        usuario_id=usuario_id,
        descricao=f"Pagamento fatura {cartao.nome} - {mes_fatura}",
        valor=data.valor_pago,
        data=data.data_pagamento,
        banco_id=data.banco_id,
        pago=True,
        data_pagamento=data.data_pagamento,
        cartao_id=cartao.id,
        mes_fatura=mes_fatura,
    )
    db.add(despesa)
    db.flush()

    # Criar registro de pagamento de fatura
    pagamento = PagamentoFatura(
        cartao_id=cartao.id,
        mes_fatura=mes_fatura,
        valor_pago=data.valor_pago,
        data_pagamento=data.data_pagamento,
        banco_id=data.banco_id,
        despesa_id=despesa.id,
    )
    db.add(pagamento)
    db.commit()
    db.refresh(pagamento)
    return pagamento
