"""Dependencies de controle de acesso por plano e perfil."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.services.subscription_service import SubscriptionService


def require_plus(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Verifica se o usuário tem acesso ao Plano Plus. Admins passam direto."""
    perfil = current_user.get("perfil")
    if perfil == "admin":
        return current_user
    plan = SubscriptionService.get_effective_plan(db, current_user["user_id"])
    if plan not in ("plus", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recurso disponível apenas no Plano Plus",
        )
    return current_user


def require_admin(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Verifica se o usuário tem perfil 'admin'."""
    if current_user.get("perfil") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user
