"""Router de categorias: CRUD com filtro por tipo."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaUpdate

router = APIRouter()


@router.get("/", response_model=list[CategoriaResponse])
def listar_categorias(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    tipo: str | None = Query(default=None, pattern=r"^(receita|despesa)$"),
) -> list[CategoriaResponse]:
    """Lista categorias do usuário, opcionalmente filtradas por tipo."""
    usuario_id = current_user["user_id"]
    query = db.query(Categoria).filter(Categoria.usuario_id == usuario_id)
    if tipo:
        query = query.filter(Categoria.tipo == tipo)
    categorias = query.all()
    return [CategoriaResponse.model_validate(c) for c in categorias]


@router.post("/", response_model=CategoriaResponse, status_code=201)
def criar_categoria(
    data: CategoriaCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CategoriaResponse:
    """Cria uma nova categoria para o usuário."""
    usuario_id = current_user["user_id"]
    categoria = Categoria(
        usuario_id=usuario_id,
        nome=data.nome,
        tipo=data.tipo,
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return CategoriaResponse.model_validate(categoria)


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def atualizar_categoria(
    categoria_id: int,
    data: CategoriaUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CategoriaResponse:
    """Atualiza dados de uma categoria do usuário."""
    usuario_id = current_user["user_id"]
    categoria = (
        db.query(Categoria)
        .filter(Categoria.id == categoria_id, Categoria.usuario_id == usuario_id)
        .first()
    )
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(categoria, field, value)

    db.commit()
    db.refresh(categoria)
    return CategoriaResponse.model_validate(categoria)


@router.delete("/{categoria_id}", status_code=204)
def excluir_categoria(
    categoria_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui (desativa) uma categoria do usuário."""
    usuario_id = current_user["user_id"]
    categoria = (
        db.query(Categoria)
        .filter(Categoria.id == categoria_id, Categoria.usuario_id == usuario_id)
        .first()
    )
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")

    categoria.ativo = False
    db.commit()
