"""Router de orçamento: CRUD, itens, análise, projeções e sugestões."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.historico_orcamento import HistoricoOrcamento
from app.models.item_orcamento import ItemOrcamento
from app.models.orcamento import Orcamento
from app.schemas.orcamento import (
    HistoricoOrcamentoResponse,
    ItemOrcamentoCreate,
    ItemOrcamentoResponse,
    OrcamentoCreate,
    OrcamentoResponse,
    OrcamentoStatusUpdate,
    PercentuaisResponse,
    ProjecaoResponse,
    RealizadosResponse,
    SugestaoResponse,
    TotaisMensaisResponse,
)
from app.services import orcamento_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_orcamento_or_404(
    db: Session, orcamento_id: int, usuario_id: int,
) -> Orcamento:
    orc = (
        db.query(Orcamento)
        .filter(Orcamento.id == orcamento_id, Orcamento.usuario_id == usuario_id)
        .first()
    )
    if not orc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orçamento não encontrado",
        )
    return orc


# ---------------------------------------------------------------------------
# CRUD Orçamento
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[OrcamentoResponse])
def listar_orcamentos(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[OrcamentoResponse]:
    """Lista todos os orçamentos do usuário."""
    usuario_id = current_user["user_id"]
    orcamentos = (
        db.query(Orcamento)
        .filter(Orcamento.usuario_id == usuario_id)
        .order_by(Orcamento.ano.desc())
        .all()
    )
    return [OrcamentoResponse.model_validate(o) for o in orcamentos]


@router.post("/", response_model=OrcamentoResponse, status_code=201)
def criar_orcamento(
    data: OrcamentoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrcamentoResponse:
    """Cria um novo orçamento anual."""
    usuario_id = current_user["user_id"]

    # Check uniqueness (usuario_id + ano)
    existente = (
        db.query(Orcamento)
        .filter(Orcamento.usuario_id == usuario_id, Orcamento.ano == data.ano)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um orçamento para o ano {data.ano}",
        )

    orcamento = Orcamento(
        usuario_id=usuario_id,
        ano=data.ano,
        status="ativo",
    )
    db.add(orcamento)
    db.commit()
    db.refresh(orcamento)
    return OrcamentoResponse.model_validate(orcamento)


@router.put("/{orcamento_id}/status", response_model=OrcamentoResponse)
def atualizar_status(
    orcamento_id: int,
    data: OrcamentoStatusUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrcamentoResponse:
    """Atualiza o status (ativo/inativo) de um orçamento."""
    usuario_id = current_user["user_id"]
    orc = _get_orcamento_or_404(db, orcamento_id, usuario_id)
    orc.status = data.status
    db.commit()
    db.refresh(orc)
    return OrcamentoResponse.model_validate(orc)


@router.delete("/{orcamento_id}", status_code=204)
def excluir_orcamento(
    orcamento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui um orçamento e todos os seus itens (cascade)."""
    usuario_id = current_user["user_id"]
    orc = _get_orcamento_or_404(db, orcamento_id, usuario_id)
    db.delete(orc)
    db.commit()


# ---------------------------------------------------------------------------
# Itens de Orçamento
# ---------------------------------------------------------------------------

@router.get("/{orcamento_id}/itens", response_model=list[ItemOrcamentoResponse])
def listar_itens(
    orcamento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ItemOrcamentoResponse]:
    """Lista itens de um orçamento."""
    usuario_id = current_user["user_id"]
    _get_orcamento_or_404(db, orcamento_id, usuario_id)

    itens = (
        db.query(ItemOrcamento)
        .filter(ItemOrcamento.orcamento_id == orcamento_id)
        .order_by(ItemOrcamento.categoria_id, ItemOrcamento.mes)
        .all()
    )
    return [ItemOrcamentoResponse.model_validate(i) for i in itens]


