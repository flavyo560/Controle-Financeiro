"""Router administrativo: gestão de usuários, planos e trial."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.middleware.plano import require_admin
from app.schemas.admin import (
    AdminUsuarioResponse,
    ConcederPlanoRequest,
    EstenderTrialRequest,
    ResetarSenhaRequest,
)
from app.services.admin_service import AdminService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/usuarios", response_model=list[AdminUsuarioResponse])
def listar_usuarios(
    db: Annotated[Session, Depends(get_db)],
) -> list[AdminUsuarioResponse]:
    """Lista todos os usuários com dados de assinatura e trial."""
    users = AdminService.list_users(db)
    return [AdminUsuarioResponse(**u) for u in users]


@router.get("/usuarios/{user_id}", response_model=AdminUsuarioResponse)
def detalhe_usuario(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> AdminUsuarioResponse:
    """Retorna detalhes de um usuário específico."""
    user = AdminService.get_user_detail(db, user_id)
    return AdminUsuarioResponse(**user)


@router.post("/usuarios/{user_id}/conceder-plano")
def conceder_plano(
    user_id: int,
    data: ConcederPlanoRequest,
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Concede plano manualmente a um usuário (sem Stripe)."""
    admin_id = current_user["user_id"]
    AdminService.grant_plan(db, user_id, data.plano, data.ciclo, admin_id)
    return {"detail": "Plano concedido com sucesso"}


@router.post("/usuarios/{user_id}/revogar")
def revogar_assinatura(
    user_id: int,
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Revoga assinatura de um usuário imediatamente."""
    admin_id = current_user["user_id"]
    AdminService.revoke_subscription(db, user_id, admin_id)
    return {"detail": "Assinatura revogada"}


@router.post("/usuarios/{user_id}/estender-trial")
def estender_trial(
    user_id: int,
    data: EstenderTrialRequest,
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Estende ou concede trial a um usuário."""
    admin_id = current_user["user_id"]
    AdminService.extend_trial(db, user_id, data.dias, admin_id)
    return {"detail": "Trial atualizado"}


@router.post("/usuarios/{user_id}/resetar-senha")
def resetar_senha(
    user_id: int,
    data: ResetarSenhaRequest,
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Reseta a senha de um usuário (admin only)."""
    from app.services.auth_service import _hash_bcrypt, get_user_by_id

    user = get_user_by_id(db, user_id)
    user.senha_hash_bcrypt = _hash_bcrypt(data.nova_senha)
    user.senha_hash = None
    db.commit()
    return {"detail": f"Senha do usuário {user.nome} resetada com sucesso"}
