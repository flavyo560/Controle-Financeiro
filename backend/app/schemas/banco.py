"""Schemas Pydantic para bancos."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BancoCreate(BaseModel):
    """Corpo da requisição para criar banco."""

    nome: str = Field(min_length=1, max_length=255)
    saldo_inicial: Decimal = Field(default=Decimal("0"))
    tipo: Literal["debito", "credito"] = "debito"
    limite_total: Decimal | None = None
    dia_fechamento: int | None = None
    dia_vencimento: int | None = None
    bandeira: str | None = None

    @model_validator(mode="after")
    def validar_campos_credito(self):
        if self.tipo == "credito":
            if self.limite_total is None or self.limite_total <= 0:
                raise ValueError("Limite total deve ser maior que zero para tipo crédito")
            if self.dia_fechamento is None or not (1 <= self.dia_fechamento <= 31):
                raise ValueError("Dia de fechamento deve estar entre 1 e 31")
            if self.dia_vencimento is None or not (1 <= self.dia_vencimento <= 31):
                raise ValueError("Dia de vencimento deve estar entre 1 e 31")
        return self


class BancoUpdate(BaseModel):
    """Corpo da requisição para atualizar banco."""

    nome: str | None = Field(default=None, min_length=1, max_length=255)
    saldo_inicial: Decimal | None = None
    ativo: bool | None = None
    tipo: Literal["debito", "credito"] | None = None
    limite_total: Decimal | None = None
    dia_fechamento: int | None = None
    dia_vencimento: int | None = None
    bandeira: str | None = None


class BancoResponse(BaseModel):
    """Dados do banco retornados pela API."""

    id: int
    nome: str
    saldo_inicial: float
    ativo: bool
    tipo: str = "debito"
    cartao_id: int | None = None
    criado_em: datetime | None = None
    saldo_calculado: float = 0

    model_config = {"from_attributes": True}


class SaldoDetalhadoResponse(BaseModel):
    """Saldo detalhado de um banco."""

    banco_id: int
    nome: str
    saldo_inicial: float
    total_receitas: float
    total_despesas_pagas: float
    total_transferencias_entrada: float
    total_transferencias_saida: float
    saldo_calculado: float
