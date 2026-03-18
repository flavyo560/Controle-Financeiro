"""
Módulo de operações relacionadas a gestão de frota.
"""
import sqlite3
from database.connection import DatabaseManager
from database.migrations import get_db_manager
from utils.logger import logger


def listar_veiculos_ativos():
    """Lista todos os veículos ativos."""
    db = get_db_manager()
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nome_identificador FROM veiculos WHERE status = 1 ORDER BY nome_identificador ASC")
        veiculos = cur.fetchall()
    return veiculos
