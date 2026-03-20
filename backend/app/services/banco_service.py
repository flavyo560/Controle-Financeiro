"""Serviço de bancos: lógica de negócio para criação com cartão vinculado."""

from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from app.models.banco import Banco
from app.models.cartao import Cartao
from app.models.compra_cartao import CompraCartao
from app.models.pagamento_fatura import PagamentoFatura
from app.schemas.banco import BancoCreate, BancoUpdate


def criar_banco_com_cartao(
    db: Session, usuario_id: int, data: BancoCreate,
) -> Banco:
    """Cria banco e, se tipo=credito, cria cartão vinculado na mesma transação."""
    banco = Banco(
        usuario_id=usuario_id,
        nome=data.nome,
        saldo_inicial=data.saldo_inicial,
        tipo=data.tipo,
    )
    db.add(banco)
    db.flush()

    if data.tipo == "credito":
        try:
            _criar_cartao_vinculado(db, banco, usuario_id, data)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao criar cartão vinculado. Operação revertida.",
            )

    db.commit()
    db.refresh(banco)
    return banco


def atualizar_banco_com_tipo(
    db: Session, banco: Banco, data: BancoUpdate, usuario_id: int,
) -> Banco:
    """Atualiza banco gerenciando mudanças de tipo (debito↔credito)."""
    update_data = data.model_dump(exclude_unset=True)
    novo_tipo = update_data.get("tipo")

    # Mudança de tipo debito → credito
    if novo_tipo == "credito" and banco.tipo == "debito":
        # Validar campos obrigatórios
        limite = update_data.get("limite_total")
        dia_f = update_data.get("dia_fechamento")
        dia_v = update_data.get("dia_vencimento")
        if not limite or limite <= 0:
            raise HTTPException(status_code=422, detail="Limite total deve ser maior que zero para tipo crédito")
        if not dia_f or not (1 <= dia_f <= 31):
            raise HTTPException(status_code=422, detail="Dia de fechamento deve estar entre 1 e 31")
        if not dia_v or not (1 <= dia_v <= 31):
            raise HTTPException(status_code=422, detail="Dia de vencimento deve estar entre 1 e 31")

        banco.tipo = "credito"
        _criar_cartao_vinculado(db, banco, usuario_id, data)

    # Mudança de tipo credito → debito
    elif novo_tipo == "debito" and banco.tipo == "credito":
        if banco.cartao_id:
            saldo = _verificar_saldo_devedor(db, banco.cartao_id)
            if saldo > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Não é possível alterar para débito: cartão vinculado possui saldo devedor de R$ {saldo:.2f}",
                )
            # Desativar cartão vinculado (soft-delete)
            cartao = db.query(Cartao).filter(Cartao.id == banco.cartao_id).first()
            if cartao:
                cartao.status = False
            banco.cartao_id = None
        banco.tipo = "debito"

    # Mesmo tipo credito — propagar campos para cartão
    elif banco.tipo == "credito" and banco.cartao_id and novo_tipo != "debito":
        cartao = db.query(Cartao).filter(Cartao.id == banco.cartao_id).first()
        if cartao:
            for field in ("limite_total", "dia_fechamento", "dia_vencimento", "bandeira"):
                if field in update_data and update_data[field] is not None:
                    setattr(cartao, field, update_data[field])

    # Aplicar demais campos ao banco
    for field in ("nome", "saldo_inicial", "ativo"):
        if field in update_data:
            setattr(banco, field, update_data[field])

    db.commit()
    db.refresh(banco)
    return banco


def _criar_cartao_vinculado(
    db: Session, banco: Banco, usuario_id: int, data,
) -> Cartao:
    """Helper: cria cartão e atualiza banco.cartao_id."""
    cartao = Cartao(
        usuario_id=usuario_id,
        nome=banco.nome,
        limite_total=data.limite_total,
        dia_fechamento=data.dia_fechamento,
        dia_vencimento=data.dia_vencimento,
        bandeira=getattr(data, "bandeira", None),
        status=True,
    )
    db.add(cartao)
    db.flush()
    banco.cartao_id = cartao.id
    return cartao


def _verificar_saldo_devedor(db: Session, cartao_id: int) -> Decimal:
    """Verifica se cartão tem saldo devedor em faturas abertas."""
    total_compras = Decimal(str(
        db.query(sqlfunc.coalesce(sqlfunc.sum(CompraCartao.valor), 0))
        .filter(CompraCartao.cartao_id == cartao_id)
        .scalar()
    ))
    total_pagamentos = Decimal(str(
        db.query(sqlfunc.coalesce(sqlfunc.sum(PagamentoFatura.valor_pago), 0))
        .filter(PagamentoFatura.cartao_id == cartao_id)
        .scalar()
    ))
    return max(total_compras - total_pagamentos, Decimal("0"))
