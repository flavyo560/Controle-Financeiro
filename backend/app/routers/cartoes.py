"""Router de cartões de crédito: CRUD, compras, faturas e pagamentos."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.cartao import Cartao
from app.schemas.cartao import (
    CartaoCreate,
    CartaoResponse,
    CartaoUpdate,
    CompraCartaoCreate,
    CompraCartaoResponse,
    CompraParceladaCreate,
    FaturaResponse,
    PagamentoFaturaCreate,
    PagamentoFaturaResponse,
)
from app.services.cartao_service import (
    atualizar_cartao,
    calcular_limite_utilizado,
    listar_faturas,
    obter_fatura,
    pagar_fatura,
    registrar_compra_avista,
    registrar_compra_parcelada,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_cartao_or_404(
    db: Session, cartao_id: int, usuario_id: int,
) -> Cartao:
    """Busca cartão do usuário ou levanta 404."""
    cartao = (
        db.query(Cartao)
        .filter(Cartao.id == cartao_id, Cartao.usuario_id == usuario_id)
        .first()
    )
    if not cartao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cartão não encontrado",
        )
    return cartao


def _build_cartao_response(db: Session, cartao: Cartao) -> CartaoResponse:
    """Constrói CartaoResponse com limites calculados."""
    limite_utilizado = calcular_limite_utilizado(db, cartao.id)
    limite_disponivel = max(cartao.limite_total - limite_utilizado, 0)
    return CartaoResponse(
        id=cartao.id,
        nome=cartao.nome,
        bandeira=cartao.bandeira,
        limite_total=cartao.limite_total,
        dia_fechamento=cartao.dia_fechamento,
        dia_vencimento=cartao.dia_vencimento,
        status=cartao.status,
        limite_utilizado=limite_utilizado,
        limite_disponivel=limite_disponivel,
    )


# ---------------------------------------------------------------------------
# CRUD Cartão
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[CartaoResponse])
def listar_cartoes(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[CartaoResponse]:
    """Lista cartões do usuário com limites calculados."""
    usuario_id = current_user["user_id"]
    cartoes = (
        db.query(Cartao)
        .filter(Cartao.usuario_id == usuario_id)
        .order_by(Cartao.nome)
        .all()
    )
    return [_build_cartao_response(db, c) for c in cartoes]


@router.post("/", response_model=CartaoResponse, status_code=201)
def criar_cartao(
    data: CartaoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CartaoResponse:
    """Cria um novo cartão de crédito."""
    usuario_id = current_user["user_id"]
    cartao = Cartao(
        usuario_id=usuario_id,
        nome=data.nome,
        limite_total=data.limite_total,
        dia_fechamento=data.dia_fechamento,
        dia_vencimento=data.dia_vencimento,
        bandeira=data.bandeira,
    )
    db.add(cartao)
    db.commit()
    db.refresh(cartao)
    return _build_cartao_response(db, cartao)


@router.put("/{cartao_id}", response_model=CartaoResponse)
def editar_cartao(
    cartao_id: int,
    data: CartaoUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CartaoResponse:
    """Atualiza dados do cartão. Rejeita redução de limite abaixo do utilizado."""
    usuario_id = current_user["user_id"]
    cartao = _get_cartao_or_404(db, cartao_id, usuario_id)
    atualizar_cartao(db, cartao, data)
    return _build_cartao_response(db, cartao)


@router.patch("/{cartao_id}/desativar", response_model=CartaoResponse)
def desativar_cartao(
    cartao_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CartaoResponse:
    """Desativa um cartão de crédito."""
    usuario_id = current_user["user_id"]
    cartao = _get_cartao_or_404(db, cartao_id, usuario_id)
    cartao.status = False
    db.commit()
    db.refresh(cartao)
    return _build_cartao_response(db, cartao)


@router.delete("/{cartao_id}", status_code=204)
def excluir_cartao(
    cartao_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui um cartão de crédito."""
    usuario_id = current_user["user_id"]
    cartao = _get_cartao_or_404(db, cartao_id, usuario_id)
    db.delete(cartao)
    db.commit()


# ---------------------------------------------------------------------------
# Compras
# ---------------------------------------------------------------------------

@router.post("/{cartao_id}/compras", response_model=CompraCartaoResponse, status_code=201)
def criar_compra_avista(
    cartao_id: int,
    data: CompraCartaoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CompraCartaoResponse:
    """Registra compra à vista no cartão."""
    usuario_id = current_user["user_id"]
    cartao = _get_cartao_or_404(db, cartao_id, usuario_id)
    compra = registrar_compra_avista(db, cartao, data)
    return CompraCartaoResponse.model_validate(compra)


@router.post(
    "/{cartao_id}/compras/parcelada",
    response_model=list[CompraCartaoResponse],
    status_code=201,
)
def criar_compra_parcelada(
    cartao_id: int,
    data: CompraParceladaCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[CompraCartaoResponse]:
    """Registra compra parcelada no cartão, gerando parcelas em meses consecutivos."""
    usuario_id = current_user["user_id"]
    cartao = _get_cartao_or_404(db, cartao_id, usuario_id)
    compras = registrar_compra_parcelada(db, cartao, data)
    return [CompraCartaoResponse.model_validate(c) for c in compras]


# ---------------------------------------------------------------------------
# Faturas
# ---------------------------------------------------------------------------

@router.get("/{cartao_id}/faturas", response_model=list[str])
def listar_faturas_cartao(
    cartao_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[str]:
    """Lista meses de fatura disponíveis para o cartão."""
    usuario_id = current_user["user_id"]
    cartao = _get_cartao_or_404(db, cartao_id, usuario_id)
    return listar_faturas(db, cartao)


@router.get("/{cartao_id}/faturas/{mes_fatura}", response_model=FaturaResponse)
def detalhe_fatura(
    cartao_id: int,
    mes_fatura: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FaturaResponse:
    """Retorna detalhes da fatura de um mês específico."""
    usuario_id = current_user["user_id"]
    cartao = _get_cartao_or_404(db, cartao_id, usuario_id)
    fatura_data = obter_fatura(db, cartao, mes_fatura)
    return FaturaResponse(
        compras=[CompraCartaoResponse.model_validate(c) for c in fatura_data["compras"]],
        valor_total=fatura_data["valor_total"],
        valor_pago=fatura_data["valor_pago"],
        saldo_devedor=fatura_data["saldo_devedor"],
        data_vencimento=fatura_data["data_vencimento"],
        status=fatura_data["status"],
    )


@router.post(
    "/{cartao_id}/faturas/{mes_fatura}/pagar",
    response_model=PagamentoFaturaResponse,
    status_code=201,
)
def pagar_fatura_endpoint(
    cartao_id: int,
    mes_fatura: str,
    data: PagamentoFaturaCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PagamentoFaturaResponse:
    """Registra pagamento de fatura e cria despesa correspondente no banco."""
    usuario_id = current_user["user_id"]
    cartao = _get_cartao_or_404(db, cartao_id, usuario_id)
    pagamento = pagar_fatura(db, cartao, mes_fatura, data, usuario_id)
    return PagamentoFaturaResponse.model_validate(pagamento)
