"""Serviço de autenticação: login, registro e gestão de senhas."""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, RegisterRequest, UserUpdate

logger = logging.getLogger(__name__)


def _create_reset_token(user: Usuario) -> str:
    """Gera JWT de reset de senha com expiração de 1 hora."""
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "user_id": user.id,
        "email": user.email,
        "tipo": "reset_senha",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_reset_token(token: str) -> dict:
    """Valida JWT de reset de senha.

    Returns:
        Payload do token.

    Raises:
        HTTPException 400: token inválido ou expirado.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("tipo") != "reset_senha":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido")


def _hash_bcrypt(password: str) -> str:
    """Gera hash bcrypt com 12 rounds."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_bcrypt(password: str, hashed: str) -> bool:
    """Verifica senha contra hash bcrypt."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.error("Erro ao verificar bcrypt: %s", e)
        return False


def _hash_sha256(password: str) -> str:
    """Gera hash SHA-256 (compatibilidade legado)."""
    return hashlib.sha256(password.encode()).hexdigest()


def _create_jwt(user: Usuario, db: Session) -> str:
    """Gera JWT com payload user_id, email, perfil, plano e expiração de 24h."""
    from app.services.subscription_service import SubscriptionService

    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    plano = SubscriptionService.get_effective_plan(db, user.id)
    payload: dict = {
        "user_id": user.id,
        "email": user.email,
        "perfil": user.perfil,
        "plano": plano,
        "exp": expire,
    }

    trial_active, dias_restantes = SubscriptionService.is_trial_active(db, user.id)
    if trial_active and user.trial_inicio:
        trial_fim = user.trial_inicio + timedelta(days=7)
        payload["trial_fim"] = trial_fim.isoformat()

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def authenticate(db: Session, data: LoginRequest) -> tuple[str, Usuario]:
    """Autentica usuário por email, nome ou CPF.

    Verifica bcrypt primeiro; se não houver hash bcrypt, tenta SHA-256
    e migra automaticamente para bcrypt em caso de sucesso.

    Returns:
        Tupla (access_token, usuario).

    Raises:
        HTTPException 401: credenciais inválidas.
    """
    user = db.query(Usuario).filter(
        or_(
            Usuario.email == data.identificador,
            Usuario.nome == data.identificador,
            Usuario.cpf == data.identificador,
        )
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    # Tentar bcrypt primeiro
    if user.senha_hash_bcrypt and _verify_bcrypt(data.senha, user.senha_hash_bcrypt):
        token = _create_jwt(user, db)
        return token, user

    # Fallback SHA-256 com migração automática
    if user.senha_hash and _hash_sha256(data.senha) == user.senha_hash:
        # Migrar para bcrypt
        user.senha_hash_bcrypt = _hash_bcrypt(data.senha)
        user.senha_hash = None
        db.commit()
        db.refresh(user)
        token = _create_jwt(user, db)
        return token, user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
    )


def register(db: Session, data: RegisterRequest) -> Usuario:
    """Cadastra novo usuário com senha bcrypt (12 rounds).

    Raises:
        HTTPException 409: email já cadastrado.
    """
    existing = db.query(Usuario).filter(Usuario.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado",
        )

    user = Usuario(
        nome=data.nome,
        email=data.email,
        senha_hash_bcrypt=_hash_bcrypt(data.senha),
        cpf=data.cpf,
        telefone=data.telefone,
        trial_inicio=datetime.now(timezone.utc),
        trial_usado=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> Usuario:
    """Busca usuário por ID.

    Raises:
        HTTPException 404: usuário não encontrado.
    """
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return user


def update_user(db: Session, user_id: int, data: UserUpdate) -> Usuario:
    """Atualiza perfil do usuário.

    Raises:
        HTTPException 404: usuário não encontrado.
        HTTPException 409: email já em uso por outro usuário.
    """
    user = get_user_by_id(db, user_id)

    if data.email is not None and data.email != user.email:
        existing = db.query(Usuario).filter(
            Usuario.email == data.email,
            Usuario.id != user_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email já em uso por outro usuário",
            )
        user.email = data.email

    if data.nome is not None:
        user.nome = data.nome

    if data.senha is not None:
        user.senha_hash_bcrypt = _hash_bcrypt(data.senha)
        user.senha_hash = None

    db.commit()
    db.refresh(user)
    return user


async def request_password_reset(db: Session, email: str) -> bool:
    """Gera token de reset e envia email.

    Retorna True sempre (não revela se email existe).
    """
    from app.services.email_service import enviar_email_reset_senha

    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None:
        # Não revelar que email não existe
        return True

    token = _create_reset_token(user)
    await enviar_email_reset_senha(user.email, user.nome, token)
    return True


def reset_password(db: Session, token: str, nova_senha: str) -> bool:
    """Valida token e redefine a senha do usuário."""
    payload = verify_reset_token(token)
    user = db.query(Usuario).filter(Usuario.id == payload["user_id"]).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não encontrado",
        )
    user.senha_hash_bcrypt = _hash_bcrypt(nova_senha)
    user.senha_hash = None
    db.commit()
    return True
