"""Schemas Pydantic para autenticação e perfil de usuário."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Corpo da requisição de login."""

    identificador: str  # email, nome ou CPF
    senha: str


class UserResponse(BaseModel):
    """Dados públicos do usuário retornados pela API."""

    id: int
    nome: str
    email: str
    cpf: str | None = None
    telefone: str | None = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Resposta do endpoint de login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegisterRequest(BaseModel):
    """Corpo da requisição de cadastro."""

    nome: str = Field(min_length=2, max_length=255)
    email: EmailStr
    senha: str = Field(min_length=8)
    cpf: str | None = None
    telefone: str | None = None


class UserUpdate(BaseModel):
    """Corpo da requisição de atualização de perfil."""

    nome: str | None = None
    email: EmailStr | None = None
    senha: str | None = Field(default=None, min_length=8)
