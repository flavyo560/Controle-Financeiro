"""Serviço administrativo — gestão de usuários e licenças."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.assinatura import Assinatura
from app.models.usuario import Usuario
from app.services.subscription_service import SubscriptionService


class AdminService:
    """Lógica de negócio do painel administrativo."""

    @staticmethod
    def _build_user_dict(db: Session, user: Usuario) -> dict:
        """Monta dict de usuário no formato AdminUsuarioResponse."""
        subscription = SubscriptionService.get_user_subscription(db, user.id)
        trial_active, dias_restantes = SubscriptionService.is_trial_active(db, user.id)

        return {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "perfil": user.perfil,
            "criado_em": user.criado_em,
            "plano_atual": subscription.plano if subscription else None,
            "status_assinatura": subscription.status if subscription else None,
            "trial_inicio": user.trial_inicio,
            "trial_usado": user.trial_usado,
            "dias_restantes_trial": dias_restantes,
        }

    @staticmethod
    def list_users(db: Session) -> list[dict]:
        """Lista todos os usuários com dados de assinatura e trial."""
        users = db.query(Usuario).all()
        return [AdminService._build_user_dict(db, u) for u in users]

    @staticmethod
    def get_user_detail(db: Session, user_id: int) -> dict:
        """Retorna detalhes de um usuário. Levanta 404 se não encontrado."""
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )
        return AdminService._build_user_dict(db, user)

    @staticmethod
    def grant_plan(
        db: Session, user_id: int, plano: str, ciclo: str, admin_id: int
    ) -> None:
        """Concede plano manualmente sem Stripe. Cria ou atualiza assinatura."""
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )

        assinatura = (
            db.query(Assinatura).filter(Assinatura.usuario_id == user_id).first()
        )
        status_anterior = assinatura.status if assinatura else None

        if assinatura is None:
            assinatura = Assinatura(
                usuario_id=user_id,
                plano=plano,
                ciclo=ciclo,
                status="ativa",
            )
            db.add(assinatura)
        else:
            assinatura.plano = plano
            assinatura.ciclo = ciclo
            assinatura.status = "ativa"
            assinatura.atualizado_em = datetime.now(timezone.utc)

        db.flush()

        SubscriptionService._log_event(
            db,
            usuario_id=user_id,
            evento="admin_grant_plan",
            status_anterior=status_anterior,
            status_novo="ativa",
            detalhes=f"Plano {plano} ({ciclo}) concedido manualmente pelo admin {admin_id}",
            admin_id=admin_id,
        )

    @staticmethod
    def revoke_subscription(db: Session, user_id: int, admin_id: int) -> None:
        """Revoga assinatura imediatamente. Levanta 404 se usuário não encontrado."""
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )

        assinatura = SubscriptionService.get_user_subscription(db, user_id)
        if assinatura is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário não possui assinatura ativa",
            )

        status_anterior = assinatura.status
        assinatura.status = "cancelada"
        assinatura.atualizado_em = datetime.now(timezone.utc)
        db.flush()

        SubscriptionService._log_event(
            db,
            usuario_id=user_id,
            evento="admin_revoke",
            status_anterior=status_anterior,
            status_novo="cancelada",
            detalhes=f"Assinatura revogada pelo admin {admin_id}",
            admin_id=admin_id,
        )

    @staticmethod
    def extend_trial(
        db: Session, user_id: int, dias: int, admin_id: int
    ) -> None:
        """Estende ou concede trial. Levanta 404 se usuário não encontrado."""
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )

        if user.trial_inicio is None:
            # Conceder novo trial
            user.trial_inicio = datetime.now(timezone.utc)
            user.trial_usado = True
            detalhes = f"Trial de {dias} dias concedido pelo admin {admin_id}"
            # Adjust trial_inicio backwards so total trial = dias days
            if dias != 7:
                user.trial_inicio = datetime.now(timezone.utc) - timedelta(days=(7 - dias))
        else:
            # Estender trial existente: mover trial_inicio para trás
            user.trial_inicio = user.trial_inicio - timedelta(days=dias)
            detalhes = f"Trial estendido em {dias} dias pelo admin {admin_id}"

        db.flush()

        SubscriptionService._log_event(
            db,
            usuario_id=user_id,
            evento="admin_extend_trial",
            status_anterior=None,
            status_novo=None,
            detalhes=detalhes,
            admin_id=admin_id,
        )
