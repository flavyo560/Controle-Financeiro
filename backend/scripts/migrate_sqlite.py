#!/usr/bin/env python3
"""Script de migração SQLite → Supabase (PostgreSQL).

Uso:
    python migrate_sqlite.py --sqlite-path /caminho/banco.db \
        --supabase-url postgresql://user:pass@host:5432/db \
        --supabase-key <opcional>

Conversões de tipo:
    TEXT (datas) → DATE / TIMESTAMPTZ
    REAL (monetário) → NUMERIC
    INTEGER (boolean) → BOOLEAN

Preserva senha_hash (SHA-256) e senha_hash_bcrypt.
Inserção em batches de 500 registros.
Rollback por tabela em caso de falha.
Relatório final com contagem de registros migrados e erros.
"""

import argparse
import logging
import sqlite3
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 500

# Ordem de migração respeitando dependências de FK
TABELAS_ORDEM = [
    "usuarios",
    "bancos",
    "categorias",
    "receitas",
    "despesas_parceladas",
    "despesas_recorrentes",
    "cartoes",
    "despesas",
    "compras_cartao",
    "pagamentos_fatura",
    "investimentos",
    "dividendos",
    "transferencias",
    "veiculos",
    "abastecimentos",
    "manutencoes",
    "orcamentos",
    "itens_orcamento",
    "historico_orcamento",
    "configuracoes",
]

# Colunas que são datas (TEXT no SQLite → DATE no PostgreSQL)
COLUNAS_DATE: dict[str, set[str]] = {
    "receitas": {"data"},
    "despesas": {"data", "data_vencimento", "data_pagamento"},
    "despesas_parceladas": {"data_primeira_parcela"},
    "despesas_recorrentes": {"data_inicio", "data_fim"},
    "compras_cartao": {"data_compra"},
    "pagamentos_fatura": {"data_pagamento"},
    "investimentos": {"data"},
    "dividendos": {"data"},
    "transferencias": {"data"},
    "abastecimentos": {"data"},
    "manutencoes": {"data"},
}

# Colunas que são timestamps (TEXT no SQLite → TIMESTAMPTZ no PostgreSQL)
COLUNAS_TIMESTAMP: dict[str, set[str]] = {
    "usuarios": {"criado_em"},
    "bancos": {"criado_em"},
    "categorias": {"criado_em"},
    "despesas_parceladas": {"criado_em"},
    "despesas_recorrentes": {"criado_em"},
    "cartoes": {"criado_em"},
    "compras_cartao": {"criado_em"},
    "pagamentos_fatura": {"criado_em"},
    "investimentos": {"criado_em"},
    "orcamentos": {"criado_em", "atualizado_em"},
    "itens_orcamento": {"criado_em", "atualizado_em"},
    "historico_orcamento": {"data_alteracao"},
}

# Colunas monetárias (REAL no SQLite → NUMERIC no PostgreSQL)
COLUNAS_NUMERIC: dict[str, set[str]] = {
    "bancos": {"saldo_inicial"},
    "receitas": {"valor"},
    "despesas": {"valor"},
    "despesas_parceladas": {"valor_total"},
    "despesas_recorrentes": {"valor"},
    "cartoes": {"limite_total"},
    "compras_cartao": {"valor"},
    "pagamentos_fatura": {"valor_pago"},
    "investimentos": {"valor_investido", "valor_atual"},
    "dividendos": {"valor"},
    "transferencias": {"valor"},
    "abastecimentos": {"litros", "valor", "litros_gasolina", "litros_etanol"},
    "manutencoes": {"valor"},
    "itens_orcamento": {"valor_planejado"},
    "historico_orcamento": {"valor_anterior", "valor_novo"},
}

