"""Dependências compartilhadas: sessão de banco e autenticação."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Fornece uma sessão de banco de dados com fechamento automático."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Decodifica o JWT e retorna os dados do usuário autenticado.

    Inclui perfil e plano do JWT. Se ausentes (tokens legados),
    faz fallback para consulta ao banco.

    Raises:
        HTTPException 401: Se o token for inválido ou expirado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: int | None = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Setar user_id na sessão do banco para RLS
    db.execute(text("SET LOCAL app.current_user_id = :uid"), {"uid": str(user_id)})

    perfil = payload.get("perfil")
    plano = payload.get("plano")

    # Fallback para tokens legados sem perfil/plano
    if perfil is None or plano is None:
        from app.models.usuario import Usuario
        from app.services.subscription_service import SubscriptionService

        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if user is None:
            raise credentials_exception
        if perfil is None:
            perfil = user.perfil
        if plano is None:
            plano = SubscriptionService.get_effective_plan(db, user_id)

    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "perfil": perfil,
        "plano": plano,
    }
