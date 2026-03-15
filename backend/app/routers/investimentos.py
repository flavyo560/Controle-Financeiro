"""Router de investimentos: CRUD com cálculo de rentabilidade e dividendos."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.dividendo import Dividendo
from app.models.investimento import Investimento
from app.schemas.investimento import (
    DividendoCreate,
    DividendoResponse,
    InvestimentoCreate,
    InvestimentoResponse,
    InvestimentoUpdate,
    ValorAtualUpdate,
)

router = APIRouter()


def _calcular_rentabilidade(investimento: Investimento) -> Decimal:
    """Calcula rentabilidade: ((valor_atual - valor_investido) / valor_investido) * 100.

    Retorna 0 se valor_investido for 0 (evita divisão por zero).
    """
    valor_investido = Decimal(str(investimento.valor_investido or 0))
    valor_atual = Decimal(str(investimento.valor_atual or 0))
    if valor_investido == 0:
        return Decimal("0")
    return ((valor_atual - valor_investido) / valor_investido) * 100


def _investimento_response(investimento: Investimento) -> InvestimentoResponse:
    """Constrói resposta de investimento com rentabilidade calculada."""
    resp = InvestimentoResponse.model_validate(investimento)
    resp.rentabilidade = _calcular_rentabilidade(investimento)
    return resp


# ---------------------------------------------------------------------------
# Investimentos CRUD
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[InvestimentoResponse])
def listar_investimentos(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[InvestimentoResponse]:
    """Lista todos os investimentos do usuário com rentabilidade calculada."""
    usuario_id = current_user["user_id"]
    investimentos = (
        db.query(Investimento)
        .filter(Investimento.usuario_id == usuario_id)
        .all()
    )
    return [_investimento_response(inv) for inv in investimentos]


@router.post("/", response_model=InvestimentoResponse, status_code=201)
def criar_investimento(
    data: InvestimentoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvestimentoResponse:
    """Cria um novo investimento para o usuário."""
    usuario_id = current_user["user_id"]
    investimento = Investimento(
        usuario_id=usuario_id,
        nome=data.nome,
        tipo=data.tipo,
        valor_investido=data.valor_investido,
        valor_atual=data.valor_atual,
        data=data.data,
        ativo=data.ativo,
        categoria_id=data.categoria_id,
        banco_id=data.banco_id,
    )
    db.add(investimento)
    db.commit()
    db.refresh(investimento)
    return _investimento_response(investimento)


@router.put("/{investimento_id}", response_model=InvestimentoResponse)
def atualizar_investimento(
    investimento_id: int,
    data: InvestimentoUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvestimentoResponse:
    """Atualiza dados de um investimento do usuário."""
    usuario_id = current_user["user_id"]
    investimento = (
        db.query(Investimento)
        .filter(Investimento.id == investimento_id, Investimento.usuario_id == usuario_id)
        .first()
    )
    if not investimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(investimento, field, value)

    db.commit()
    db.refresh(investimento)
    return _investimento_response(investimento)


@router.delete("/{investimento_id}", status_code=204)
def excluir_investimento(
    investimento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui um investimento do usuário."""
    usuario_id = current_user["user_id"]
    investimento = (
        db.query(Investimento)
        .filter(Investimento.id == investimento_id, Investimento.usuario_id == usuario_id)
        .first()
    )
    if not investimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado",
        )

    db.delete(investimento)
    db.commit()


@router.patch("/{investimento_id}/valor-atual", response_model=InvestimentoResponse)
def atualizar_valor_atual(
    investimento_id: int,
    data: ValorAtualUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvestimentoResponse:
    """Atualiza o valor atual de um investimento."""
    usuario_id = current_user["user_id"]
    investimento = (
        db.query(Investimento)
        .filter(Investimento.id == investimento_id, Investimento.usuario_id == usuario_id)
        .first()
    )
    if not investimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado",
        )

    investimento.valor_atual = data.valor_atual
    db.commit()
    db.refresh(investimento)
    return _investimento_response(investimento)


# ---------------------------------------------------------------------------
# Dividendos CRUD
# ---------------------------------------------------------------------------


@router.get("/{investimento_id}/dividendos", response_model=list[DividendoResponse])
def listar_dividendos(
    investimento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DividendoResponse]:
    """Lista dividendos de um investimento do usuário."""
    usuario_id = current_user["user_id"]
    investimento = (
        db.query(Investimento)
        .filter(Investimento.id == investimento_id, Investimento.usuario_id == usuario_id)
        .first()
    )
    if not investimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado",
        )

    dividendos = (
        db.query(Dividendo)
        .filter(Dividendo.investimento_id == investimento_id)
        .order_by(Dividendo.data.desc())
        .all()
    )
    return [DividendoResponse.model_validate(d) for d in dividendos]


@router.post("/{investimento_id}/dividendos", response_model=DividendoResponse, status_code=201)
def registrar_dividendo(
    investimento_id: int,
    data: DividendoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DividendoResponse:
    """Registra um dividendo para um investimento do usuário."""
    usuario_id = current_user["user_id"]
    investimento = (
        db.query(Investimento)
        .filter(Investimento.id == investimento_id, Investimento.usuario_id == usuario_id)
        .first()
    )
    if not investimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado",
        )

    dividendo = Dividendo(
        investimento_id=investimento_id,
        valor=data.valor,
        data=data.data,
    )
    db.add(dividendo)
    db.commit()
    db.refresh(dividendo)
    return DividendoResponse.model_validate(dividendo)


@router.delete("/dividendos/{dividendo_id}", status_code=204)
def excluir_dividendo(
    dividendo_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui um dividendo, verificando que pertence ao usuário."""
    usuario_id = current_user["user_id"]
    dividendo = (
        db.query(Dividendo)
        .join(Investimento, Dividendo.investimento_id == Investimento.id)
        .filter(Dividendo.id == dividendo_id, Investimento.usuario_id == usuario_id)
        .first()
    )
    if not dividendo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dividendo não encontrado",
        )

    db.delete(dividendo)
    db.commit()