@router.post("/{orcamento_id}/itens", response_model=ItemOrcamentoResponse, status_code=201)
def criar_ou_atualizar_item(
    orcamento_id: int,
    data: ItemOrcamentoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ItemOrcamentoResponse:
    """Cria ou atualiza um item de orçamento. Registra histórico se valor mudou."""
    usuario_id = current_user["user_id"]
    orc = _get_orcamento_or_404(db, orcamento_id, usuario_id)
    item = orcamento_service.criar_ou_atualizar_item(db, orc, data, usuario_id)
    return ItemOrcamentoResponse.model_validate(item)


# ---------------------------------------------------------------------------
# Análise: Realizados, Percentuais, Totais Mensais
# ---------------------------------------------------------------------------

@router.get("/{orcamento_id}/realizados", response_model=RealizadosResponse)
def obter_realizados(
    orcamento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RealizadosResponse:
    """Valores realizados por categoria e mês."""
    usuario_id = current_user["user_id"]
    orc = _get_orcamento_or_404(db, orcamento_id, usuario_id)
    itens = orcamento_service.calcular_realizados(db, orc, usuario_id)
    return RealizadosResponse(orcamento_id=orc.id, ano=orc.ano, itens=itens)


@router.get("/{orcamento_id}/percentuais", response_model=PercentuaisResponse)
def obter_percentuais(
    orcamento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PercentuaisResponse:
    """Percentuais de execução por categoria e mês."""
    usuario_id = current_user["user_id"]
    orc = _get_orcamento_or_404(db, orcamento_id, usuario_id)
    itens = orcamento_service.calcular_percentuais(db, orc, usuario_id)
    return PercentuaisResponse(orcamento_id=orc.id, ano=orc.ano, itens=itens)


@router.get("/{orcamento_id}/totais-mensais", response_model=TotaisMensaisResponse)
def obter_totais_mensais(
    orcamento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TotaisMensaisResponse:
    """Totais planejados vs realizados por mês."""
    usuario_id = current_user["user_id"]
    orc = _get_orcamento_or_404(db, orcamento_id, usuario_id)
    meses = orcamento_service.calcular_totais_mensais(db, orc, usuario_id)
    return TotaisMensaisResponse(orcamento_id=orc.id, ano=orc.ano, meses=meses)


# ---------------------------------------------------------------------------
# Projeções e Sugestões
# ---------------------------------------------------------------------------

@router.get("/{orcamento_id}/projecoes", response_model=ProjecaoResponse)
def obter_projecoes(
    orcamento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjecaoResponse:
    """Projeções de gastos futuros por categoria."""
    usuario_id = current_user["user_id"]
    orc = _get_orcamento_or_404(db, orcamento_id, usuario_id)
    mes_atual, categorias = orcamento_service.calcular_projecoes(db, orc, usuario_id)
    return ProjecaoResponse(
        orcamento_id=orc.id,
        ano=orc.ano,
        mes_atual=mes_atual,
        categorias=categorias,
    )


@router.get("/{orcamento_id}/sugestoes", response_model=SugestaoResponse)
def obter_sugestoes(
    orcamento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SugestaoResponse:
    """Sugestões de ajuste de orçamento."""
    usuario_id = current_user["user_id"]
    orc = _get_orcamento_or_404(db, orcamento_id, usuario_id)
    sugestoes = orcamento_service.calcular_sugestoes(db, orc, usuario_id)
    return SugestaoResponse(orcamento_id=orc.id, ano=orc.ano, sugestoes=sugestoes)


# ---------------------------------------------------------------------------
# Cópia e Histórico
# ---------------------------------------------------------------------------

@router.post("/{orcamento_id}/copiar/{ano_destino}", response_model=OrcamentoResponse, status_code=201)
def copiar_orcamento(
    orcamento_id: int,
    ano_destino: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrcamentoResponse:
    """Copia orçamento para outro ano."""
    usuario_id = current_user["user_id"]
    orc = _get_orcamento_or_404(db, orcamento_id, usuario_id)

    # Check if destination already exists
    existente = (
        db.query(Orcamento)
        .filter(Orcamento.usuario_id == usuario_id, Orcamento.ano == ano_destino)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um orçamento para o ano {ano_destino}",
        )

    novo = orcamento_service.copiar_orcamento(db, orc, ano_destino, usuario_id)
    return OrcamentoResponse.model_validate(novo)


@router.get("/{orcamento_id}/historico", response_model=list[HistoricoOrcamentoResponse])
def obter_historico(
    orcamento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[HistoricoOrcamentoResponse]:
    """Histórico de alterações de itens do orçamento."""
    usuario_id = current_user["user_id"]
    _get_orcamento_or_404(db, orcamento_id, usuario_id)

    # Get all item IDs for this orcamento
    item_ids = [
        i.id
        for i in db.query(ItemOrcamento.id)
        .filter(ItemOrcamento.orcamento_id == orcamento_id)
        .all()
    ]
    if not item_ids:
        return []

    historicos = (
        db.query(HistoricoOrcamento)
        .filter(HistoricoOrcamento.item_orcamento_id.in_(item_ids))
        .order_by(HistoricoOrcamento.data_alteracao.desc())
        .all()
    )
    return [HistoricoOrcamentoResponse.model_validate(h) for h in historicos]
