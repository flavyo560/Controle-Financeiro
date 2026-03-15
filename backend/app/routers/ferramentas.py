"""Router de ferramentas: backup (exportar/importar) dados do usuário."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import (
    Abastecimento,
    Banco,
    Cartao,
    Categoria,
    CompraCartao,
    Configuracao,
    Despesa,
    DespesaParcelada,
    DespesaRecorrente,
    Dividendo,
    HistoricoOrcamento,
    Investimento,
    ItemOrcamento,
    Manutencao,
    Orcamento,
    PagamentoFatura,
    Receita,
    Transferencia,
    Veiculo,
)

router = APIRouter()

# Ordem de exportação/importação respeita dependências de FK
_TABELAS_EXPORT = [
    ("bancos", Banco),
    ("categorias", Categoria),
    ("receitas", Receita),
    ("despesas_parceladas", DespesaParcelada),
    ("despesas_recorrentes", DespesaRecorrente),
    ("despesas", Despesa),
    ("cartoes", Cartao),
    ("compras_cartao", CompraCartao),
    ("pagamentos_fatura", PagamentoFatura),
    ("investimentos", Investimento),
    ("dividendos", Dividendo),
    ("transferencias", Transferencia),
    ("veiculos", Veiculo),
    ("abastecimentos", Abastecimento),
    ("manutencoes", Manutencao),
    ("orcamentos", Orcamento),
    ("itens_orcamento", ItemOrcamento),
    ("historico_orcamento", HistoricoOrcamento),
    ("configuracoes", Configuracao),
]

# Tabelas com usuario_id direto
_TABELAS_COM_USUARIO = {
    "bancos", "categorias", "receitas", "despesas_parceladas",
    "despesas_recorrentes", "despesas", "cartoes", "investimentos",
    "transferencias", "veiculos", "orcamentos", "configuracoes",
}

# Tabelas filhas (filtradas via FK para tabela pai)
_TABELAS_FILHAS: dict[str, tuple[str, Any]] = {
    "compras_cartao": ("cartao_id", Cartao),
    "pagamentos_fatura": ("cartao_id", Cartao),
    "dividendos": ("investimento_id", Investimento),
    "abastecimentos": ("veiculo_id", Veiculo),
    "manutencoes": ("veiculo_id", Veiculo),
    "itens_orcamento": ("orcamento_id", Orcamento),
    "historico_orcamento": ("item_orcamento_id", ItemOrcamento),
}


def _serialize(obj: Any) -> Any:
    """Converte um objeto SQLAlchemy para dict serializável."""
    data = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, (datetime, date)):
            data[col.name] = val.isoformat()
        elif isinstance(val, Decimal):
            data[col.name] = float(val)
        else:
            data[col.name] = val
    return data


@router.get("/backup/exportar")
def exportar_backup(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    """Exporta todos os dados do usuário em JSON."""
    usuario_id = current_user["user_id"]
    backup: dict[str, list[dict]] = {}

    for nome_tabela, modelo in _TABELAS_EXPORT:
        if nome_tabela in _TABELAS_COM_USUARIO:
            registros = db.query(modelo).filter(
                modelo.usuario_id == usuario_id
            ).all()
        elif nome_tabela in _TABELAS_FILHAS:
            fk_col, pai_modelo = _TABELAS_FILHAS[nome_tabela]
            ids_pai = [
                r.id for r in db.query(pai_modelo.id).filter(
                    pai_modelo.usuario_id == usuario_id
                ).all()
            ] if hasattr(pai_modelo, "usuario_id") else _get_ids_filha(
                db, nome_tabela, fk_col, pai_modelo, usuario_id
            )
            registros = db.query(modelo).filter(
                getattr(modelo, fk_col).in_(ids_pai)
            ).all() if ids_pai else []
        else:
            registros = []

        backup[nome_tabela] = [_serialize(r) for r in registros]

    return JSONResponse(
        content={"version": "1.0", "data": backup},
        headers={"Content-Disposition": "attachment; filename=backup_financeiro.json"},
    )


def _get_ids_filha(
    db: Session, nome_tabela: str, fk_col: str,
    pai_modelo: Any, usuario_id: int,
) -> list[int]:
    """Resolve IDs para tabelas filhas de segundo nível (ex: historico_orcamento)."""
    if nome_tabela == "historico_orcamento":
        orc_ids = [r.id for r in db.query(Orcamento.id).filter(
            Orcamento.usuario_id == usuario_id
        ).all()]
        if not orc_ids:
            return []
        return [r.id for r in db.query(ItemOrcamento.id).filter(
            ItemOrcamento.orcamento_id.in_(orc_ids)
        ).all()]
    return []


# Mapeamento de tabelas válidas para importação
_TABELAS_IMPORT_ORDER = [
    "bancos", "categorias", "receitas", "despesas_parceladas",
    "despesas_recorrentes", "despesas", "cartoes", "compras_cartao",
    "pagamentos_fatura", "investimentos", "dividendos", "transferencias",
    "veiculos", "abastecimentos", "manutencoes", "orcamentos",
    "itens_orcamento", "historico_orcamento", "configuracoes",
]

_MODELO_MAP: dict[str, Any] = {nome: modelo for nome, modelo in _TABELAS_EXPORT}

_CAMPOS_OBRIGATORIOS: dict[str, list[str]] = {
    "bancos": ["nome"],
    "categorias": ["nome", "tipo"],
    "receitas": ["valor", "data"],
    "despesas": ["valor", "data"],
    "despesas_parceladas": ["descricao", "valor_total", "numero_parcelas", "data_primeira_parcela"],
    "despesas_recorrentes": ["descricao", "valor", "dia_mes", "data_inicio"],
    "cartoes": ["nome", "limite_total", "dia_fechamento", "dia_vencimento"],
    "compras_cartao": ["descricao", "valor", "data_compra", "mes_fatura"],
    "pagamentos_fatura": ["mes_fatura", "valor_pago", "data_pagamento"],
    "investimentos": ["nome", "valor_investido", "data"],
    "dividendos": ["valor", "data"],
    "transferencias": ["valor", "data"],
    "veiculos": ["nome_identificador"],
    "abastecimentos": ["data", "valor"],
    "manutencoes": ["data", "valor"],
    "orcamentos": ["ano"],
    "itens_orcamento": ["mes", "valor_planejado"],
    "historico_orcamento": ["valor_anterior", "valor_novo"],
    "configuracoes": ["chave"],
}


@router.post("/backup/importar")
def importar_backup(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    backup_data: dict,
) -> dict:
    """Importa dados de backup JSON com validação e remapeamento de IDs."""
    usuario_id = current_user["user_id"]
    erros: list[str] = []

    # Validar estrutura
    if "data" not in backup_data or not isinstance(backup_data["data"], dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de backup inválido: campo 'data' ausente ou inválido",
        )

    dados = backup_data["data"]

    # Validar campos obrigatórios por tabela
    for tabela, registros in dados.items():
        if tabela not in _MODELO_MAP:
            erros.append(f"Tabela desconhecida: {tabela}")
            continue
        if not isinstance(registros, list):
            erros.append(f"Tabela '{tabela}' deve ser uma lista")
            continue
        campos_req = _CAMPOS_OBRIGATORIOS.get(tabela, [])
        for i, reg in enumerate(registros):
            if not isinstance(reg, dict):
                erros.append(f"{tabela}[{i}]: registro inválido")
                continue
            for campo in campos_req:
                if campo not in reg or reg[campo] is None:
                    erros.append(f"{tabela}[{i}]: campo obrigatório '{campo}' ausente")

    if erros:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Backup contém dados inválidos", "errors": erros},
        )

    # Importar com remapeamento de IDs
    id_map: dict[str, dict[int, int]] = {}
    total_importado: dict[str, int] = {}

    try:
        for tabela in _TABELAS_IMPORT_ORDER:
            if tabela not in dados:
                continue

            modelo = _MODELO_MAP[tabela]
            registros = dados[tabela]
            id_map[tabela] = {}
            count = 0

            for reg in registros:
                old_id = reg.pop("id", None)
                reg.pop("criado_em", None)
                reg.pop("atualizado_em", None)

                # Setar usuario_id
                if tabela in _TABELAS_COM_USUARIO:
                    reg["usuario_id"] = usuario_id

                # Remapear FKs
                _remapear_fks(reg, tabela, id_map)

                novo = modelo(**reg)
                db.add(novo)
                db.flush()

                if old_id is not None:
                    id_map[tabela][old_id] = novo.id
                count += 1

            total_importado[tabela] = count

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao importar backup: {str(e)}",
        )

    return {
        "message": "Backup importado com sucesso",
        "registros_importados": total_importado,
    }


def _remapear_fks(reg: dict, tabela: str, id_map: dict[str, dict[int, int]]) -> None:
    """Remapeia foreign keys usando o mapa de IDs antigo→novo."""
    fk_mappings: dict[str, list[tuple[str, str]]] = {
        "receitas": [("categoria_id", "categorias"), ("banco_id", "bancos")],
        "despesas": [
            ("categoria_id", "categorias"), ("banco_id", "bancos"),
            ("despesa_parcelada_id", "despesas_parceladas"),
            ("despesa_recorrente_id", "despesas_recorrentes"),
            ("cartao_id", "cartoes"),
        ],
        "despesas_parceladas": [("categoria_id", "categorias"), ("banco_id", "bancos")],
        "despesas_recorrentes": [("categoria_id", "categorias"), ("banco_id", "bancos")],
        "compras_cartao": [("cartao_id", "cartoes"), ("categoria_id", "categorias")],
        "pagamentos_fatura": [("cartao_id", "cartoes"), ("banco_id", "bancos"), ("despesa_id", "despesas")],
        "investimentos": [("categoria_id", "categorias"), ("banco_id", "bancos")],
        "dividendos": [("investimento_id", "investimentos")],
        "transferencias": [("banco_origem_id", "bancos"), ("banco_destino_id", "bancos")],
        "abastecimentos": [("veiculo_id", "veiculos")],
        "manutencoes": [("veiculo_id", "veiculos")],
        "itens_orcamento": [("orcamento_id", "orcamentos"), ("categoria_id", "categorias")],
        "historico_orcamento": [("item_orcamento_id", "itens_orcamento"), ("usuario_id", "")],
    }

    for fk_col, ref_tabela in fk_mappings.get(tabela, []):
        if fk_col in reg and reg[fk_col] is not None and ref_tabela in id_map:
            old_fk = reg[fk_col]
            if isinstance(old_fk, int) and old_fk in id_map[ref_tabela]:
                reg[fk_col] = id_map[ref_tabela][old_fk]
