"""Schemas Pydantic para endpoints administrativos."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AdminUsuarioResponse(BaseModel):
    """Dados de usuário retornados no painel admin."""

    id: int
    nome: str
    email: str
    perfil: str
    criado_em: datetime
    plano_atual: str | None = None
    status_assinatura: str | None = None
    trial_inicio: datetime | None = None
    trial_usado: bool
    dias_restantes_trial: int

    model_config = {"from_attributes": True}


class ConcederPlanoRequest(BaseModel):
    """Corpo da requisição de concessão manual de plano."""

    plano: Literal["simples", "plus"]
    ciclo: Literal["mensal", "anual"]


class EstenderTrialRequest(BaseModel):
    """Corpo da requisição de extensão de trial."""

    dias: int = Field(gt=0)


class ResetarSenhaRequest(BaseModel):
    """Corpo da requisição de reset de senha pelo admin."""

    nova_senha: str = Field(min_length=4)
