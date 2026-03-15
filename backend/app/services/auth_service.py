"""Serviço de autenticação: login, registro e gestão de senhas."""

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from passlib.hash import bcrypt as passlib_bcrypt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, RegisterRequest, UserUpdate


def _hash_bcrypt(password: str) -> str:
    """Gera hash bcrypt com 12 rounds."""
    return passlib_bcrypt.using(rounds=12).hash(password)


def _verify_bcrypt(password: str, hashed: str) -> bool:
    """Verifica senha contra hash bcrypt."""
    return passlib_bcrypt.verify(password, hashed)


def _hash_sha256(password: str) -> str:
    """Gera hash SHA-256 (compatibilidade legado)."""
    return hashlib.sha256(password.encode()).hexdigest()


def _create_jwt(user: Usuario) -> str:
    """Gera JWT com payload user_id + email e expiração de 24h."""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": expire,
    }
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
        token = _create_jwt(user)
        return token, user

    # Fallback SHA-256 com migração automática
    if user.senha_hash and _hash_sha256(data.senha) == user.senha_hash:
        # Migrar para bcrypt
        user.senha_hash_bcrypt = _hash_bcrypt(data.senha)
        user.senha_hash = None
        db.commit()
        db.refresh(user)
        token = _create_jwt(user)
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
