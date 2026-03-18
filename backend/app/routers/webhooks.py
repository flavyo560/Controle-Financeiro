"""Router de webhooks: recebe e processa eventos do Stripe."""

import logging

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter()

# Mapeamento de tipos de evento para handlers
_EVENT_HANDLERS = {
    "checkout.session.completed": SubscriptionService.handle_checkout_completed,
    "invoice.payment_succeeded": SubscriptionService.handle_invoice_paid,
    "invoice.payment_failed": SubscriptionService.handle_invoice_failed,
    "customer.subscription.deleted": SubscriptionService.handle_subscription_deleted,
}


@router.post("/stripe")
async def stripe_webhook(request: Request) -> dict:
    """Recebe eventos do Stripe, valida assinatura e despacha para handlers."""
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido",
        )
    except stripe.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assinatura de webhook inválida",
        )

    event_type = event.get("type", "")
    handler = _EVENT_HANDLERS.get(event_type)

    if handler is None:
        logger.info("Evento Stripe ignorado: %s", event_type)
        return {"status": "ignored"}

    db: Session = SessionLocal()
    try:
        handler(event, db)
    except Exception:
        logger.exception("Erro ao processar evento %s", event_type)
        raise
    finally:
        db.close()

    return {"status": "processed"}
