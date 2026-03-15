"""Router de receitas: CRUD paginado com filtros."""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.receita import Receita
from app.schemas.common import PaginatedResponse
from app.schemas.receita import ReceitaCreate, ReceitaResponse, ReceitaUpdate

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ReceitaResponse])
def listar_receitas(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    categoria_id: int | None = None,
    banco_id: int | None = None,
) -> PaginatedResponse[ReceitaResponse]:
    """Lista receitas do usuário com paginação e filtros."""
    usuario_id = current_user["user_id"]
    query = db.query(Receita).filter(
        Receita.usuario_id == usuario_id,
        Receita.ativo.is_(True),
    )

    if mes is not None:
        query = query.filter(extract("month", Receita.data) == mes)
    if ano is not None:
        query = query.filter(extract("year", Receita.data) == ano)
    if categoria_id is not None:
        query = query.filter(Receita.categoria_id == categoria_id)
    if banco_id is not None:
        query = query.filter(Receita.banco_id == banco_id)

    total = query.count()
    offset = (page - 1) * per_page
    receitas = query.order_by(Receita.data.desc()).offset(offset).limit(per_page).all()

    return PaginatedResponse(
        items=[ReceitaResponse.model_validate(r) for r in receitas],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.post("/", response_model=ReceitaResponse, status_code=201)
def criar_receita(
    data: ReceitaCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReceitaResponse:
    """Cria uma nova receita para o usuário."""
    usuario_id = current_user["user_id"]
    receita = Receita(
        usuario_id=usuario_id,
        descricao=data.descricao,
        valor=data.valor,
        data=data.data,
        categoria_id=data.categoria_id,
        banco_id=data.banco_id,
    )
    db.add(receita)
    db.commit()
    db.refresh(receita)
    return ReceitaResponse.model_validate(receita)


@router.put("/{receita_id}", response_model=ReceitaResponse)
def atualizar_receita(
    receita_id: int,
    data: ReceitaUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReceitaResponse:
    """Atualiza dados de uma receita do usuário."""
    usuario_id = current_user["user_id"]
    receita = (
        db.query(Receita)
        .filter(Receita.id == receita_id, Receita.usuario_id == usuario_id, Receita.ativo.is_(True))
        .first()
    )
    if not receita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receita não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(receita, field, value)

    db.commit()
    db.refresh(receita)
    return ReceitaResponse.model_validate(receita)


@router.delete("/{receita_id}", status_code=204)
def excluir_receita(
    receita_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui (desativa) uma receita do usuário."""
    usuario_id = current_user["user_id"]
    receita = (
        db.query(Receita)
        .filter(Receita.id == receita_id, Receita.usuario_id == usuario_id, Receita.ativo.is_(True))
        .first()
    )
    if not receita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receita não encontrada")

    receita.ativo = False
    db.commit()
