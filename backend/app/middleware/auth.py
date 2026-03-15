"""Utilitários de autenticação JWT e helpers para RLS.

A validação principal de JWT já é feita em ``dependencies.get_current_user``.
Este módulo fornece helpers complementares para uso em middleware ou contextos
onde a injeção de dependência do FastAPI não está disponível.
"""

from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings


def decode_jwt(token: str) -> dict | None:
    """Decodifica e valida um JWT.

    Returns:
        Payload do token ou ``None`` se inválido/expirado.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        return payload
    except JWTError:
        return None


def set_rls_user(db: Session, user_id: int) -> None:
    """Define ``app.current_user_id`` na sessão do banco para RLS."""
    db.execute(text("SET LOCAL app.current_user_id = :uid"), {"uid": str(user_id)})
