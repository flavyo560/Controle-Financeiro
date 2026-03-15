"""Router de bancos: CRUD com saldo calculado."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.banco import Banco
from app.models.despesa import Despesa
from app.models.receita import Receita
from app.models.transferencia import Transferencia
from app.schemas.banco import (
    BancoCreate,
    BancoResponse,
    BancoUpdate,
    SaldoDetalhadoResponse,
)

router = APIRouter()


def _calcular_saldo(db: Session, banco: Banco, usuario_id: int) -> Decimal:
    """Calcula saldo do banco: saldo_inicial + receitas - despesas pagas."""
    total_receitas = (
        db.query(func.coalesce(func.sum(Receita.valor), 0))
        .filter(
            Receita.banco_id == banco.id,
            Receita.usuario_id == usuario_id,
            Receita.ativo.is_(True),
        )
        .scalar()
    )

    total_despesas = (
        db.query(func.coalesce(func.sum(Despesa.valor), 0))
        .filter(
            Despesa.banco_id == banco.id,
            Despesa.usuario_id == usuario_id,
            Despesa.pago.is_(True),
            Despesa.ativo.is_(True),
        )
        .scalar()
    )

    saldo_inicial = banco.saldo_inicial or Decimal("0")
    return Decimal(str(saldo_inicial)) + Decimal(str(total_receitas)) - Decimal(str(total_despesas))


@router.get("/", response_model=list[BancoResponse])
def listar_bancos(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[BancoResponse]:
    """Lista todos os bancos do usuário com saldo calculado."""
    usuario_id = current_user["user_id"]
    bancos = db.query(Banco).filter(Banco.usuario_id == usuario_id).all()

    result = []
    for banco in bancos:
        saldo = _calcular_saldo(db, banco, usuario_id)
        resp = BancoResponse.model_validate(banco)
        resp.saldo_calculado = saldo
        result.append(resp)
    return result


@router.post("/", response_model=BancoResponse, status_code=201)
def criar_banco(
    data: BancoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BancoResponse:
    """Cria um novo banco para o usuário."""
    usuario_id = current_user["user_id"]
    banco = Banco(
        usuario_id=usuario_id,
        nome=data.nome,
        saldo_inicial=data.saldo_inicial,
    )
    db.add(banco)
    db.commit()
    db.refresh(banco)
    resp = BancoResponse.model_validate(banco)
    resp.saldo_calculado = banco.saldo_inicial or Decimal("0")
    return resp


@router.put("/{banco_id}", response_model=BancoResponse)
def atualizar_banco(
    banco_id: int,
    data: BancoUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BancoResponse:
    """Atualiza dados de um banco do usuário."""
    usuario_id = current_user["user_id"]
    banco = (
        db.query(Banco)
        .filter(Banco.id == banco_id, Banco.usuario_id == usuario_id)
        .first()
    )
    if not banco:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banco não encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(banco, field, value)

    db.commit()
    db.refresh(banco)
    resp = BancoResponse.model_validate(banco)
    resp.saldo_calculado = _calcular_saldo(db, banco, usuario_id)
    return resp


@router.delete("/{banco_id}", status_code=204)
def excluir_banco(
    banco_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui (desativa) um banco do usuário."""
    usuario_id = current_user["user_id"]
    banco = (
        db.query(Banco)
        .filter(Banco.id == banco_id, Banco.usuario_id == usuario_id)
        .first()
    )
    if not banco:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banco não encontrado")

    banco.ativo = False
    db.commit()


@router.get("/{banco_id}/saldo", response_model=SaldoDetalhadoResponse)
def saldo_banco(
    banco_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SaldoDetalhadoResponse:
    """Retorna saldo detalhado de um banco."""
    usuario_id = current_user["user_id"]
    banco = (
        db.query(Banco)
        .filter(Banco.id == banco_id, Banco.usuario_id == usuario_id)
        .first()
    )
    if not banco:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banco não encontrado")

    total_receitas = Decimal(str(
        db.query(func.coalesce(func.sum(Receita.valor), 0))
        .filter(Receita.banco_id == banco.id, Receita.usuario_id == usuario_id, Receita.ativo.is_(True))
        .scalar()
    ))

    total_despesas = Decimal(str(
        db.query(func.coalesce(func.sum(Despesa.valor), 0))
        .filter(Despesa.banco_id == banco.id, Despesa.usuario_id == usuario_id, Despesa.pago.is_(True), Despesa.ativo.is_(True))
        .scalar()
    ))

    total_transf_entrada = Decimal(str(
        db.query(func.coalesce(func.sum(Transferencia.valor), 0))
        .filter(Transferencia.banco_destino_id == banco.id, Transferencia.usuario_id == usuario_id)
        .scalar()
    ))

    total_transf_saida = Decimal(str(
        db.query(func.coalesce(func.sum(Transferencia.valor), 0))
        .filter(Transferencia.banco_origem_id == banco.id, Transferencia.usuario_id == usuario_id)
        .scalar()
    ))

    saldo_inicial = Decimal(str(banco.saldo_inicial or 0))
    saldo = saldo_inicial + total_receitas - total_despesas + total_transf_entrada - total_transf_saida

    return SaldoDetalhadoResponse(
        banco_id=banco.id,
        nome=banco.nome,
        saldo_inicial=saldo_inicial,
        total_receitas=total_receitas,
        total_despesas_pagas=total_despesas,
        total_transferencias_entrada=total_transf_entrada,
        total_transferencias_saida=total_transf_saida,
        saldo_calculado=saldo,
    )
