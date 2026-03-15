"""Router de transferências: CRUD com transação atômica."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.banco import Banco
from app.models.transferencia import Transferencia
from app.schemas.transferencia import (
    TransferenciaCreate,
    TransferenciaResponse,
    TransferenciaUpdate,
)

router = APIRouter()


def _validar_bancos(
    db: Session, usuario_id: int, banco_origem_id: int, banco_destino_id: int,
) -> tuple[Banco, Banco]:
    """Valida que ambos os bancos existem e pertencem ao usuário."""
    if banco_origem_id == banco_destino_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Banco de origem e destino devem ser diferentes",
        )

    origem = (
        db.query(Banco)
        .filter(Banco.id == banco_origem_id, Banco.usuario_id == usuario_id)
        .first()
    )
    if not origem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banco de origem não encontrado",
        )

    destino = (
        db.query(Banco)
        .filter(Banco.id == banco_destino_id, Banco.usuario_id == usuario_id)
        .first()
    )
    if not destino:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banco de destino não encontrado",
        )

    return origem, destino


@router.get("/", response_model=list[TransferenciaResponse])
def listar_transferencias(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TransferenciaResponse]:
    """Lista todas as transferências do usuário."""
    usuario_id = current_user["user_id"]
    transferencias = (
        db.query(Transferencia)
        .filter(Transferencia.usuario_id == usuario_id)
        .order_by(Transferencia.data.desc())
        .all()
    )
    return [TransferenciaResponse.model_validate(t) for t in transferencias]


@router.post("/", response_model=TransferenciaResponse, status_code=201)
def criar_transferencia(
    data: TransferenciaCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TransferenciaResponse:
    """Cria transferência entre bancos (transação atômica)."""
    usuario_id = current_user["user_id"]

    # Validar bancos dentro da mesma transação
    _validar_bancos(db, usuario_id, data.banco_origem_id, data.banco_destino_id)

    # Criar registro de transferência (atômico na mesma sessão)
    transferencia = Transferencia(
        usuario_id=usuario_id,
        banco_origem_id=data.banco_origem_id,
        banco_destino_id=data.banco_destino_id,
        valor=data.valor,
        data=data.data,
        descricao=data.descricao,
    )
    db.add(transferencia)
    db.commit()
    db.refresh(transferencia)
    return TransferenciaResponse.model_validate(transferencia)


@router.put("/{transferencia_id}", response_model=TransferenciaResponse)
def atualizar_transferencia(
    transferencia_id: int,
    data: TransferenciaUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TransferenciaResponse:
    """Atualiza dados de uma transferência do usuário."""
    usuario_id = current_user["user_id"]
    transferencia = (
        db.query(Transferencia)
        .filter(Transferencia.id == transferencia_id, Transferencia.usuario_id == usuario_id)
        .first()
    )
    if not transferencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transferência não encontrada",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Se bancos estão sendo alterados, validar
    new_origem = update_data.get("banco_origem_id", transferencia.banco_origem_id)
    new_destino = update_data.get("banco_destino_id", transferencia.banco_destino_id)
    if "banco_origem_id" in update_data or "banco_destino_id" in update_data:
        _validar_bancos(db, usuario_id, new_origem, new_destino)

    for field, value in update_data.items():
        setattr(transferencia, field, value)

    db.commit()
    db.refresh(transferencia)
    return TransferenciaResponse.model_validate(transferencia)


@router.delete("/{transferencia_id}", status_code=204)
def excluir_transferencia(
    transferencia_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui uma transferência do usuário."""
    usuario_id = current_user["user_id"]
    transferencia = (
        db.query(Transferencia)
        .filter(Transferencia.id == transferencia_id, Transferencia.usuario_id == usuario_id)
        .first()
    )
    if not transferencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transferência não encontrada",
        )

    db.delete(transferencia)
    db.commit()
