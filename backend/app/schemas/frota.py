"""Schemas Pydantic para gestão de frota: veículos, abastecimentos e manutenções."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Veículos
# ---------------------------------------------------------------------------


class VeiculoCreate(BaseModel):
    """Corpo da requisição para criar veículo."""

    nome_identificador: str = Field(min_length=1, max_length=255)
    placa: str | None = Field(default=None, max_length=10)
    modelo: str | None = Field(default=None, max_length=255)


class VeiculoUpdate(BaseModel):
    """Corpo da requisição para atualizar veículo."""

    nome_identificador: str | None = Field(default=None, min_length=1, max_length=255)
    placa: str | None = Field(default=None, max_length=10)
    modelo: str | None = Field(default=None, max_length=255)


class VeiculoResponse(BaseModel):
    """Dados do veículo retornados pela API."""

    id: int
    usuario_id: int
    nome_identificador: str
    placa: str | None = None
    modelo: str | None = None
    status: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Abastecimentos
# ---------------------------------------------------------------------------


class AbastecimentoCreate(BaseModel):
    """Corpo da requisição para registrar abastecimento."""

    data: date
    litros: Decimal | None = Field(default=None, ge=0)
    valor: Decimal = Field(ge=0)
    km: Decimal | None = Field(default=None, ge=0)
    posto: str | None = Field(default=None, max_length=255)
    tipo: str | None = Field(default=None, max_length=50)
    litros_gasolina: Decimal | None = Field(default=None, ge=0)
    litros_etanol: Decimal | None = Field(default=None, ge=0)


class AbastecimentoUpdate(BaseModel):
    """Corpo da requisição para atualizar abastecimento."""

    data: date | None = None
    litros: Decimal | None = Field(default=None, ge=0)
    valor: Decimal | None = Field(default=None, ge=0)
    km: Decimal | None = Field(default=None, ge=0)
    posto: str | None = Field(default=None, max_length=255)
    tipo: str | None = Field(default=None, max_length=50)
    litros_gasolina: Decimal | None = Field(default=None, ge=0)
    litros_etanol: Decimal | None = Field(default=None, ge=0)


class AbastecimentoResponse(BaseModel):
    """Dados do abastecimento retornados pela API."""

    id: int
    veiculo_id: int
    data: date
    litros: Decimal | None = None
    valor: Decimal
    km: Decimal | None = None
    posto: str | None = None
    tipo: str | None = None
    litros_gasolina: Decimal | None = None
    litros_etanol: Decimal | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Manutenções
# ---------------------------------------------------------------------------


class ManutencaoCreate(BaseModel):
    """Corpo da requisição para registrar manutenção."""

    data: date
    servico: str | None = None
    valor: Decimal = Field(ge=0)
    km: Decimal | None = Field(default=None, ge=0)


class ManutencaoUpdate(BaseModel):
    """Corpo da requisição para atualizar manutenção."""

    data: date | None = None
    servico: str | None = None
    valor: Decimal | None = Field(default=None, ge=0)
    km: Decimal | None = Field(default=None, ge=0)


class ManutencaoResponse(BaseModel):
    """Dados da manutenção retornados pela API."""

    id: int
    veiculo_id: int
    data: date
    servico: str | None = None
    valor: Decimal
    km: Decimal | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Consumo Médio
# ---------------------------------------------------------------------------


class ConsumoMedioResponse(BaseModel):
    """Dados de consumo médio de um veículo."""

    veiculo_id: int
    consumo_medio: Decimal = Decimal("0")
    total_litros: Decimal = Decimal("0")
    total_valor: Decimal = Decimal("0")
    total_abastecimentos: int = 0
