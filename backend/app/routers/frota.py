"""Router de frota: CRUD veículos, abastecimentos, manutenções e consumo médio."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.abastecimento import Abastecimento
from app.models.manutencao import Manutencao
from app.models.veiculo import Veiculo
from app.schemas.frota import (
    AbastecimentoCreate,
    AbastecimentoResponse,
    AbastecimentoUpdate,
    ConsumoMedioResponse,
    ManutencaoCreate,
    ManutencaoResponse,
    ManutencaoUpdate,
    VeiculoCreate,
    VeiculoResponse,
    VeiculoUpdate,
)

router = APIRouter()


def _get_veiculo_do_usuario(
    db: Session, veiculo_id: int, usuario_id: int,
) -> Veiculo:
    """Busca veículo garantindo que pertence ao usuário. Levanta 404 se não encontrado."""
    veiculo = (
        db.query(Veiculo)
        .filter(Veiculo.id == veiculo_id, Veiculo.usuario_id == usuario_id)
        .first()
    )
    if not veiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Veículo não encontrado",
        )
    return veiculo


# ---------------------------------------------------------------------------
# Veículos CRUD
# ---------------------------------------------------------------------------


@router.get("/veiculos", response_model=list[VeiculoResponse])
def listar_veiculos(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[VeiculoResponse]:
    """Lista todos os veículos do usuário."""
    usuario_id = current_user["user_id"]
    veiculos = (
        db.query(Veiculo)
        .filter(Veiculo.usuario_id == usuario_id)
        .all()
    )
    return [VeiculoResponse.model_validate(v) for v in veiculos]


@router.post("/veiculos", response_model=VeiculoResponse, status_code=201)
def criar_veiculo(
    data: VeiculoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VeiculoResponse:
    """Cria um novo veículo para o usuário."""
    usuario_id = current_user["user_id"]
    veiculo = Veiculo(
        usuario_id=usuario_id,
        nome_identificador=data.nome_identificador,
        placa=data.placa,
        modelo=data.modelo,
    )
    db.add(veiculo)
    db.commit()
    db.refresh(veiculo)
    return VeiculoResponse.model_validate(veiculo)


@router.put("/veiculos/{veiculo_id}", response_model=VeiculoResponse)
def atualizar_veiculo(
    veiculo_id: int,
    data: VeiculoUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VeiculoResponse:
    """Atualiza dados de um veículo do usuário."""
    usuario_id = current_user["user_id"]
    veiculo = _get_veiculo_do_usuario(db, veiculo_id, usuario_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(veiculo, field, value)

    db.commit()
    db.refresh(veiculo)
    return VeiculoResponse.model_validate(veiculo)


@router.patch("/veiculos/{veiculo_id}/desativar", response_model=VeiculoResponse)
def desativar_veiculo(
    veiculo_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VeiculoResponse:
    """Desativa um veículo do usuário."""
    usuario_id = current_user["user_id"]
    veiculo = _get_veiculo_do_usuario(db, veiculo_id, usuario_id)

    veiculo.status = False
    db.commit()
    db.refresh(veiculo)
    return VeiculoResponse.model_validate(veiculo)


# ---------------------------------------------------------------------------
# Abastecimentos CRUD
# ---------------------------------------------------------------------------


@router.get("/veiculos/{veiculo_id}/abastecimentos", response_model=list[AbastecimentoResponse])
def listar_abastecimentos(
    veiculo_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AbastecimentoResponse]:
    """Lista abastecimentos de um veículo do usuário."""
    usuario_id = current_user["user_id"]
    _get_veiculo_do_usuario(db, veiculo_id, usuario_id)

    abastecimentos = (
        db.query(Abastecimento)
        .filter(Abastecimento.veiculo_id == veiculo_id)
        .order_by(Abastecimento.data.desc())
        .all()
    )
    return [AbastecimentoResponse.model_validate(a) for a in abastecimentos]


@router.post("/veiculos/{veiculo_id}/abastecimentos", response_model=AbastecimentoResponse, status_code=201)
def registrar_abastecimento(
    veiculo_id: int,
    data: AbastecimentoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AbastecimentoResponse:
    """Registra um abastecimento para um veículo do usuário."""
    usuario_id = current_user["user_id"]
    _get_veiculo_do_usuario(db, veiculo_id, usuario_id)

    abastecimento = Abastecimento(
        veiculo_id=veiculo_id,
        data=data.data,
        litros=data.litros,
        valor=data.valor,
        km=data.km,
        posto=data.posto,
        tipo=data.tipo,
        litros_gasolina=data.litros_gasolina,
        litros_etanol=data.litros_etanol,
    )
    db.add(abastecimento)
    db.commit()
    db.refresh(abastecimento)
    return AbastecimentoResponse.model_validate(abastecimento)


@router.put("/abastecimentos/{abastecimento_id}", response_model=AbastecimentoResponse)
def atualizar_abastecimento(
    abastecimento_id: int,
    data: AbastecimentoUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AbastecimentoResponse:
    """Atualiza um abastecimento, verificando que o veículo pertence ao usuário."""
    usuario_id = current_user["user_id"]
    abastecimento = (
        db.query(Abastecimento)
        .join(Veiculo, Abastecimento.veiculo_id == Veiculo.id)
        .filter(Abastecimento.id == abastecimento_id, Veiculo.usuario_id == usuario_id)
        .first()
    )
    if not abastecimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Abastecimento não encontrado",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(abastecimento, field, value)

    db.commit()
    db.refresh(abastecimento)
    return AbastecimentoResponse.model_validate(abastecimento)


@router.delete("/abastecimentos/{abastecimento_id}", status_code=204)
def excluir_abastecimento(
    abastecimento_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui um abastecimento, verificando que o veículo pertence ao usuário."""
    usuario_id = current_user["user_id"]
    abastecimento = (
        db.query(Abastecimento)
        .join(Veiculo, Abastecimento.veiculo_id == Veiculo.id)
        .filter(Abastecimento.id == abastecimento_id, Veiculo.usuario_id == usuario_id)
        .first()
    )
    if not abastecimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Abastecimento não encontrado",
        )

    db.delete(abastecimento)
    db.commit()


