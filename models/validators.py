"""
Modelos de validação Pydantic para o sistema de controle financeiro.

Este módulo fornece validação robusta e tipada para todas as entradas do usuário,
garantindo integridade dos dados antes de operações de banco de dados.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date
from decimal import Decimal
from typing import Optional


class DespesaModel(BaseModel):
    """Modelo de validação para despesas."""
    descricao: str = Field(min_length=1, max_length=200)
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    data: date
    categoria_id: int = Field(gt=0)
    banco_id: int = Field(gt=0)
    
    @field_validator('descricao')
    @classmethod
    def descricao_nao_vazia(cls, v):
        if not v.strip():
            raise ValueError('Descrição não pode ser vazia ou apenas espaços')
        return v.strip()
    
    @field_validator('data')
    @classmethod
    def data_nao_futura(cls, v):
        if v > date.today():
            raise ValueError('Data não pode ser futura')
        return v


class ReceitaModel(BaseModel):
    """Modelo de validação para receitas."""
    descricao: str = Field(min_length=1, max_length=200)
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    data: date
    categoria_id: int = Field(gt=0)
    banco_id: int = Field(gt=0)
    
    @field_validator('descricao')
    @classmethod
    def descricao_nao_vazia(cls, v):
        if not v.strip():
            raise ValueError('Descrição não pode ser vazia')
        return v.strip()


class CartaoModel(BaseModel):
    """Modelo de validação para cartões de crédito."""
    nome: str = Field(min_length=1, max_length=100)
    limite_total: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    dia_fechamento: int = Field(ge=1, le=31)
    dia_vencimento: int = Field(ge=1, le=31)
    bandeira: Optional[str] = Field(default=None, max_length=50)
    
    @field_validator('nome')
    @classmethod
    def nome_nao_vazio(cls, v):
        if not v.strip():
            raise ValueError('Nome não pode ser vazio')
        return v.strip()
    
    @model_validator(mode='after')
    def validar_datas_cartao(self):
        if self.dia_fechamento == self.dia_vencimento:
            raise ValueError('Dia de fechamento e vencimento não podem ser iguais')
        return self


class CompraCartaoModel(BaseModel):
    """Modelo de validação para compras no cartão."""
    cartao_id: int = Field(gt=0)
    descricao: str = Field(min_length=1, max_length=200)
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    data_compra: date
    categoria_id: Optional[int] = Field(default=None, gt=0)
    
    @field_validator('descricao')
    @classmethod
    def descricao_nao_vazia(cls, v):
        if not v.strip():
            raise ValueError('Descrição não pode ser vazia')
        return v.strip()


class DespesaParceladaModel(BaseModel):
    """Modelo de validação para despesas parceladas."""
    descricao: str = Field(min_length=1, max_length=200)
    valor_total: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    numero_parcelas: int = Field(ge=2, le=120)
    data_primeira_parcela: date
    categoria_id: int = Field(gt=0)
    banco_id: int = Field(gt=0)
    
    @field_validator('descricao')
    @classmethod
    def descricao_nao_vazia(cls, v):
        if not v.strip():
            raise ValueError('Descrição não pode ser vazia')
        return v.strip()


class DespesaRecorrenteModel(BaseModel):
    """Modelo de validação para despesas recorrentes."""
    descricao: str = Field(min_length=1, max_length=200)
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    dia_mes: int = Field(ge=1, le=31)
    categoria_id: int = Field(gt=0)
    banco_id: int = Field(gt=0)
    data_inicio: date
    data_fim: Optional[date] = None
    
    @field_validator('descricao')
    @classmethod
    def descricao_nao_vazia(cls, v):
        if not v.strip():
            raise ValueError('Descrição não pode ser vazia')
        return v.strip()
    
    @model_validator(mode='after')
    def validar_periodo(self):
        if self.data_fim and self.data_fim < self.data_inicio:
            raise ValueError('Data fim não pode ser anterior à data início')
        return self


class UsuarioModel(BaseModel):
    """Modelo de validação para usuários."""
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=100)
    senha: str = Field(min_length=8, max_length=100)
    perfil: str = Field(default="admin")
    
    @field_validator('nome')
    @classmethod
    def nome_nao_vazio(cls, v):
        if not v.strip():
            raise ValueError('Nome não pode ser vazio')
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def email_valido(cls, v):
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Email inválido')
        return v.lower().strip()
    
    @field_validator('senha')
    @classmethod
    def senha_forte(cls, v):
        if len(v) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter pelo menos um número')
        return v



class OrcamentoModel(BaseModel):
    """Modelo de validação para orçamentos."""
    ano: int = Field(ge=2000, le=2100)
    status: str = Field(pattern='^(ativo|inativo)$', default='ativo')
    
    @field_validator('ano')
    @classmethod
    def validar_ano(cls, v):
        if v < 2000 or v > 2100:
            raise ValueError('Ano deve estar entre 2000 e 2100')
        return v


class ItemOrcamentoModel(BaseModel):
    """Modelo de validação para itens de orçamento."""
    orcamento_id: int = Field(gt=0)
    categoria_id: int = Field(gt=0)
    mes: int = Field(ge=1, le=12)
    valor_planejado: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    
    @field_validator('valor_planejado')
    @classmethod
    def validar_valor(cls, v):
        if v < 0:
            raise ValueError('Valor planejado não pode ser negativo')
        # Limitar a 2 casas decimais
        return round(v, 2)
    
    @field_validator('mes')
    @classmethod
    def validar_mes(cls, v):
        if v < 1 or v > 12:
            raise ValueError('Mês deve estar entre 1 e 12')
        return v