# Colunas booleanas (INTEGER no SQLite → BOOLEAN no PostgreSQL)
COLUNAS_BOOLEAN: dict[str, set[str]] = {
    "bancos": {"ativo"},
    "categorias": {"ativo"},
    "receitas": {"ativo"},
    "despesas": {"pago", "ativo"},
    "despesas_recorrentes": {"ativa"},
    "cartoes": {"status"},
    "investimentos": {"ativo"},
    "veiculos": {"status"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrar SQLite → Supabase PostgreSQL")
    parser.add_argument("--sqlite-path", required=True, help="Caminho do arquivo SQLite")
    parser.add_argument("--supabase-url", required=True, help="URL de conexão PostgreSQL")
    parser.add_argument("--supabase-key", default="", help="Chave Supabase (opcional)")
    return parser.parse_args()


def converter_valor(tabela: str, coluna: str, valor):
    """Converte um valor SQLite para o tipo PostgreSQL correto."""
    if valor is None:
        return None

    # DATE
    if coluna in COLUNAS_DATE.get(tabela, set()):
        if isinstance(valor, str):
            try:
                return date.fromisoformat(valor[:10])
            except ValueError:
                return None
        return valor

    # TIMESTAMPTZ
    if coluna in COLUNAS_TIMESTAMP.get(tabela, set()):
        if isinstance(valor, str):
            try:
                return datetime.fromisoformat(valor.replace("Z", "+00:00"))
            except ValueError:
                try:
                    return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return datetime.now()
        return valor

    # NUMERIC
    if coluna in COLUNAS_NUMERIC.get(tabela, set()):
        try:
            return Decimal(str(valor))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    # BOOLEAN
    if coluna in COLUNAS_BOOLEAN.get(tabela, set()):
        if isinstance(valor, int):
            return bool(valor)
        if isinstance(valor, str):
            return valor.lower() in ("1", "true", "sim")
        return bool(valor)

    return valor


def get_sqlite_tables(conn: sqlite3.Connection) -> set[str]:
    """Retorna nomes das tabelas existentes no SQLite."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return {row[0] for row in cursor.fetchall()}


def get_sqlite_columns(conn: sqlite3.Connection, tabela: str) -> list[str]:
    """Retorna nomes das colunas de uma tabela SQLite."""
    cursor = conn.execute(f"PRAGMA table_info({tabela})")
    return [row[1] for row in cursor.fetchall()]


def migrar_tabela(
    sqlite_conn: sqlite3.Connection,
    pg_session,
    tabela: str,
    id_map: dict[str, dict[int, int]],
) -> tuple[int, list[str]]:
    """Migra uma tabela do SQLite para PostgreSQL.

    Returns:
        (registros_migrados, lista_de_erros)
    """
    erros: list[str] = []

    sqlite_tables = get_sqlite_tables(sqlite_conn)
    if tabela not in sqlite_tables:
        logger.info("Tabela '%s' não existe no SQLite, pulando.", tabela)
        return 0, []

    colunas = get_sqlite_columns(sqlite_conn, tabela)
    cursor = sqlite_conn.execute(f"SELECT * FROM {tabela}")
    rows = cursor.fetchall()

    if not rows:
        logger.info("Tabela '%s': 0 registros.", tabela)
        return 0, []

    id_map[tabela] = {}
    count = 0
    batch: list[dict] = []

    for row in rows:
        registro = dict(zip(colunas, row))
        old_id = registro.pop("id", None)

        # Converter tipos
        for col in list(registro.keys()):
            registro[col] = converter_valor(tabela, col, registro[col])

        # Remapear FKs
        _remapear_fks_migracao(registro, tabela, id_map)

        batch.append({"old_id": old_id, "data": registro})

        if len(batch) >= BATCH_SIZE:
            count += _inserir_batch(pg_session, tabela, colunas, batch, id_map, erros)
            batch = []

    if batch:
        count += _inserir_batch(pg_session, tabela, colunas, batch, id_map, erros)

    logger.info("Tabela '%s': %d registros migrados.", tabela, count)
    return count, erros


def _inserir_batch(
    pg_session, tabela: str, colunas_sqlite: list[str],
    batch: list[dict], id_map: dict[str, dict[int, int]],
    erros: list[str],
) -> int:
    """Insere um batch de registros no PostgreSQL via INSERT ... RETURNING id."""
    count = 0
    for item in batch:
        old_id = item["old_id"]
        data = item["data"]
        cols = [c for c in data.keys() if c != "id"]
        if not cols:
            continue

        placeholders = ", ".join(f":{c}" for c in cols)
        col_names = ", ".join(cols)

        try:
            result = pg_session.execute(
                text(f"INSERT INTO {tabela} ({col_names}) VALUES ({placeholders}) RETURNING id"),
                data,
            )
            new_id = result.scalar()
            if old_id is not None and new_id is not None:
                id_map[tabela][old_id] = new_id
            count += 1
        except Exception as e:
            erros.append(f"{tabela} (old_id={old_id}): {str(e)[:200]}")

    return count


# Mapeamento de FKs para remapeamento durante migração
_FK_MAP: dict[str, list[tuple[str, str]]] = {
    "bancos": [],
    "categorias": [],
    "receitas": [("categoria_id", "categorias"), ("banco_id", "bancos")],
    "despesas_parceladas": [("categoria_id", "categorias"), ("banco_id", "bancos")],
    "despesas_recorrentes": [("categoria_id", "categorias"), ("banco_id", "bancos")],
    "despesas": [
        ("categoria_id", "categorias"), ("banco_id", "bancos"),
        ("despesa_parcelada_id", "despesas_parceladas"),
        ("despesa_recorrente_id", "despesas_recorrentes"),
        ("cartao_id", "cartoes"),
    ],
    "cartoes": [],
    "compras_cartao": [("cartao_id", "cartoes"), ("categoria_id", "categorias")],
    "pagamentos_fatura": [("cartao_id", "cartoes"), ("banco_id", "bancos"), ("despesa_id", "despesas")],
    "investimentos": [("categoria_id", "categorias"), ("banco_id", "bancos")],
    "dividendos": [("investimento_id", "investimentos")],
    "transferencias": [("banco_origem_id", "bancos"), ("banco_destino_id", "bancos")],
    "veiculos": [],
    "abastecimentos": [("veiculo_id", "veiculos")],
    "manutencoes": [("veiculo_id", "veiculos")],
    "orcamentos": [],
    "itens_orcamento": [("orcamento_id", "orcamentos"), ("categoria_id", "categorias")],
    "historico_orcamento": [("item_orcamento_id", "itens_orcamento")],
    "configuracoes": [],
}


def _remapear_fks_migracao(
    registro: dict, tabela: str, id_map: dict[str, dict[int, int]],
) -> None:
    """Remapeia foreign keys usando o mapa de IDs antigo→novo."""
    # usuario_id é preservado (mesma tabela usuarios migrada primeiro)
    if "usuario_id" in registro and "usuarios" in id_map:
        old_uid = registro["usuario_id"]
        if isinstance(old_uid, int) and old_uid in id_map["usuarios"]:
            registro["usuario_id"] = id_map["usuarios"][old_uid]

    for fk_col, ref_tabela in _FK_MAP.get(tabela, []):
        if fk_col in registro and registro[fk_col] is not None:
            old_fk = registro[fk_col]
            if isinstance(old_fk, int) and ref_tabela in id_map and old_fk in id_map[ref_tabela]:
                registro[fk_col] = id_map[ref_tabela][old_fk]


def main() -> None:
    args = parse_args()

    logger.info("Conectando ao SQLite: %s", args.sqlite_path)
    sqlite_conn = sqlite3.connect(args.sqlite_path)

    logger.info("Conectando ao PostgreSQL...")
    engine = create_engine(args.supabase_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)

    relatorio: dict[str, dict] = {}
    total_migrado = 0
    total_erros = 0
    id_map: dict[str, dict[int, int]] = {}

    for tabela in TABELAS_ORDEM:
        session = Session()
        try:
            count, erros = migrar_tabela(sqlite_conn, session, tabela, id_map)
            session.commit()
            relatorio[tabela] = {"migrados": count, "erros": len(erros), "detalhes": erros}
            total_migrado += count
            total_erros += len(erros)
        except Exception as e:
            session.rollback()
            logger.error("Rollback tabela '%s': %s", tabela, e)
            relatorio[tabela] = {"migrados": 0, "erros": 1, "detalhes": [str(e)[:500]]}
            total_erros += 1
        finally:
            session.close()

    sqlite_conn.close()

    # Relatório final
    logger.info("=" * 60)
    logger.info("RELATÓRIO DE MIGRAÇÃO")
    logger.info("=" * 60)
    for tabela, info in relatorio.items():
        status = "OK" if info["erros"] == 0 else f"ERROS: {info['erros']}"
        logger.info("  %-25s %5d registros  [%s]", tabela, info["migrados"], status)
        for detalhe in info["detalhes"][:3]:
            logger.warning("    → %s", detalhe)
    logger.info("-" * 60)
    logger.info("Total migrado: %d registros | Erros: %d", total_migrado, total_erros)
    logger.info("=" * 60)

    if total_erros > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
