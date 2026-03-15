"""Schemas Pydantic para categorias."""

from datetime import datetime

from pydantic import BaseModel, Field


class CategoriaCreate(BaseModel):
    """Corpo da requisição para criar categoria."""

    nome: str = Field(min_length=1, max_length=255)
    tipo: str = Field(pattern=r"^(receita|despesa)$")


class CategoriaUpdate(BaseModel):
    """Corpo da requisição para atualizar categoria."""

    nome: str | None = Field(default=None, min_length=1, max_length=255)
    tipo: str | None = Field(default=None, pattern=r"^(receita|despesa)$")
    ativo: bool | None = None


class CategoriaResponse(BaseModel):
    """Dados da categoria retornados pela API."""

    id: int
    nome: str
    tipo: str
    ativo: bool
    criado_em: datetime | None = None

    model_config = {"from_attributes": True}
