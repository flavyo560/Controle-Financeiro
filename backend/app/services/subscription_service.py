"""Serviço de assinaturas — lógica de negócio e integração Stripe."""

import logging
from datetime import datetime, timezone

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.assinatura import Assinatura
from app.models.log_assinatura import LogAssinatura
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionService:
    """Serviço de assinaturas — lógica de negócio."""

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    @staticmethod
    def get_user_subscription(db: Session, user_id: int) -> Assinatura | None:
        """Retorna a assinatura ativa do usuário, ou None."""
        return (
            db.query(Assinatura)
            .filter(Assinatura.usuario_id == user_id, Assinatura.status == "ativa")
            .first()
        )

    @staticmethod
    def get_effective_plan(db: Session, user_id: int) -> str:
        """Retorna o plano efetivo do usuário.

        Ordem de verificação:
        1. Se perfil == 'admin' → 'admin'
        2. Se possui assinatura ativa → plano da assinatura
        3. Se trial ativo → 'plus'
        4. Caso contrário → 'nenhum'
        """
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if user is None:
            return "nenhum"

        if user.perfil == "admin":
            return "admin"

        subscription = SubscriptionService.get_user_subscription(db, user_id)
        if subscription is not None:
            return subscription.plano

        trial_active, _ = SubscriptionService.is_trial_active(db, user_id)
        if trial_active:
            return "plus"

        return "nenhum"

    @staticmethod
    def is_trial_active(db: Session, user_id: int) -> tuple[bool, int]:
        """Verifica se o trial está ativo e retorna (ativo, dias_restantes).

        Trial dura 7 dias a partir de trial_inicio.
        Requer trial_inicio preenchido e trial_usado == True.
        """
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if user is None:
            return (False, 0)

        if user.trial_inicio is None or not user.trial_usado:
            return (False, 0)

        now = datetime.now(timezone.utc)
        elapsed = (now - user.trial_inicio).days
        days_remaining = max(0, 7 - elapsed)
        return (days_remaining > 0, days_remaining)

    # ------------------------------------------------------------------
    # Checkout & Portal
    # ------------------------------------------------------------------

    @staticmethod
    def create_checkout_session(
        db: Session, user_id: int, plano: str, ciclo: str
    ) -> str:
        """Cria sessão de checkout no Stripe. Retorna URL do checkout."""
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )

        # Verificar se já possui assinatura ativa
        existing = SubscriptionService.get_user_subscription(db, user_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você já possui uma assinatura ativa",
            )

        price_key = f"{plano}_{ciclo}"
        price_id = settings.stripe_prices.get(price_key)
        if not price_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Preço não configurado para {plano}/{ciclo}",
            )

        # Obter ou criar stripe_customer_id
        # Buscar assinatura existente (qualquer status) para reutilizar customer
        any_sub = (
            db.query(Assinatura)
            .filter(Assinatura.usuario_id == user_id)
            .first()
        )
        customer_id = any_sub.stripe_customer_id if any_sub and any_sub.stripe_customer_id else None

        if not customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.nome,
                metadata={"user_id": str(user_id)},
            )
            customer_id = customer.id
            # Salvar customer_id se houver registro de assinatura
            if any_sub:
                any_sub.stripe_customer_id = customer_id
                db.commit()

        frontend_base = settings.FRONTEND_URL or settings.CORS_ORIGINS.split(",")[0].strip()
        success_url = f"{frontend_base}/planos?sucesso=true"
        cancel_url = f"{frontend_base}/planos?cancelado=true"

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": str(user_id), "plano": plano, "ciclo": ciclo},
            )
        except stripe.StripeError as e:
            logger.error("Erro ao criar sessão de checkout: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao iniciar pagamento",
            )

        return session.url

    @staticmethod
    def create_portal_session(db: Session, user_id: int) -> str:
        """Cria sessão do Stripe Customer Portal. Retorna URL."""
        sub = (
            db.query(Assinatura)
            .filter(Assinatura.usuario_id == user_id)
            .first()
        )
        if sub is None or not sub.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma assinatura encontrada para gerenciar",
            )

        try:
            frontend_base = settings.FRONTEND_URL or settings.CORS_ORIGINS.split(",")[0].strip()
            session = stripe.billing_portal.Session.create(
                customer=sub.stripe_customer_id,
                return_url=f"{frontend_base}/planos",
            )
        except stripe.StripeError as e:
            logger.error("Erro ao criar sessão do portal: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao abrir portal de gerenciamento",
            )

        return session.url

    # ------------------------------------------------------------------
    # Cancelamento
    # ------------------------------------------------------------------

    @staticmethod
    def cancel_subscription(db: Session, user_id: int) -> None:
        """Agenda cancelamento da assinatura no final do ciclo."""
        sub = SubscriptionService.get_user_subscription(db, user_id)
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma assinatura ativa para cancelar",
            )

        if sub.stripe_subscription_id:
            try:
                stripe.Subscription.modify(
                    sub.stripe_subscription_id,
                    cancel_at_period_end=True,
                )
            except stripe.StripeError as e:
                logger.error("Erro ao cancelar assinatura no Stripe: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao processar cancelamento",
                )

        SubscriptionService._log_event(
            db,
            usuario_id=user_id,
            evento="cancelamento_agendado",
            status_anterior=sub.status,
            status_novo=sub.status,  # mantém ativa até fim do ciclo
            detalhes="Cancelamento agendado para final do ciclo",
        )

    # ------------------------------------------------------------------
    # Webhook handlers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_event_processed(db: Session, stripe_event_id: str) -> bool:
        """Verifica se um evento Stripe já foi processado (idempotência)."""
        if not stripe_event_id:
            return False
        existing = (
            db.query(LogAssinatura)
            .filter(LogAssinatura.stripe_event_id == stripe_event_id)
            .first()
        )
        return existing is not None

    @staticmethod
    def handle_checkout_completed(event_data: dict, db: Session) -> None:
        """Processa evento checkout.session.completed.

        Cria ou atualiza assinatura com status 'ativa'.
        """
        stripe_event_id = event_data.get("id")
        if SubscriptionService._is_event_processed(db, stripe_event_id):
            logger.info("Evento %s já processado, ignorando.", stripe_event_id)
            return

        session_obj = event_data.get("data", {}).get("object", {})
        customer_id = session_obj.get("customer")
        stripe_subscription_id = session_obj.get("subscription")
        metadata = session_obj.get("metadata", {})
        user_id_str = metadata.get("user_id")
        plano = metadata.get("plano", "simples")
        ciclo = metadata.get("ciclo", "mensal")

        # Encontrar usuário
        user = None
        if user_id_str:
            user = db.query(Usuario).filter(Usuario.id == int(user_id_str)).first()
        if user is None and customer_id:
            sub = (
                db.query(Assinatura)
                .filter(Assinatura.stripe_customer_id == customer_id)
                .first()
            )
            if sub:
                user = db.query(Usuario).filter(Usuario.id == sub.usuario_id).first()

        if user is None:
            logger.warning("Usuário não encontrado para checkout event %s", stripe_event_id)
            return

        # Criar ou atualizar assinatura
        assinatura = (
            db.query(Assinatura).filter(Assinatura.usuario_id == user.id).first()
        )
        status_anterior = assinatura.status if assinatura else None

        if assinatura is None:
            assinatura = Assinatura(
                usuario_id=user.id,
                plano=plano,
                ciclo=ciclo,
                status="ativa",
                stripe_customer_id=customer_id,
                stripe_subscription_id=stripe_subscription_id,
            )
            db.add(assinatura)
        else:
            assinatura.plano = plano
            assinatura.ciclo = ciclo
            assinatura.status = "ativa"
            assinatura.stripe_customer_id = customer_id
            assinatura.stripe_subscription_id = stripe_subscription_id
            assinatura.atualizado_em = datetime.now(timezone.utc)

        db.flush()

        SubscriptionService._log_event(
            db,
            usuario_id=user.id,
            evento="checkout_completed",
            status_anterior=status_anterior,
            status_novo="ativa",
            detalhes=f"Plano {plano} ({ciclo}) ativado via checkout",
            stripe_event_id=stripe_event_id,
        )

    @staticmethod
    def handle_invoice_paid(event_data: dict, db: Session) -> None:
        """Processa evento invoice.payment_succeeded.

        Atualiza data_renovacao da assinatura.
        """
        stripe_event_id = event_data.get("id")
        if SubscriptionService._is_event_processed(db, stripe_event_id):
            logger.info("Evento %s já processado, ignorando.", stripe_event_id)
            return

        invoice = event_data.get("data", {}).get("object", {})
        stripe_subscription_id = invoice.get("subscription")

        if not stripe_subscription_id:
            return

        assinatura = (
            db.query(Assinatura)
            .filter(Assinatura.stripe_subscription_id == stripe_subscription_id)
            .first()
        )
        if assinatura is None:
            logger.warning(
                "Assinatura não encontrada para subscription %s",
                stripe_subscription_id,
            )
            return

        period_end = invoice.get("lines", {}).get("data", [{}])[0].get("period", {}).get("end")
        if period_end:
            assinatura.data_renovacao = datetime.fromtimestamp(period_end, tz=timezone.utc)

        assinatura.atualizado_em = datetime.now(timezone.utc)
        db.flush()

        SubscriptionService._log_event(
            db,
            usuario_id=assinatura.usuario_id,
            evento="invoice_paid",
            status_anterior=assinatura.status,
            status_novo=assinatura.status,
            detalhes="Pagamento de fatura confirmado",
            stripe_event_id=stripe_event_id,
        )

    @staticmethod
    def handle_invoice_failed(event_data: dict, db: Session) -> None:
        """Processa evento invoice.payment_failed.

        Altera status da assinatura para 'inadimplente'.
        """
        stripe_event_id = event_data.get("id")
        if SubscriptionService._is_event_processed(db, stripe_event_id):
            logger.info("Evento %s já processado, ignorando.", stripe_event_id)
            return

        invoice = event_data.get("data", {}).get("object", {})
        stripe_subscription_id = invoice.get("subscription")

        if not stripe_subscription_id:
            return

        assinatura = (
            db.query(Assinatura)
            .filter(Assinatura.stripe_subscription_id == stripe_subscription_id)
            .first()
        )
        if assinatura is None:
            logger.warning(
                "Assinatura não encontrada para subscription %s",
                stripe_subscription_id,
            )
            return

        status_anterior = assinatura.status
        assinatura.status = "inadimplente"
        assinatura.atualizado_em = datetime.now(timezone.utc)
        db.flush()

        SubscriptionService._log_event(
            db,
            usuario_id=assinatura.usuario_id,
            evento="invoice_failed",
            status_anterior=status_anterior,
            status_novo="inadimplente",
            detalhes="Falha no pagamento da fatura",
            stripe_event_id=stripe_event_id,
        )

    @staticmethod
    def handle_subscription_deleted(event_data: dict, db: Session) -> None:
        """Processa evento customer.subscription.deleted.

        Altera status da assinatura para 'cancelada'.
        """
        stripe_event_id = event_data.get("id")
        if SubscriptionService._is_event_processed(db, stripe_event_id):
            logger.info("Evento %s já processado, ignorando.", stripe_event_id)
            return

        sub_obj = event_data.get("data", {}).get("object", {})
        stripe_subscription_id = sub_obj.get("id")

        if not stripe_subscription_id:
            return

        assinatura = (
            db.query(Assinatura)
            .filter(Assinatura.stripe_subscription_id == stripe_subscription_id)
            .first()
        )
        if assinatura is None:
            logger.warning(
                "Assinatura não encontrada para subscription %s",
                stripe_subscription_id,
            )
            return

        status_anterior = assinatura.status
        assinatura.status = "cancelada"
        assinatura.atualizado_em = datetime.now(timezone.utc)
        db.flush()

        SubscriptionService._log_event(
            db,
            usuario_id=assinatura.usuario_id,
            evento="subscription_deleted",
            status_anterior=status_anterior,
            status_novo="cancelada",
            detalhes="Assinatura cancelada pelo Stripe",
            stripe_event_id=stripe_event_id,
        )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @staticmethod
    def _log_event(
        db: Session,
        usuario_id: int,
        evento: str,
        status_anterior: str | None = None,
        status_novo: str | None = None,
        detalhes: str | None = None,
        stripe_event_id: str | None = None,
        admin_id: int | None = None,
    ) -> None:
        """Registra evento no log de assinaturas."""
        log = LogAssinatura(
            usuario_id=usuario_id,
            evento=evento,
            status_anterior=status_anterior,
            status_novo=status_novo,
            detalhes=detalhes,
            stripe_event_id=stripe_event_id,
            admin_id=admin_id,
        )
        db.add(log)
        db.commit()
