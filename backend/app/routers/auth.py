"""Router de autenticação: login, registro e perfil."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
    UserUpdate,
)
from app.services import auth_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    """Autentica usuário por email, nome ou CPF e retorna JWT."""
    token, user = auth_service.authenticate(db, data)
    return LoginResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    data: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Cadastra novo usuário com senha bcrypt."""
    user = auth_service.register(db, data)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Retorna dados do usuário autenticado."""
    user = auth_service.get_user_by_id(db, current_user["user_id"])
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Atualiza perfil do usuário autenticado."""
    user = auth_service.update_user(db, current_user["user_id"], data)
    return UserResponse.model_validate(user)
