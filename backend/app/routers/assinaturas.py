"""Router de assinaturas: status, checkout, portal e cancelamento."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.schemas.assinatura import (
    AssinaturaResponse,
    CheckoutRequest,
    CheckoutResponse,
    StatusResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
def obter_status(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StatusResponse:
    """Retorna status da assinatura, trial e plano efetivo do usuário."""
    user_id = current_user["user_id"]
    subscription = SubscriptionService.get_user_subscription(db, user_id)
    is_trial, dias_restantes = SubscriptionService.is_trial_active(db, user_id)
    plano_efetivo = SubscriptionService.get_effective_plan(db, user_id)

    assinatura_resp = None
    if subscription:
        assinatura_resp = AssinaturaResponse.model_validate(subscription)

    return StatusResponse(
        assinatura=assinatura_resp,
        is_trial=is_trial,
        dias_restantes_trial=dias_restantes,
        plano_efetivo=plano_efetivo,
    )


@router.post("/checkout", response_model=CheckoutResponse)
def criar_checkout(
    data: CheckoutRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CheckoutResponse:
    """Cria sessão de checkout no Stripe e retorna URL."""
    user_id = current_user["user_id"]
    url = SubscriptionService.create_checkout_session(db, user_id, data.plano, data.ciclo)
    return CheckoutResponse(checkout_url=url)


@router.post("/portal")
def criar_portal(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Cria sessão do Stripe Customer Portal e retorna URL."""
    user_id = current_user["user_id"]
    url = SubscriptionService.create_portal_session(db, user_id)
    return {"portal_url": url}


@router.post("/cancelar")
def cancelar_assinatura(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Agenda cancelamento da assinatura para o final do ciclo."""
    user_id = current_user["user_id"]
    SubscriptionService.cancel_subscription(db, user_id)
    return {"detail": "Cancelamento agendado"}