# ---------------------------------------------------------------------------
# Manutenções CRUD
# ---------------------------------------------------------------------------


@router.get("/veiculos/{veiculo_id}/manutencoes", response_model=list[ManutencaoResponse])
def listar_manutencoes(
    veiculo_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ManutencaoResponse]:
    """Lista manutenções de um veículo do usuário."""
    usuario_id = current_user["user_id"]
    _get_veiculo_do_usuario(db, veiculo_id, usuario_id)

    manutencoes = (
        db.query(Manutencao)
        .filter(Manutencao.veiculo_id == veiculo_id)
        .order_by(Manutencao.data.desc())
        .all()
    )
    return [ManutencaoResponse.model_validate(m) for m in manutencoes]


@router.post("/veiculos/{veiculo_id}/manutencoes", response_model=ManutencaoResponse, status_code=201)
def registrar_manutencao(
    veiculo_id: int,
    data: ManutencaoCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ManutencaoResponse:
    """Registra uma manutenção para um veículo do usuário."""
    usuario_id = current_user["user_id"]
    _get_veiculo_do_usuario(db, veiculo_id, usuario_id)

    manutencao = Manutencao(
        veiculo_id=veiculo_id,
        data=data.data,
        servico=data.servico,
        valor=data.valor,
        km=data.km,
    )
    db.add(manutencao)
    db.commit()
    db.refresh(manutencao)
    return ManutencaoResponse.model_validate(manutencao)


@router.put("/manutencoes/{manutencao_id}", response_model=ManutencaoResponse)
def atualizar_manutencao(
    manutencao_id: int,
    data: ManutencaoUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ManutencaoResponse:
    """Atualiza uma manutenção, verificando que o veículo pertence ao usuário."""
    usuario_id = current_user["user_id"]
    manutencao = (
        db.query(Manutencao)
        .join(Veiculo, Manutencao.veiculo_id == Veiculo.id)
        .filter(Manutencao.id == manutencao_id, Veiculo.usuario_id == usuario_id)
        .first()
    )
    if not manutencao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manutenção não encontrada",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(manutencao, field, value)

    db.commit()
    db.refresh(manutencao)
    return ManutencaoResponse.model_validate(manutencao)


@router.delete("/manutencoes/{manutencao_id}", status_code=204)
def excluir_manutencao(
    manutencao_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Exclui uma manutenção, verificando que o veículo pertence ao usuário."""
    usuario_id = current_user["user_id"]
    manutencao = (
        db.query(Manutencao)
        .join(Veiculo, Manutencao.veiculo_id == Veiculo.id)
        .filter(Manutencao.id == manutencao_id, Veiculo.usuario_id == usuario_id)
        .first()
    )
    if not manutencao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manutenção não encontrada",
        )

    db.delete(manutencao)
    db.commit()


# ---------------------------------------------------------------------------
# Consumo Médio
# ---------------------------------------------------------------------------


@router.get("/veiculos/{veiculo_id}/consumo", response_model=ConsumoMedioResponse)
def consumo_medio(
    veiculo_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ConsumoMedioResponse:
    """Calcula consumo médio (km/litro) de um veículo baseado em abastecimentos consecutivos.

    Algoritmo:
    - Ordena abastecimentos por km crescente
    - Para cada par consecutivo (i, i+1): consumo = (km[i+1] - km[i]) / litros[i+1]
    - Média de todos os consumos parciais
    - Retorna 0 se menos de 2 abastecimentos com dados de km
    """
    usuario_id = current_user["user_id"]
    _get_veiculo_do_usuario(db, veiculo_id, usuario_id)

    abastecimentos = (
        db.query(Abastecimento)
        .filter(Abastecimento.veiculo_id == veiculo_id)
        .all()
    )

    # Totais gerais
    total_litros = Decimal("0")
    total_valor = Decimal("0")
    for a in abastecimentos:
        if a.litros:
            total_litros += Decimal(str(a.litros))
        total_valor += Decimal(str(a.valor))

    # Filtrar abastecimentos com km e litros válidos para cálculo de consumo
    com_km = [
        a for a in abastecimentos
        if a.km is not None and a.litros is not None and Decimal(str(a.litros)) > 0
    ]
    com_km.sort(key=lambda a: Decimal(str(a.km)))

    consumo_medio_valor = Decimal("0")
    if len(com_km) >= 2:
        consumos = []
        for i in range(len(com_km) - 1):
            km_diff = Decimal(str(com_km[i + 1].km)) - Decimal(str(com_km[i].km))
            litros_next = Decimal(str(com_km[i + 1].litros))
            if km_diff > 0 and litros_next > 0:
                consumos.append(km_diff / litros_next)
        if consumos:
            consumo_medio_valor = sum(consumos) / len(consumos)

    return ConsumoMedioResponse(
        veiculo_id=veiculo_id,
        consumo_medio=consumo_medio_valor.quantize(Decimal("0.01")),
        total_litros=total_litros.quantize(Decimal("0.01")),
        total_valor=total_valor.quantize(Decimal("0.01")),
        total_abastecimentos=len(abastecimentos),
    )
