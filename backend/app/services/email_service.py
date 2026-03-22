"""Serviço de envio de emails via Resend."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def enviar_email_reset_senha(destinatario: str, nome: str, token: str) -> bool:
    """Envia email com link de reset de senha via Resend API."""
    link = f"{settings.FRONTEND_URL}/resetar-senha?token={token}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; background: #0b0b0b; color: #a4b0be; border-radius: 12px;">
        <h2 style="color: #00ffa3; text-align: center;">Controle Financeiro</h2>
        <p>Olá <strong>{nome}</strong>,</p>
        <p>Recebemos uma solicitação para redefinir sua senha.</p>
        <p style="text-align: center; margin: 24px 0;">
            <a href="{link}" style="background: #00ffa3; color: #0b0b0b; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">
                Redefinir Senha
            </a>
        </p>
        <p style="font-size: 13px; color: #666;">Este link expira em 1 hora. Se você não solicitou, ignore este email.</p>
    </div>
    """

    payload = {
        "from": "Controle Financeiro <onboarding@resend.dev>",
        "to": [destinatario],
        "subject": "Redefinir sua senha - Controle Financeiro",
        "html": html,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                RESEND_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
        if resp.status_code in (200, 201):
            logger.info("Email de reset enviado para %s", destinatario)
            return True
        logger.error("Resend erro %s: %s", resp.status_code, resp.text)
        return False
    except Exception as e:
        logger.error("Erro ao enviar email: %s", e)
        return False
