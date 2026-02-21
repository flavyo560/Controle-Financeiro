import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
import os

# ==============================
# 📂 CONFIGURAÇÃO DE CAMINHO
# ==============================
APP_DIR = Path(os.getenv("LOCALAPPDATA")) / "ControleFinanceiro"
APP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / "financas.db"

def conectar():
    return sqlite3.connect(DB_PATH)

def coluna_existe(cur, tabela, coluna):
    """Verifica se uma coluna já existe para evitar erros de duplicidade."""
    try:
        cur.execute(f"PRAGMA table_info({tabela})")
        return coluna in [info[1] for info in cur.fetchall()]
    except:
        return False

# ==============================
# 🏗️ CRIAÇÃO E MIGRAÇÃO SEGURA
# ==============================
def criar_tabelas():
    conn = conectar()
    cur = conn.cursor()

    # Criação das tabelas base
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, 
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL, 
            perfil TEXT DEFAULT 'admin', 
            criado_em TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            placa TEXT,
            modelo TEXT,
            status INTEGER DEFAULT 1
        )
    """)

    cur.execute("CREATE TABLE IF NOT EXISTS bancos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL, saldo_inicial REAL DEFAULT 0, criado_em TEXT, status INTEGER DEFAULT 1)")
    cur.execute("CREATE TABLE IF NOT EXISTS receitas (id INTEGER PRIMARY KEY AUTOINCREMENT, valor REAL NOT NULL, data TEXT NOT NULL, banco_id INTEGER, FOREIGN KEY (banco_id) REFERENCES bancos (id))")
    cur.execute("CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT, valor REAL NOT NULL, data TEXT NOT NULL, banco_id INTEGER, FOREIGN KEY (banco_id) REFERENCES bancos (id))")

    # Migrações: Adiciona colunas novas sem apagar as tabelas
    migracoes = [
        ("usuarios", "cpf", "TEXT"),
        ("usuarios", "telefone", "TEXT"),
        ("usuarios", "senha_hash", "TEXT NOT NULL DEFAULT 'e10adc3949ba59abbe56e057f20f883e'"),
        ("veiculos", "modelo", "TEXT"),
        ("bancos", "criado_em", "TEXT")
    ]
    
    for tabela, coluna, definicao in migracoes:
        if not coluna_existe(cur, tabela, coluna):
            try:
                cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
            except: pass

    conn.commit()
    conn.close()

# ==============================
# ⚠️ FUNÇÃO DE RESET (EXIGIDA PELA MAIN_WINDOW)
# ==============================
def resetar_banco():
    """Apaga as tabelas e recria, usada pelo menu Ferramentas."""
    conn = conectar()
    cur = conn.cursor()
    tabelas = ["despesas", "receitas", "usuarios", "bancos", "veiculos", "categorias"]
    for t in tabelas:
        try:
            cur.execute(f"DROP TABLE IF EXISTS {t}")
        except: pass
    conn.commit()
    conn.close()
    criar_tabelas()

# ==============================
# 🚗 FUNÇÕES DE SUPORTE
# ==============================

def listar_veiculos_ativos():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM veiculos WHERE status = 1 ORDER BY nome ASC")
    veiculos = cur.fetchall()
    conn.close()
    return veiculos

def calcular_saldo_banco(banco_id=None):
    conn = conectar()
    cur = conn.cursor()
    filtro = "WHERE banco_id = ?" if banco_id else ""
    params = (banco_id,) if banco_id else ()

    cur.execute(f"SELECT SUM(saldo_inicial) FROM bancos {filtro.replace('banco_id', 'id')}", params)
    inicial = cur.fetchone()[0] or 0
    cur.execute(f"SELECT SUM(valor) FROM receitas {filtro}", params)
    receitas = cur.fetchone()[0] or 0
    cur.execute(f"SELECT SUM(valor) FROM despesas {filtro}", params)
    despesas = cur.fetchone()[0] or 0
    conn.close()
    return inicial + receitas - despesas

# ==============================
# 🔑 SEGURANÇA E ACESSO
# ==============================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def existe_usuario():
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM usuarios")
        return cur.fetchone()[0] > 0
    except: return False
    finally: conn.close()

def criar_usuario(nome, email, senha, perfil="admin"):
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil, criado_em)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, email, hash_senha(senha), perfil, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    finally: conn.close()

def validar_login(identificador, senha):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nome, email, cpf, telefone FROM usuarios
        WHERE (email = ? OR nome = ? OR cpf = ?) AND senha_hash = ?
    """, (identificador, identificador, identificador, hash_senha(senha)))
    usuario = cur.fetchone()
    conn.close()
    return usuario