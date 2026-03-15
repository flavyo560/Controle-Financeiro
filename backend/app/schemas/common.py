"""Schemas comuns: paginação e respostas genéricas."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Parâmetros de paginação para queries."""

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class PaginatedResponse(BaseModel, Generic[T]):
    """Resposta paginada genérica."""

    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int
