"""Router de despesas: CRUD simples, parceladas e recorrentes."""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.despesa import Despesa
from app.models.despesa_parcelada import DespesaParcelada
from app.models.despesa_recorrente import DespesaRecorrente
from app.schemas.common import PaginatedResponse
from app.schemas.despesa import (
    DespesaCreate,
    DespesaParceladaCreate,
    DespesaParceladaResponse,
    DespesaRecorrenteCreate,
    DespesaRecorrenteResponse,
    DespesaRecorrenteUpdate,
    DespesaResponse,
    DespesaUpdate,
    EditarParcelaRequest,
    PagarDespesaRequest,
)
from app.services.despesa_service import (
    criar_despesa_parcelada,
    criar_despesa_recorrente,
    desativar_recorrente,
    editar_parcela,
    excluir_despesa,
    gerar_lancamentos_recorrentes,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# CRUD simples
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedResponse[DespesaResponse])
def listar_despesas(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    categoria_id: int | None = None,
    banco_id: int | None = None,
    pago: bool | None = None,
) -> PaginatedResponse[DespesaResponse]:
    """Lista despesas do usuário com paginação e filtros."""
    usuario_id = current_user["user_id"]
    query = db.query(Despesa).filter(
        Despesa.usuario_id == usuario_id,
        Despesa.ativo.is_(True),
    )

    if mes is not None:
        query = query.filter(extract("month", Despesa.data) == mes)
    if ano is not None:
        query = query.filter(extract("year", Despesa.data) == ano)
    if categoria_id is not None:
        query = query.filter(Despesa.categoria_id == categoria_id)
    if banco_id is not None:
        query = query.filter(Despesa.banco_id == banco_id)
    if pago is not None:
        query = query.filter(Despesa.pago == pago)

    total = query.count()
    offset = (page - 1) * per_page
    despesas = query.order_by(Despesa.data.desc()).offset(offset).limit(per_page).all()

    return PaginatedResponse(
        items=[DespesaResponse.model_validate(d) for d in despesas],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.post("/", response_model=DespesaResponse, status_code=201)
def criar_despesa(
    data: DespesaCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DespesaResponse:
    """Cria uma nova despesa simples."""
    usuario_id = current_user["user_id"]
    despesa = Despesa(
        usuario_id=usuario_id,
        descricao=data.descricao,
        valor=data.valor,
        data=data.data,
        categoria_id=data.categoria_id,
        banco_id=data.banco_id,
        data_vencimento=data.data_vencimento,
        pago=False,
    )
    db.add(despesa)
    db.commit()
    db.refresh(despesa)
    return DespesaResponse.model_validate(despesa)


@router.put("/{despesa_id}", response_model=DespesaResponse)
def atualizar_despesa(
    despesa_id: int,
    data: DespesaUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DespesaResponse:
    """Atualiza dados de uma despesa."""
    usuario_id = current_user["user_id"]
    despesa = (
        db.query(Despesa)
        .filter(Despesa.id == despesa_id, Despesa.usuario_id == usuario_id, Despesa.ativo.is_(True))
        .first()
    )
    if not despesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(despesa, field, value)

    db.commit()
    db.refresh(despesa)
    return DespesaResponse.model_validate(despesa)


@router.delete("/{despesa_id}", status_code=204)
def deletar_despesa(
    despesa_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui (desativa) uma despesa. Cascateia para parcelada se última."""
    usuario_id = current_user["user_id"]
    despesa = (
        db.query(Despesa)
        .filter(Despesa.id == despesa_id, Despesa.usuario_id == usuario_id, Despesa.ativo.is_(True))
        .first()
    )
    if not despesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    excluir_despesa(db, despesa)


@router.patch("/{despesa_id}/pagar", response_model=DespesaResponse)
def pagar_despesa(
    despesa_id: int,
    data: PagarDespesaRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DespesaResponse:
    """Marca uma despesa como paga."""
    usuario_id = current_user["user_id"]
    despesa = (
        db.query(Despesa)
        .filter(Despesa.id == despesa_id, Despesa.usuario_id == usuario_id, Despesa.ativo.is_(True))
        .first()
    )
    if not despesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    despesa.pago = True
    despesa.data_pagamento = data.data_pagamento
    db.commit()
    db.refresh(despesa)
    return DespesaResponse.model_validate(despesa)


# ---------------------------------------------------------------------------
# Parceladas
# ---------------------------------------------------------------------------

@router.post("/parceladas", response_model=DespesaParceladaResponse, status_code=201)
def criar_parcelada(
    data: DespesaParceladaCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DespesaParceladaResponse:
    """Cria despesa parcelada e gera parcelas automaticamente."""
    usuario_id = current_user["user_id"]
    parcelada = criar_despesa_parcelada(db, data, usuario_id)
    return DespesaParceladaResponse.model_validate(parcelada)


@router.get("/parceladas", response_model=list[DespesaParceladaResponse])
def listar_parceladas(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DespesaParceladaResponse]:
    """Lista despesas parceladas do usuário."""
    usuario_id = current_user["user_id"]
    parceladas = (
        db.query(DespesaParcelada)
        .filter(DespesaParcelada.usuario_id == usuario_id)
        .order_by(DespesaParcelada.criado_em.desc())
        .all()
    )
    return [DespesaParceladaResponse.model_validate(p) for p in parceladas]


@router.put("/parceladas/{parcelada_id}/parcela/{parcela_id}", response_model=DespesaResponse)
def editar_parcela_endpoint(
    parcelada_id: int,
    parcela_id: int,
    data: EditarParcelaRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DespesaResponse:
    """Edita uma parcela individual, opcionalmente propagando para futuras."""
    usuario_id = current_user["user_id"]
    parcela = editar_parcela(db, parcelada_id, parcela_id, data, usuario_id)
    if not parcela:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela não encontrada")
    return DespesaResponse.model_validate(parcela)


# ---------------------------------------------------------------------------
# Recorrentes
# ---------------------------------------------------------------------------

@router.post("/recorrentes", response_model=DespesaRecorrenteResponse, status_code=201)
def criar_recorrente(
    data: DespesaRecorrenteCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DespesaRecorrenteResponse:
    """Cria uma despesa recorrente."""
    usuario_id = current_user["user_id"]
    recorrente = criar_despesa_recorrente(db, data, usuario_id)
    return DespesaRecorrenteResponse.model_validate(recorrente)


@router.get("/recorrentes", response_model=list[DespesaRecorrenteResponse])
def listar_recorrentes(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DespesaRecorrenteResponse]:
    """Lista despesas recorrentes e gera lançamentos do mês se necessário."""
    usuario_id = current_user["user_id"]
    # Auto-gera lançamentos do mês atual
    gerar_lancamentos_recorrentes(db, usuario_id)

    recorrentes = (
        db.query(DespesaRecorrente)
        .filter(DespesaRecorrente.usuario_id == usuario_id)
        .order_by(DespesaRecorrente.criado_em.desc())
        .all()
    )
    return [DespesaRecorrenteResponse.model_validate(r) for r in recorrentes]


@router.put("/recorrentes/{recorrente_id}", response_model=DespesaRecorrenteResponse)
def atualizar_recorrente(
    recorrente_id: int,
    data: DespesaRecorrenteUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DespesaRecorrenteResponse:
    """Atualiza dados de uma despesa recorrente."""
    usuario_id = current_user["user_id"]
    recorrente = (
        db.query(DespesaRecorrente)
        .filter(
            DespesaRecorrente.id == recorrente_id,
            DespesaRecorrente.usuario_id == usuario_id,
        )
        .first()
    )
    if not recorrente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa recorrente não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recorrente, field, value)

    db.commit()
    db.refresh(recorrente)
    return DespesaRecorrenteResponse.model_validate(recorrente)


@router.patch("/recorrentes/{recorrente_id}/desativar", response_model=DespesaRecorrenteResponse)
def desativar_recorrente_endpoint(
    recorrente_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DespesaRecorrenteResponse:
    """Desativa uma despesa recorrente, preservando lançamentos existentes."""
    usuario_id = current_user["user_id"]
    recorrente = desativar_recorrente(db, recorrente_id, usuario_id)
    if not recorrente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa recorrente não encontrada")
    return DespesaRecorrenteResponse.model_validate(recorrente)


@router.delete("/recorrentes/{recorrente_id}", status_code=204)
def excluir_recorrente(
    recorrente_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui uma despesa recorrente."""
    usuario_id = current_user["user_id"]
    recorrente = (
        db.query(DespesaRecorrente)
        .filter(
            DespesaRecorrente.id == recorrente_id,
            DespesaRecorrente.usuario_id == usuario_id,
        )
        .first()
    )
    if not recorrente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa recorrente não encontrada")

    db.delete(recorrente)
    db.commit()
