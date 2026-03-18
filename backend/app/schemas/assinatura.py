"""Schemas Pydantic para assinaturas e checkout."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AssinaturaResponse(BaseModel):
    """Dados da assinatura retornados pela API."""

    plano: str
    ciclo: str
    status: str
    data_inicio: datetime
    data_renovacao: datetime | None = None
    stripe_subscription_id: str | None = None

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    """Corpo da requisição de criação de checkout."""

    plano: Literal["simples", "plus"]
    ciclo: Literal["mensal", "anual"]


class CheckoutResponse(BaseModel):
    """Resposta do endpoint de checkout."""

    checkout_url: str


class StatusResponse(BaseModel):
    """Resposta do endpoint de status da assinatura."""

    assinatura: AssinaturaResponse | None = None
    is_trial: bool
    dias_restantes_trial: int
    plano_efetivo: str
