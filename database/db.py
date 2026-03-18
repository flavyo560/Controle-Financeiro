import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import time
import logging
from utils.logger import logger, log_errors

# ==============================
# 📂 IMPORTAR MÓDULO CENTRALIZADO
# ==============================
# CORREÇÃO: Bug de Perda de Dados em Banco de Produção
# Usar módulo centralizado db_config.py como única fonte de verdade
from database.db_config import (
    get_persistent_db_path,
    get_db_manager_instance,
    conectar as conectar_centralizado
)

# ==============================
# 🔧 FUNÇÕES DE COMPATIBILIDADE
# ==============================
def get_db_path():
    """
    Retorna o caminho do banco de dados.
    
    REFATORADO: Agora usa o módulo centralizado db_config.py
    """
    return get_persistent_db_path()

def get_db_manager():
    """
    Retorna a instância global do DatabaseManager.
    Thread-safe e gerencia conexões automaticamente.
    
    REFATORADO: Agora usa o módulo centralizado db_config.py
    """
    return get_db_manager_instance()

def conectar():
    """
    DEPRECATED: Returns a raw connection for backward compatibility.
    
    REFATORADO: Agora usa o módulo centralizado db_config.py
    
    For new code, use get_db_manager().get_connection() instead.
    
    WARNING: Caller is responsible for closing the connection!
    """
    return conectar_centralizado()

def coluna_existe(cur, tabela, coluna):
    """Verifica se uma coluna já existe para evitar erros de duplicidade."""
    from database.validators import validate_table_name
    
    try:
        # Validar nome da tabela
        tabela = validate_table_name(tabela)
        cur.execute(f"PRAGMA table_info({tabela})")
        return coluna in [info[1] for info in cur.fetchall()]
    except ValueError as e:
        logger.error(f"Nome de tabela inválido: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar coluna: {e}")
        return False

# ==============================
# 🏗️ CRIAÇÃO E MIGRAÇÃO SEGURA
# ==============================
def criar_tabelas():
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()

        try:
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.OperationalError as e:
            logger.error(f"Erro ao configurar PRAGMA journal_mode/synchronous: {e}")
        except sqlite3.DatabaseError as e:
            logger.error(f"Erro de banco de dados ao configurar PRAGMAs: {e}")

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
                nome_identificador TEXT NOT NULL,
                placa TEXT,
                modelo TEXT,
                status INTEGER DEFAULT 1
            )
        """)

        cur.execute("CREATE TABLE IF NOT EXISTS bancos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL, saldo_inicial REAL DEFAULT 0, criado_em TEXT, status INTEGER DEFAULT 1)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL,
                criado_em TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                valor REAL NOT NULL,
                data TEXT NOT NULL,
                categoria_id INTEGER,
                banco_id INTEGER,
                FOREIGN KEY (banco_id) REFERENCES bancos (id),
                FOREIGN KEY (categoria_id) REFERENCES categorias (id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                valor REAL NOT NULL,
                data TEXT NOT NULL,
                categoria_id INTEGER,
                banco_id INTEGER,
                FOREIGN KEY (banco_id) REFERENCES bancos (id),
                FOREIGN KEY (categoria_id) REFERENCES categorias (id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS investimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT,
                valor_investido REAL NOT NULL,
                valor_atual REAL,
                data TEXT NOT NULL,
                criado_em TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dividendos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investimento_id INTEGER,
                valor REAL NOT NULL,
                data TEXT NOT NULL,
                FOREIGN KEY (investimento_id) REFERENCES investimentos (id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transferencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                banco_origem_id INTEGER,
                banco_destino_id INTEGER,
                valor REAL NOT NULL,
                data TEXT NOT NULL,
                descricao TEXT,
                FOREIGN KEY (banco_origem_id) REFERENCES bancos (id),
                FOREIGN KEY (banco_destino_id) REFERENCES bancos (id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS abastecimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                veiculo_id INTEGER,
                data TEXT NOT NULL,
                litros REAL,
                valor_total REAL NOT NULL,
                km_atual REAL,
                posto TEXT,
                FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS manutencoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                veiculo_id INTEGER,
                data TEXT NOT NULL,
                descricao TEXT,
                valor REAL NOT NULL,
                km_atual REAL,
                FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave TEXT UNIQUE NOT NULL,
                valor TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS despesas_parceladas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor_total REAL NOT NULL,
                numero_parcelas INTEGER NOT NULL,
                data_primeira_parcela TEXT NOT NULL,
                categoria_id INTEGER,
                banco_id INTEGER,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                FOREIGN KEY (banco_id) REFERENCES bancos (id),
                CHECK (numero_parcelas > 1 AND numero_parcelas <= 120)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS despesas_recorrentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                dia_mes INTEGER NOT NULL,
                categoria_id INTEGER,
                banco_id INTEGER,
                data_inicio TEXT NOT NULL,
                data_fim TEXT,
                ativa INTEGER DEFAULT 1,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                FOREIGN KEY (banco_id) REFERENCES bancos (id),
                CHECK (dia_mes >= 1 AND dia_mes <= 31),
                CHECK (ativa IN (0, 1))
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cartoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                bandeira TEXT,
                limite_total REAL NOT NULL,
                dia_fechamento INTEGER NOT NULL,
                dia_vencimento INTEGER NOT NULL,
                status INTEGER DEFAULT 1,
                criado_em TEXT NOT NULL,
                CHECK (limite_total > 0),
                CHECK (dia_fechamento >= 1 AND dia_fechamento <= 31),
                CHECK (dia_vencimento >= 1 AND dia_vencimento <= 31),
                CHECK (status IN (0, 1))
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compras_cartao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cartao_id INTEGER NOT NULL,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                data_compra TEXT NOT NULL,
                categoria_id INTEGER,
                mes_fatura TEXT NOT NULL,
                parcela_numero INTEGER,
                parcela_total INTEGER,
                compra_parcelada_id INTEGER,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (cartao_id) REFERENCES cartoes (id),
                FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                CHECK (valor > 0),
                CHECK (parcela_numero IS NULL OR parcela_numero > 0),
                CHECK (parcela_total IS NULL OR parcela_total >= 2)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pagamentos_fatura (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cartao_id INTEGER NOT NULL,
                mes_fatura TEXT NOT NULL,
                valor_pago REAL NOT NULL,
                data_pagamento TEXT NOT NULL,
                banco_id INTEGER NOT NULL,
                despesa_id INTEGER,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (cartao_id) REFERENCES cartoes (id),
                FOREIGN KEY (banco_id) REFERENCES bancos (id),
                FOREIGN KEY (despesa_id) REFERENCES despesas (id),
                CHECK (valor_pago > 0)
            )
        """)

        # Migrações: Adiciona colunas novas sem apagar as tabelas
        migracoes = [
            ("usuarios", "cpf", "TEXT"),
            ("usuarios", "telefone", "TEXT"),
            ("usuarios", "senha_hash", "TEXT NOT NULL DEFAULT 'e10adc3949ba59abbe56e057f20f883e'"),
            ("usuarios", "senha_hash_bcrypt", "TEXT"),
            ("veiculos", "modelo", "TEXT"),
            ("bancos", "criado_em", "TEXT"),
            ("receitas", "descricao", "TEXT"),
            ("receitas", "categoria_id", "INTEGER"),
            ("despesas", "descricao", "TEXT"),
            ("despesas", "categoria_id", "INTEGER"),
            ("despesas", "parcela_numero", "INTEGER"),
            ("despesas", "parcela_total", "INTEGER"),
            ("despesas", "despesa_parcelada_id", "INTEGER REFERENCES despesas_parceladas(id)"),
            ("despesas", "despesa_recorrente_id", "INTEGER REFERENCES despesas_recorrentes(id)"),
            ("investimentos", "ativo", "INTEGER DEFAULT 1"),
            ("investimentos", "valor", "REAL"),
            ("investimentos", "categoria_id", "INTEGER"),
            ("investimentos", "banco_id", "INTEGER"),
            ("categorias", "ativo", "INTEGER DEFAULT 1"),
            ("abastecimentos", "km", "REAL"),
            ("abastecimentos", "litros_gasolina", "REAL"),
            ("abastecimentos", "litros_etanol", "REAL"),
            ("abastecimentos", "tipo", "TEXT"),
            ("abastecimentos", "valor", "REAL"),
            ("manutencoes", "servico", "TEXT"),
            ("manutencoes", "km", "REAL"),
            ("receitas", "ativo", "INTEGER DEFAULT 1"),
            ("despesas", "ativo", "INTEGER DEFAULT 1"),
            ("bancos", "ativo", "INTEGER DEFAULT 1"),
        ]

        for tabela, coluna, definicao in migracoes:
            if not coluna_existe(cur, tabela, coluna):
                try:
                    from database.validators import validate_table_name, validate_column_name
                    # Validar nomes
                    tabela_validada = validate_table_name(tabela)
                    coluna_validada = validate_column_name(coluna)
                    cur.execute(f"ALTER TABLE {tabela_validada} ADD COLUMN {coluna_validada} {definicao}")
                except ValueError as e:
                    logger.error(f"Erro de validação na migração: {e}")
                except Exception as e:
                    logger.error(f"Erro ao adicionar coluna: {e}")

        # Copiar dados de colunas antigas para novas (se existirem)
        # abastecimentos: km_atual -> km
        if coluna_existe(cur, "abastecimentos", "km_atual") and coluna_existe(cur, "abastecimentos", "km"):
            try:
                cur.execute("UPDATE abastecimentos SET km = km_atual WHERE km IS NULL AND km_atual IS NOT NULL")
            except sqlite3.IntegrityError as e:
                logger.error(f"Erro de integridade ao migrar km_atual -> km: {e}")
            except sqlite3.OperationalError as e:
                logger.error(f"Erro operacional ao migrar km_atual -> km: {e}")

        # abastecimentos: valor_total -> valor
        if coluna_existe(cur, "abastecimentos", "valor_total") and coluna_existe(cur, "abastecimentos", "valor"):
            try:
                cur.execute("UPDATE abastecimentos SET valor = valor_total WHERE valor IS NULL AND valor_total IS NOT NULL")
            except sqlite3.IntegrityError as e:
                logger.error(f"Erro de integridade ao migrar valor_total -> valor: {e}")
            except sqlite3.OperationalError as e:
                logger.error(f"Erro operacional ao migrar valor_total -> valor: {e}")

        # manutencoes: descricao -> servico
        if coluna_existe(cur, "manutencoes", "descricao") and coluna_existe(cur, "manutencoes", "servico"):
            try:
                cur.execute("UPDATE manutencoes SET servico = descricao WHERE servico IS NULL AND descricao IS NOT NULL")
            except sqlite3.IntegrityError as e:
                logger.error(f"Erro de integridade ao migrar descricao -> servico: {e}")
            except sqlite3.OperationalError as e:
                logger.error(f"Erro operacional ao migrar descricao -> servico: {e}")

        # manutencoes: km_atual -> km
        if coluna_existe(cur, "manutencoes", "km_atual") and coluna_existe(cur, "manutencoes", "km"):
            try:
                cur.execute("UPDATE manutencoes SET km = km_atual WHERE km IS NULL AND km_atual IS NOT NULL")
            except sqlite3.IntegrityError as e:
                logger.error(f"Erro de integridade ao migrar km_atual -> km em manutencoes: {e}")
            except sqlite3.OperationalError as e:
                logger.error(f"Erro operacional ao migrar km_atual -> km em manutencoes: {e}")

        # investimentos: valor_investido -> valor
        if coluna_existe(cur, "investimentos", "valor_investido") and coluna_existe(cur, "investimentos", "valor"):
            try:
                cur.execute("UPDATE investimentos SET valor = valor_investido WHERE valor IS NULL AND valor_investido IS NOT NULL")
            except sqlite3.IntegrityError as e:
                logger.error(f"Erro de integridade ao migrar valor_investido -> valor: {e}")
            except sqlite3.OperationalError as e:
                logger.error(f"Erro operacional ao migrar valor_investido -> valor: {e}")

        # Migração: renomear coluna 'nome' para 'nome_identificador' em veiculos (bancos de dados antigos)
        cur.execute("PRAGMA table_info(veiculos)")
        colunas_veiculos = [info[1] for info in cur.fetchall()]
        if "nome" in colunas_veiculos and "nome_identificador" not in colunas_veiculos:
            try:
                cur.execute("ALTER TABLE veiculos RENAME COLUMN nome TO nome_identificador")
            except sqlite3.OperationalError as e:
                logger.error(f"Erro ao renomear coluna nome -> nome_identificador: {e}")
            except sqlite3.DatabaseError as e:
                logger.error(f"Erro de banco de dados ao renomear coluna: {e}")

        # Criação de índices para otimizar consultas de cartões de crédito
        indices = [
            ("idx_compras_cartao_cartao_id", "compras_cartao", "cartao_id"),
            ("idx_compras_cartao_mes_fatura", "compras_cartao", "mes_fatura"),
            ("idx_compras_cartao_parcelada", "compras_cartao", "compra_parcelada_id"),
            ("idx_pagamentos_fatura_cartao_id", "pagamentos_fatura", "cartao_id"),
            ("idx_pagamentos_fatura_mes", "pagamentos_fatura", "mes_fatura"),
        ]

        for nome_indice, tabela, coluna in indices:
            try:
                cur.execute(f"CREATE INDEX IF NOT EXISTS {nome_indice} ON {tabela}({coluna})")
            except sqlite3.OperationalError as e:
                logger.error(f"Erro ao criar índice {nome_indice}: {e}")
            except sqlite3.DatabaseError as e:
                logger.error(f"Erro de banco de dados ao criar índice {nome_indice}: {e}")

        # Connection will be automatically committed and closed by context manager


def executar_escrita(sql, params=()):
    """
    Executa operação de escrita com retry automático.
    
    DEPRECATED: Use get_db_manager().get_connection() diretamente.
    DatabaseManager já implementa retry logic com backoff exponencial.
    """
    db = get_db_manager()
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            # Commit automático pelo context manager
        return True
    except sqlite3.OperationalError as e:
        logger.error(f"Erro operacional ao executar escrita: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao executar escrita: {e}")
        raise

# ==============================
# ⚠️ FUNÇÃO DE RESET (EXIGIDA PELA MAIN_WINDOW)
# ==============================
def resetar_banco():
    """Apaga as tabelas e recria, usada pelo menu Ferramentas."""
    # Check test mode dynamically
    test_mode = os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("TEST_MODE") == "1"
    if not test_mode:
        raise RuntimeError("❌ BLOQUEADO: resetar_banco() só funciona em testes!")
    
    from database.validators import validate_table_name
    
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        tabelas = [
            "dividendos", "abastecimentos", "manutencoes", "transferencias",
            "investimentos", "despesas", "receitas", "categorias",
            "veiculos", "bancos", "configuracoes", "usuarios",
            "pagamentos_fatura", "compras_cartao", "cartoes",
            "despesas_parceladas", "despesas_recorrentes"
        ]
        for t in tabelas:
            try:
                # Validar nome da tabela
                t_validado = validate_table_name(t)
                cur.execute(f"DROP TABLE IF EXISTS {t_validado}")
            except ValueError as e:
                logger.error(f"Nome de tabela inválido: {e}")
            except Exception as e:
                logger.error(f"Erro ao dropar tabela: {e}")
        # Commit automático pelo context manager
    criar_tabelas()

# ==============================
# 🚗 FUNÇÕES DE SUPORTE
# ==============================

def listar_veiculos_ativos():
    db = get_db_manager()
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nome_identificador FROM veiculos WHERE status = 1 ORDER BY nome_identificador ASC")
        veiculos = cur.fetchall()
    return veiculos

@log_errors()
def calcular_saldo_banco(banco_id=None):
    conn = conectar()
    cur = conn.cursor()
    filtro = "WHERE banco_id = ?" if banco_id else ""
    params = (banco_id,) if banco_id else ()

    cur.execute(f"SELECT SUM(saldo_inicial) FROM bancos {filtro.replace('banco_id', 'id')}", params)
    inicial = cur.fetchone()[0] or 0
    cur.execute(f"SELECT SUM(valor) FROM receitas {filtro}", params)
    receitas = cur.fetchone()[0] or 0
    # CORREÇÃO: Considerar apenas despesas pagas (pago = 1)
    cur.execute(f"SELECT SUM(valor) FROM despesas {filtro} {'AND' if filtro else 'WHERE'} pago = 1", params)
    despesas = cur.fetchone()[0] or 0
    conn.close()
    return inicial + receitas - despesas

# ==============================
# 🔑 SEGURANÇA E ACESSO
# ==============================

import bcrypt

def hash_senha(senha):
    """DEPRECATED: Use hash_senha_bcrypt() para novas senhas."""
    return hashlib.sha256(senha.encode()).hexdigest()

def hash_senha_bcrypt(senha: str) -> str:
    """
    Hash seguro de senha usando bcrypt com salt automático.
    
    Args:
        senha: Senha em texto claro
        
    Returns:
        Hash bcrypt da senha (string)
        
    Raises:
        ValueError: Se senha vazia
    """
    if not senha:
        raise ValueError("Senha não pode ser vazia")
    
    # Gerar salt e hash (12 rounds = bom equilíbrio segurança/performance)
    salt = bcrypt.gensalt(rounds=12)
    hash_bytes = bcrypt.hashpw(senha.encode('utf-8'), salt)
    return hash_bytes.decode('utf-8')

def verificar_senha_bcrypt(senha: str, hash_armazenado: str) -> bool:
    """
    Verifica senha contra hash bcrypt.
    
    Args:
        senha: Senha em texto claro
        hash_armazenado: Hash bcrypt armazenado
        
    Returns:
        True se senha correta, False caso contrário
    """
    try:
        return bcrypt.checkpw(
            senha.encode('utf-8'),
            hash_armazenado.encode('utf-8')
        )
    except Exception:
        return False

def existe_usuario():
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM usuarios")
        return cur.fetchone()[0] > 0
    except sqlite3.OperationalError as e:
        logger.error(f"Erro operacional ao verificar existência de usuário: {e}")
        return False
    except sqlite3.DatabaseError as e:
        logger.error(f"Erro de banco de dados ao verificar existência de usuário: {e}")
        return False
    finally: 
        conn.close()

@log_errors()
def criar_usuario(nome, email, senha, perfil="admin"):
    conn = conectar()
    cur = conn.cursor()
    try:
        # Inserir com bcrypt (novo sistema) e um valor dummy para senha_hash (compatibilidade)
        cur.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, senha_hash_bcrypt, perfil, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, email, '', hash_senha_bcrypt(senha), perfil, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    finally: conn.close()

def validar_login(identificador, senha):
    """
    Valida login do usuário com suporte a migração automática de SHA-256 para bcrypt.
    
    Args:
        identificador: Email, nome ou CPF do usuário
        senha: Senha em texto claro
        
    Returns:
        Tupla (id, nome, email, cpf, telefone) se login válido, None caso contrário
    """
    conn = conectar()
    cur = conn.cursor()
    
    # Buscar usuário
    cur.execute("""
        SELECT id, nome, email, cpf, telefone, senha_hash_bcrypt, senha_hash
        FROM usuarios
        WHERE email = ? OR nome = ? OR cpf = ?
    """, (identificador, identificador, identificador))
    
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return None
    
    user_id, nome, email, cpf, telefone, senha_bcrypt, senha_sha256 = row
    
    # Tentar bcrypt primeiro (novo sistema)
    if senha_bcrypt:
        if verificar_senha_bcrypt(senha, senha_bcrypt):
            return (user_id, nome, email, cpf, telefone)
        return None
    
    # Fallback para SHA-256 (sistema antigo) e migrar
    if senha_sha256 and senha_sha256 == hash_senha(senha):
        # Migrar para bcrypt
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                UPDATE usuarios 
                SET senha_hash_bcrypt = ?, senha_hash = ''
                WHERE id = ?
            """, (hash_senha_bcrypt(senha), user_id))
            conn.commit()
            conn.close()
            logger.info(f"Senha do usuário {user_id} migrada para bcrypt")
        except Exception as e:
            logger.error(f"Erro ao migrar senha: {e}")
        
        return (user_id, nome, email, cpf, telefone)
    
    return None

# ==============================
# 💳 DESPESAS PARCELADAS
# ==============================

@log_errors()
def criar_despesa_parcelada(descricao, valor_total, numero_parcelas,
                           data_primeira_parcela, categoria_id, banco_id):
    """
    Cria uma despesa parcelada e gera automaticamente as parcelas.

    Args:
        descricao: Descrição da despesa
        valor_total: Valor total da despesa
        numero_parcelas: Número de parcelas
        data_primeira_parcela: Data da primeira parcela (formato YYYY-MM-DD)
        categoria_id: ID da categoria
        banco_id: ID do banco

    Returns:
        ID da despesa parcelada criada
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        # Inserir registro da despesa parcelada
        cur.execute("""
            INSERT INTO despesas_parceladas
            (descricao, valor_total, numero_parcelas, data_primeira_parcela,
             categoria_id, banco_id, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (descricao, valor_total, numero_parcelas, data_primeira_parcela,
              categoria_id, banco_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        despesa_parcelada_id = cur.lastrowid

        # Gerar as parcelas
        gerar_parcelas(cur, despesa_parcelada_id, descricao, valor_total,
                      numero_parcelas, data_primeira_parcela, categoria_id, banco_id)

        conn.commit()
        return despesa_parcelada_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def gerar_parcelas(despesa_parcelada_id):
    """
    Gera os lançamentos individuais de uma despesa parcelada.
    Chamada internamente por criar_despesa_parcelada().
    
    Calcula valor_parcela = valor_total / numero_parcelas
    Incrementa data em 1 mês para cada parcela
    Cria registros em 'despesas' com referência à despesa_parcelada_id
    Define data_vencimento igual à data da parcela
    Define data_pagamento = NULL e pago = 0
    
    Requirements: 10.1, 10.2
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar dados da despesa parcelada
        cur.execute("""
            SELECT descricao, valor_total, numero_parcelas, data_primeira_parcela,
                   categoria_id, banco_id
            FROM despesas_parceladas
            WHERE id = ?
        """, (despesa_parcelada_id,))
        
        resultado = cur.fetchone()
        if not resultado:
            raise ValueError(f"Despesa parcelada com id {despesa_parcelada_id} não encontrada")
        
        descricao, valor_total, numero_parcelas, data_primeira_parcela, categoria_id, banco_id = resultado
        
        # Calcular valor de cada parcela
        valor_parcela = valor_total / numero_parcelas
        
        # Converter data_primeira_parcela para objeto date
        if isinstance(data_primeira_parcela, str):
            data_base = datetime.strptime(data_primeira_parcela, '%Y-%m-%d').date()
        else:
            # Já é um objeto date ou datetime
            data_base = data_primeira_parcela if isinstance(data_primeira_parcela, date) else data_primeira_parcela.date()
        
        # Criar cada parcela
        for i in range(numero_parcelas):
            # Calcular data da parcela (incremento mensal)
            data_parcela = data_base + relativedelta(months=i)
            data_parcela_str = data_parcela.strftime('%Y-%m-%d')
            
            # Inserir na tabela despesas com data_vencimento
            cur.execute("""
                INSERT INTO despesas 
                (descricao, valor, data, categoria_id, banco_id, 
                 parcela_numero, parcela_total, despesa_parcelada_id,
                 data_vencimento, data_pagamento, pago)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0)
            """, (
                descricao,
                valor_parcela,
                data_parcela_str,
                categoria_id,
                banco_id,
                i + 1,  # parcela_numero (1-indexed)
                numero_parcelas,
                despesa_parcelada_id,
                data_parcela_str  # data_vencimento = data da parcela
            ))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def listar_despesas_parceladas(filtros=None):
    """
    Lista todas as despesas parceladas com informações agregadas.
    
    Args:
        filtros: Dicionário opcional com filtros (não implementado ainda)
    
    Returns:
        Lista de dicts com: id, descricao, valor_total, numero_parcelas,
        parcelas_pagas, parcelas_pendentes, categoria_nome, banco_nome,
        data_primeira_parcela, valor_parcela
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        hoje = datetime.now().date().strftime('%Y-%m-%d')
        
        # Query com JOINs e subqueries para calcular parcelas pagas/pendentes
        cur.execute("""
            SELECT 
                dp.id,
                dp.descricao,
                dp.valor_total,
                dp.numero_parcelas,
                dp.data_primeira_parcela,
                dp.criado_em,
                c.nome AS categoria_nome,
                b.nome AS banco_nome,
                ROUND(dp.valor_total / dp.numero_parcelas, 2) AS valor_parcela,
                (
                    SELECT COUNT(*)
                    FROM despesas d
                    WHERE d.despesa_parcelada_id = dp.id
                    AND d.data <= ?
                ) AS parcelas_pagas,
                (
                    SELECT COUNT(*)
                    FROM despesas d
                    WHERE d.despesa_parcelada_id = dp.id
                    AND d.data > ?
                ) AS parcelas_pendentes
            FROM despesas_parceladas dp
            LEFT JOIN categorias c ON dp.categoria_id = c.id
            LEFT JOIN bancos b ON dp.banco_id = b.id
            ORDER BY dp.data_primeira_parcela DESC
        """, (hoje, hoje))
        
        colunas = [desc[0] for desc in cur.description]
        resultados = cur.fetchall()
        
        # Converter para lista de dicts
        despesas_parceladas = []
        for row in resultados:
            despesa = dict(zip(colunas, row))
            despesas_parceladas.append(despesa)
        
        return despesas_parceladas
        
    finally:
        conn.close()

@log_errors()
def editar_parcela(despesa_id, novos_dados, aplicar_futuras=False):
    """
    Edita uma parcela específica.
    
    Args:
        despesa_id: ID da parcela (registro em despesas)
        novos_dados: Dict com campos a atualizar (ex: {'valor': 100.0, 'data': '2024-02-01'})
        aplicar_futuras: Se True, aplica mudanças a todas parcelas futuras
        
    Raises:
        ValueError: Se a parcela não for encontrada ou não for uma parcela
    """
    from database.validators import validate_column_name
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar informações da parcela
        cur.execute("""
            SELECT id, parcela_numero, parcela_total, despesa_parcelada_id
            FROM despesas
            WHERE id = ?
        """, (despesa_id,))
        
        resultado = cur.fetchone()
        if not resultado:
            raise ValueError(f"Despesa com id {despesa_id} não encontrada")
        
        _, parcela_numero, parcela_total, despesa_parcelada_id = resultado
        
        if despesa_parcelada_id is None:
            raise ValueError(f"Despesa com id {despesa_id} não é uma parcela")
        
        # Construir query de UPDATE
        if not novos_dados:
            return  # Nada para atualizar
        
        # Validar nomes de colunas
        for coluna in novos_dados.keys():
            validate_column_name(coluna)
        
        campos = ', '.join([f"{k} = ?" for k in novos_dados.keys()])
        valores = list(novos_dados.values())
        
        if not aplicar_futuras:
            # Editar apenas esta parcela
            valores.append(despesa_id)
            cur.execute(f"""
                UPDATE despesas SET {campos}
                WHERE id = ?
            """, valores)
        else:
            # Editar esta e todas as parcelas futuras
            valores.extend([despesa_parcelada_id, parcela_numero])
            cur.execute(f"""
                UPDATE despesas SET {campos}
                WHERE despesa_parcelada_id = ?
                AND parcela_numero >= ?
            """, valores)
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


@log_errors()
def excluir_parcela(despesa_id):
    """
    Exclui uma parcela específica.
    Se for a última parcela, remove também o registro de despesa_parcelada.
    
    Args:
        despesa_id: ID da parcela (registro em despesas)
        
    Raises:
        ValueError: Se a parcela não for encontrada ou não for uma parcela
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar informações da parcela
        cur.execute("""
            SELECT id, despesa_parcelada_id
            FROM despesas
            WHERE id = ?
        """, (despesa_id,))
        
        resultado = cur.fetchone()
        if not resultado:
            raise ValueError(f"Despesa com id {despesa_id} não encontrada")
        
        _, despesa_parcelada_id = resultado
        
        if despesa_parcelada_id is None:
            raise ValueError(f"Despesa com id {despesa_id} não é uma parcela")
        
        # Excluir a parcela
        cur.execute("""
            DELETE FROM despesas
            WHERE id = ?
        """, (despesa_id,))
        
        # Verificar se restam outras parcelas da mesma despesa_parcelada_id
        cur.execute("""
            SELECT COUNT(*) FROM despesas
            WHERE despesa_parcelada_id = ?
        """, (despesa_parcelada_id,))
        
        count = cur.fetchone()[0]
        
        # Se não restam parcelas, excluir o registro de despesas_parceladas
        if count == 0:
            cur.execute("""
                DELETE FROM despesas_parceladas
                WHERE id = ?
            """, (despesa_parcelada_id,))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ==============================
# 🔁 DESPESAS RECORRENTES
# ==============================

@log_errors()
def criar_despesa_recorrente(descricao, valor, dia_mes, categoria_id,
                            banco_id, data_inicio, data_fim=None):
    """
    Cria uma despesa recorrente.

    Args:
        descricao: Descrição da despesa
        valor: Valor da despesa
        dia_mes: Dia do mês para lançamento (1-31)
        categoria_id: ID da categoria
        banco_id: ID do banco
        data_inicio: Data de início da recorrência
        data_fim: Data de fim da recorrência (opcional)

    Returns:
        ID da despesa recorrente criada
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO despesas_recorrentes
            (descricao, valor, dia_mes, categoria_id, banco_id,
             data_inicio, data_fim, ativa, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (descricao, valor, dia_mes, categoria_id, banco_id,
              data_inicio, data_fim, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        recorrente_id = cur.lastrowid
        conn.commit()
        return recorrente_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def verificar_lancamento_mes_atual(recorrente_id, mes, ano):
    """
    Verifica se já existe um lançamento de uma despesa recorrente no mês/ano especificado.
    
    Args:
        recorrente_id: ID da despesa recorrente
        mes: Mês a verificar (1-12)
        ano: Ano a verificar (ex: 2024)
        
    Returns:
        bool: True se existe lançamento no mês/ano, False caso contrário
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Query usando strftime para verificar mês e ano
        cur.execute("""
            SELECT COUNT(*) FROM despesas
            WHERE despesa_recorrente_id = ?
            AND strftime('%m', data) = ?
            AND strftime('%Y', data) = ?
        """, (recorrente_id, f'{mes:02d}', str(ano)))
        
        count = cur.fetchone()[0]
        return count > 0
        
    finally:
        conn.close()
def gerar_lancamentos_recorrentes():
    """
    Verifica todas as despesas recorrentes ativas e gera lançamentos
    para o mês atual se ainda não existirem.

    Deve ser chamada na inicialização do sistema.

    Lógica:
    - Para cada despesa_recorrente ativa
    - Verifica se data_inicio <= hoje <= data_fim (ou sem data_fim)
    - Verifica se já existe lançamento no mês atual
    - Se não existe, cria lançamento com data = dia_mes do mês atual
    - Se dia_mes > último dia do mês, usa último dia do mês

    Returns:
        int: Número de lançamentos criados
    """
    from datetime import date
    from calendar import monthrange
    from utils.logger import logger

    db = get_db_manager()
    hoje = date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year
    lancamentos_criados = 0

    try:
        with db.get_connection() as conn:
            cur = conn.cursor()

            # 1. Buscar todas despesas recorrentes ativas
            cur.execute("""
                SELECT id, descricao, valor, dia_mes, categoria_id, banco_id,
                       data_inicio, data_fim
                FROM despesas_recorrentes
                WHERE ativa = 1
            """)

            recorrentes = cur.fetchall()

            for recorrente in recorrentes:
                recorrente_id, descricao, valor, dia_mes, categoria_id, banco_id, data_inicio_str, data_fim_str = recorrente

                # 2. Verificar se está no período ativo
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()

                # Se ainda não começou, pular
                if data_inicio > hoje:
                    continue

                # Se tem data_fim e já terminou, pular
                if data_fim_str:
                    data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
                    if data_fim < hoje:
                        continue

                # 3. Verificar se já existe lançamento no mês atual
                ja_existe = verificar_lancamento_mes_atual(recorrente_id, mes_atual, ano_atual)
                if ja_existe:
                    logger.debug(f"Lançamento recorrente já existe para recorrente_id={recorrente_id}, mês={mes_atual}/{ano_atual}")
                    continue

                # 4. Calcular dia do lançamento
                # Obter o último dia do mês atual
                ultimo_dia_mes = monthrange(ano_atual, mes_atual)[1]
                # Usar o menor valor entre dia_mes configurado e último dia do mês
                dia_lancamento = min(dia_mes, ultimo_dia_mes)
                data_lancamento = date(ano_atual, mes_atual, dia_lancamento)
                data_lancamento_str = data_lancamento.strftime('%Y-%m-%d')

                # 5. Inserir em despesas com despesa_recorrente_id, pago=0, data_vencimento e data_pagamento=NULL
                # Requirements: 10.3, 10.4
                cur.execute("""
                    INSERT INTO despesas
                    (descricao, valor, data, categoria_id, banco_id, despesa_recorrente_id, 
                     pago, data_vencimento, data_pagamento)
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?, NULL)
                """, (
                    descricao,
                    valor,
                    data_lancamento_str,
                    categoria_id,
                    banco_id,
                    recorrente_id,
                    data_lancamento_str  # data_vencimento = data do lançamento
                ))

                lancamentos_criados += 1
                logger.debug(f"Lançamento recorrente criado para recorrente_id={recorrente_id}")

            # Commit automático pelo context manager
        
        if lancamentos_criados > 0:
            logger.info(f"Gerados {lancamentos_criados} lançamentos recorrentes")
        
        return lancamentos_criados
        
    except Exception as e:
        logger.error(f"Erro ao gerar lançamentos recorrentes: {e}", exc_info=True)
        return 0

def listar_despesas_recorrentes(incluir_inativas=False):
    """
    Lista todas as despesas recorrentes.

    Args:
        incluir_inativas: Se True, inclui despesas desativadas

    Returns:
        Lista de dicts com todos os campos da despesa recorrente
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        # Query com JOINs para incluir nomes de categoria e banco
        # Usar query parametrizada ao invés de f-string
        if incluir_inativas:
            cur.execute("""
                SELECT
                    dr.id,
                    dr.descricao,
                    dr.valor,
                    dr.dia_mes,
                    dr.categoria_id,
                    dr.banco_id,
                    dr.data_inicio,
                    dr.data_fim,
                    dr.ativa,
                    dr.criado_em,
                    c.nome AS categoria_nome,
                    b.nome AS banco_nome
                FROM despesas_recorrentes dr
                LEFT JOIN categorias c ON dr.categoria_id = c.id
                LEFT JOIN bancos b ON dr.banco_id = b.id
                ORDER BY dr.descricao ASC
            """)
        else:
            cur.execute("""
                SELECT
                    dr.id,
                    dr.descricao,
                    dr.valor,
                    dr.dia_mes,
                    dr.categoria_id,
                    dr.banco_id,
                    dr.data_inicio,
                    dr.data_fim,
                    dr.ativa,
                    dr.criado_em,
                    c.nome AS categoria_nome,
                    b.nome AS banco_nome
                FROM despesas_recorrentes dr
                LEFT JOIN categorias c ON dr.categoria_id = c.id
                LEFT JOIN bancos b ON dr.banco_id = b.id
                WHERE dr.ativa = 1
                ORDER BY dr.descricao ASC
            """)

        colunas = [desc[0] for desc in cur.description]
        resultados = cur.fetchall()

        # Converter para lista de dicts
        despesas_recorrentes = []
        for row in resultados:
            despesa = dict(zip(colunas, row))
            despesas_recorrentes.append(despesa)

        return despesas_recorrentes

    finally:
        conn.close()

@log_errors()
def editar_despesa_recorrente(recorrente_id, novos_dados,
                              atualizar_lancamentos_futuros=False):
    """
    Edita uma despesa recorrente.

    Args:
        recorrente_id: ID da despesa recorrente
        novos_dados: Dict com campos a atualizar (ex: {'valor': 150.0, 'descricao': 'Nova descrição'})
        atualizar_lancamentos_futuros: Se True, atualiza lançamentos futuros

    Raises:
        ValueError: Se a despesa recorrente não for encontrada
    """
    from database.validators import validate_column_name
    
    conn = conectar()
    cur = conn.cursor()

    try:
        # Verificar se a despesa recorrente existe
        cur.execute("""
            SELECT id FROM despesas_recorrentes
            WHERE id = ?
        """, (recorrente_id,))

        if not cur.fetchone():
            raise ValueError(f"Despesa recorrente com id {recorrente_id} não encontrada")

        # Construir query de UPDATE para despesas_recorrentes
        if not novos_dados:
            return  # Nada para atualizar

        # Validar nomes de colunas
        for coluna in novos_dados.keys():
            validate_column_name(coluna)

        campos = ', '.join([f"{k} = ?" for k in novos_dados.keys()])
        valores = list(novos_dados.values())
        valores.append(recorrente_id)

        # Atualizar despesa recorrente
        cur.execute(f"""
            UPDATE despesas_recorrentes SET {campos}
            WHERE id = ?
        """, valores)

        # Se atualizar_lancamentos_futuros=True, atualizar lançamentos futuros
        if atualizar_lancamentos_futuros:
            hoje = datetime.now().date().strftime('%Y-%m-%d')

            # Filtrar apenas campos que existem na tabela despesas
            campos_despesas = {}
            mapeamento = {
                'descricao': 'descricao',
                'valor': 'valor',
                'categoria_id': 'categoria_id',
                'banco_id': 'banco_id'
            }

            for campo_recorrente, campo_despesa in mapeamento.items():
                if campo_recorrente in novos_dados:
                    campos_despesas[campo_despesa] = novos_dados[campo_recorrente]

            if campos_despesas:
                # Validar nomes de colunas de despesas
                for coluna in campos_despesas.keys():
                    validate_column_name(coluna)
                
                campos_str = ', '.join([f"{k} = ?" for k in campos_despesas.keys()])
                valores_despesas = list(campos_despesas.values())
                valores_despesas.extend([recorrente_id, hoje])

                cur.execute(f"""
                    UPDATE despesas SET {campos_str}
                    WHERE despesa_recorrente_id = ?
                    AND data >= ?
                """, valores_despesas)

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@log_errors()
def desativar_despesa_recorrente(recorrente_id):
    """
    Desativa uma despesa recorrente (ativa = 0).
    Mantém lançamentos já criados.

    Args:
        recorrente_id: ID da despesa recorrente

    Raises:
        ValueError: Se a despesa recorrente não for encontrada
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        # Verificar se a despesa recorrente existe
        cur.execute("""
            SELECT id FROM despesas_recorrentes
            WHERE id = ?
        """, (recorrente_id,))

        if not cur.fetchone():
            raise ValueError(f"Despesa recorrente com id {recorrente_id} não encontrada")

        # Desativar a despesa recorrente
        cur.execute("""
            UPDATE despesas_recorrentes SET ativa = 0
            WHERE id = ?
        """, (recorrente_id,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@log_errors()
def excluir_despesa_recorrente(recorrente_id, excluir_lancamentos=False):
    """
    Exclui uma despesa recorrente.

    Args:
        recorrente_id: ID da despesa recorrente
        excluir_lancamentos: Se True, exclui também os lançamentos associados

    Raises:
        ValueError: Se a despesa recorrente não for encontrada
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        # Verificar se a despesa recorrente existe
        cur.execute("""
            SELECT id FROM despesas_recorrentes
            WHERE id = ?
        """, (recorrente_id,))

        if not cur.fetchone():
            raise ValueError(f"Despesa recorrente com id {recorrente_id} não encontrada")

        # Se excluir_lancamentos=True, excluir lançamentos associados
        if excluir_lancamentos:
            cur.execute("""
                DELETE FROM despesas
                WHERE despesa_recorrente_id = ?
            """, (recorrente_id,))
        else:
            # Apenas remover a referência dos lançamentos
            cur.execute("""
                UPDATE despesas SET despesa_recorrente_id = NULL
                WHERE despesa_recorrente_id = ?
            """, (recorrente_id,))

        # Excluir a despesa recorrente
        cur.execute("""
            DELETE FROM despesas_recorrentes
            WHERE id = ?
        """, (recorrente_id,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def listar_lancamentos_recorrente(recorrente_id):
    """
    Lista todos os lançamentos gerados de uma despesa recorrente.

    Args:
        recorrente_id: ID da despesa recorrente

    Returns:
        Lista de dicts com dados dos lançamentos ordenados por data
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        # Query para buscar lançamentos da despesa recorrente
        cur.execute("""
            SELECT
                d.id,
                d.descricao,
                d.valor,
                d.data,
                d.categoria_id,
                d.banco_id,
                d.despesa_recorrente_id,
                c.nome AS categoria_nome,
                b.nome AS banco_nome
            FROM despesas d
            LEFT JOIN categorias c ON d.categoria_id = c.id
            LEFT JOIN bancos b ON d.banco_id = b.id
            WHERE d.despesa_recorrente_id = ?
            ORDER BY d.data ASC
        """, (recorrente_id,))

        colunas = [desc[0] for desc in cur.description]
        resultados = cur.fetchall()

        # Converter para lista de dicts
        lancamentos = []
        for row in resultados:
            lancamento = dict(zip(colunas, row))
            lancamentos.append(lancamento)

        return lancamentos

    finally:
        conn.close()

# ==============================
# 💳 CARTÕES DE CRÉDITO
# ==============================

@log_errors()
def criar_cartao(nome, limite_total, dia_fechamento, dia_vencimento, bandeira=None):
    """
    Cria um novo cartão de crédito.

    Args:
        nome: Nome do cartão
        limite_total: Limite total do cartão
        dia_fechamento: Dia do fechamento da fatura (1-31)
        dia_vencimento: Dia do vencimento da fatura (1-31)
        bandeira: Bandeira do cartão (opcional)

    Returns:
        ID do cartão criado
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO cartoes
            (nome, limite_total, dia_fechamento, dia_vencimento, bandeira, status, criado_em)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (nome, limite_total, dia_fechamento, dia_vencimento, bandeira,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        cartao_id = cur.lastrowid
        conn.commit()
        return cartao_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def listar_cartoes(apenas_ativos=True):
    """
    Lista todos os cartões cadastrados.
    
    Args:
        apenas_ativos: Se True, retorna apenas cartões com status=1
        
    Returns:
        Lista de dicts com: id, nome, bandeira, limite_total, 
        limite_disponivel, limite_utilizado, percentual_uso,
        dia_fechamento, dia_vencimento, status
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Filtro de status - usar query parametrizada
        if apenas_ativos:
            cur.execute("""
                SELECT id, nome, bandeira, limite_total, dia_fechamento, 
                       dia_vencimento, status, criado_em
                FROM cartoes
                WHERE status = 1
                ORDER BY nome ASC
            """)
        else:
            cur.execute("""
                SELECT id, nome, bandeira, limite_total, dia_fechamento, 
                       dia_vencimento, status, criado_em
                FROM cartoes
                ORDER BY nome ASC
            """)
        
        cartoes = []
        for row in cur.fetchall():
            cartao_id = row[0]
            
            # Calcular limite utilizado e disponível
            limite_utilizado = calcular_limite_utilizado(cartao_id)
            limite_disponivel = row[3] - limite_utilizado  # limite_total - limite_utilizado
            percentual_uso = (limite_utilizado / row[3] * 100) if row[3] > 0 else 0
            
            cartao = {
                'id': row[0],
                'nome': row[1],
                'bandeira': row[2],
                'limite_total': row[3],
                'dia_fechamento': row[4],
                'dia_vencimento': row[5],
                'status': row[6],
                'criado_em': row[7],
                'limite_utilizado': limite_utilizado,
                'limite_disponivel': limite_disponivel,
                'percentual_uso': percentual_uso
            }
            cartoes.append(cartao)
        
        return cartoes
        
    finally:
        conn.close()

@log_errors()
def editar_cartao(cartao_id, novos_dados):
    """
    Edita informações de um cartão.
    
    Args:
        cartao_id: ID do cartão
        novos_dados: Dict com campos a atualizar
        
    Raises:
        ValueError: Se novo limite < limite_utilizado ou cartão não encontrado
    """
    from database.validators import validate_column_name
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Verificar se o cartão existe
        cur.execute("SELECT id, limite_total FROM cartoes WHERE id = ?", (cartao_id,))
        resultado = cur.fetchone()
        
        if not resultado:
            raise ValueError(f"Cartão com id {cartao_id} não encontrado")
        
        # Se está alterando o limite, validar que novo limite >= limite_utilizado
        if 'limite_total' in novos_dados:
            novo_limite = novos_dados['limite_total']
            limite_utilizado = calcular_limite_utilizado(cartao_id)
            
            if novo_limite < limite_utilizado:
                raise ValueError(
                    f"Novo limite (R$ {novo_limite:.2f}) não pode ser menor que "
                    f"o limite utilizado (R$ {limite_utilizado:.2f})"
                )
        
        # Construir query de UPDATE
        if not novos_dados:
            return  # Nada para atualizar
        
        # Validar nomes de colunas
        for coluna in novos_dados.keys():
            validate_column_name(coluna)
        
        campos = ', '.join([f"{k} = ?" for k in novos_dados.keys()])
        valores = list(novos_dados.values())
        valores.append(cartao_id)
        
        cur.execute(f"""
            UPDATE cartoes SET {campos}
            WHERE id = ?
        """, valores)
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@log_errors()
def desativar_cartao(cartao_id):
    """
    Desativa um cartão (status = 0).
    Mantém histórico de compras e faturas.
    
    Args:
        cartao_id: ID do cartão
        
    Raises:
        ValueError: Se o cartão não for encontrado
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Verificar se o cartão existe
        cur.execute("SELECT id FROM cartoes WHERE id = ?", (cartao_id,))
        
        if not cur.fetchone():
            raise ValueError(f"Cartão com id {cartao_id} não encontrado")
        
        # Desativar o cartão
        cur.execute("""
            UPDATE cartoes SET status = 0
            WHERE id = ?
        """, (cartao_id,))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@log_errors()
def excluir_cartao(cartao_id):
    """
    Exclui um cartão.
    
    Args:
        cartao_id: ID do cartão
        
    Raises:
        ValueError: Se existem compras associadas ao cartão ou cartão não encontrado
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Verificar se o cartão existe
        cur.execute("SELECT id FROM cartoes WHERE id = ?", (cartao_id,))
        
        if not cur.fetchone():
            raise ValueError(f"Cartão com id {cartao_id} não encontrado")
        
        # Verificar se existem compras associadas
        cur.execute("""
            SELECT COUNT(*) FROM compras_cartao
            WHERE cartao_id = ?
        """, (cartao_id,))
        
        count_compras = cur.fetchone()[0]
        
        if count_compras > 0:
            raise ValueError(
                f"Não é possível excluir o cartão pois existem {count_compras} "
                "compra(s) associada(s)"
            )
        
        # Excluir o cartão
        cur.execute("""
            DELETE FROM cartoes
            WHERE id = ?
        """, (cartao_id,))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@log_errors()
def calcular_limite_utilizado(cartao_id):
    """
    Calcula o limite utilizado de um cartão.
    
    Args:
        cartao_id: ID do cartão
        
    Returns:
        Float com o valor do limite utilizado
        
    Lógica:
        - Soma todas as compras em compras_cartao
        - Subtrai todos os pagamentos em pagamentos_fatura
        - limite_utilizado = SUM(compras.valor) - SUM(pagamentos.valor_pago)
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Somar todas as compras
        cur.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM compras_cartao
            WHERE cartao_id = ?
        """, (cartao_id,))
        total_compras = cur.fetchone()[0]
        
        # Somar todos os pagamentos
        cur.execute("""
            SELECT COALESCE(SUM(valor_pago), 0)
            FROM pagamentos_fatura
            WHERE cartao_id = ?
        """, (cartao_id,))
        total_pagamentos = cur.fetchone()[0]
        
        # Calcular limite utilizado
        limite_utilizado = total_compras - total_pagamentos
        
        return max(0, limite_utilizado)  # Não pode ser negativo
        
    finally:
        conn.close()


@log_errors()
def calcular_limite_disponivel(cartao_id):
    """
    Calcula o limite disponível de um cartão.
    
    Args:
        cartao_id: ID do cartão
        
    Returns:
        Float com o valor do limite disponível
        
    Lógica:
        - limite_disponivel = limite_total - limite_utilizado
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar limite total do cartão
        cur.execute("""
            SELECT limite_total
            FROM cartoes
            WHERE id = ?
        """, (cartao_id,))
        resultado = cur.fetchone()
        
        if not resultado:
            raise ValueError(f"Cartão com id {cartao_id} não encontrado")
        
        limite_total = resultado[0]
        
        # Calcular limite utilizado
        limite_utilizado = calcular_limite_utilizado(cartao_id)
        
        # Calcular limite disponível
        limite_disponivel = limite_total - limite_utilizado
        
        return limite_disponivel
        
    finally:
        conn.close()


def obter_info_limite(cartao_id):
    """
    Obtém informações completas sobre o limite de um cartão.
    
    Args:
        cartao_id: ID do cartão
        
    Returns:
        Dict com:
            - limite_total: Limite total do cartão
            - limite_utilizado: Valor utilizado
            - limite_disponivel: Valor disponível
            - percentual_uso: (limite_utilizado / limite_total) * 100
            - alerta_80: True se percentual_uso >= 80
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar limite total do cartão
        cur.execute("""
            SELECT limite_total
            FROM cartoes
            WHERE id = ?
        """, (cartao_id,))
        resultado = cur.fetchone()
        
        if not resultado:
            raise ValueError(f"Cartão com id {cartao_id} não encontrado")
        
        limite_total = resultado[0]
        
        # Calcular limite utilizado e disponível
        limite_utilizado = calcular_limite_utilizado(cartao_id)
        limite_disponivel = limite_total - limite_utilizado
        
        # Calcular percentual de uso
        percentual_uso = (limite_utilizado / limite_total * 100) if limite_total > 0 else 0
        
        # Verificar alerta de 80%
        alerta_80 = percentual_uso >= 80
        
        return {
            'limite_total': limite_total,
            'limite_utilizado': limite_utilizado,
            'limite_disponivel': limite_disponivel,
            'percentual_uso': percentual_uso,
            'alerta_80': alerta_80
        }
        
    finally:
        conn.close()


@log_errors()
def calcular_mes_fatura(data_compra, dia_fechamento):
    """
    Calcula o mês da fatura baseado na data da compra e dia de fechamento.
    
    Args:
        data_compra: Data da compra (string YYYY-MM-DD ou objeto date)
        dia_fechamento: Dia do mês de fechamento (1-31)
        
    Returns:
        String no formato YYYY-MM representando o mês da fatura
        
    Lógica:
        - Se dia da compra < dia_fechamento: fatura do mesmo mês
        - Se dia da compra >= dia_fechamento: fatura do mês seguinte
        - Se dia_fechamento > último dia do mês: usa último dia do mês
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from calendar import monthrange
    
    # Converter data_compra para objeto date
    if isinstance(data_compra, str):
        data_compra = datetime.strptime(data_compra, '%Y-%m-%d').date()
    
    # Obter último dia do mês da compra
    ultimo_dia_mes = monthrange(data_compra.year, data_compra.month)[1]
    
    # Ajustar dia_fechamento se for maior que o último dia do mês
    dia_fechamento_efetivo = min(dia_fechamento, ultimo_dia_mes)
    
    # Determinar mês da fatura
    if data_compra.day < dia_fechamento_efetivo:
        # Compra antes do fechamento: fatura do mesmo mês
        mes_fatura = data_compra
    else:
        # Compra no dia ou após o fechamento: fatura do mês seguinte
        mes_fatura = data_compra + relativedelta(months=1)
    
    return mes_fatura.strftime('%Y-%m')


@log_errors()
def calcular_data_vencimento(mes_fatura, dia_vencimento):
    """
    Calcula a data de vencimento de uma fatura.
    
    Args:
        mes_fatura: Mês da fatura no formato YYYY-MM
        dia_vencimento: Dia do mês de vencimento (1-31)
        
    Returns:
        Data de vencimento no formato YYYY-MM-DD
        
    Lógica:
        - Se dia_vencimento > último dia do mês: usa último dia do mês
    """
    from datetime import datetime
    from calendar import monthrange
    
    # Converter mes_fatura para objeto date
    data_fatura = datetime.strptime(mes_fatura, '%Y-%m')
    
    # Obter último dia do mês da fatura
    ultimo_dia_mes = monthrange(data_fatura.year, data_fatura.month)[1]
    
    # Ajustar dia_vencimento se for maior que o último dia do mês
    dia_vencimento_efetivo = min(dia_vencimento, ultimo_dia_mes)
    
    # Construir data de vencimento
    data_vencimento = datetime(data_fatura.year, data_fatura.month, dia_vencimento_efetivo)
    
    return data_vencimento.strftime('%Y-%m-%d')


@log_errors()
def criar_compra_cartao(cartao_id, descricao, valor, data_compra, categoria_id=None):
    """
    Registra uma compra à vista no cartão.

    Args:
        cartao_id: ID do cartão
        descricao: Descrição da compra
        valor: Valor da compra
        data_compra: Data da compra
        categoria_id: ID da categoria (opcional)

    Returns:
        ID da compra criada
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        # Obter informações do cartão
        cur.execute("SELECT dia_fechamento FROM cartoes WHERE id = ?", (cartao_id,))
        resultado = cur.fetchone()
        if not resultado:
            raise ValueError(f"Cartão {cartao_id} não encontrado")

        dia_fechamento = resultado[0]

        # Calcular mês da fatura
        mes_fatura = calcular_mes_fatura(data_compra, dia_fechamento)

        # Inserir compra
        cur.execute("""
            INSERT INTO compras_cartao
            (cartao_id, descricao, valor, data_compra, mes_fatura, categoria_id,
             parcela_atual, total_parcelas, compra_parcelada_id, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1, NULL, ?)
        """, (cartao_id, descricao, valor, data_compra, mes_fatura, categoria_id,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        compra_id = cur.lastrowid
        conn.commit()
        return compra_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()



@log_errors()
def criar_compra_parcelada_cartao(cartao_id, descricao, valor_total,
                                  numero_parcelas, data_compra, categoria_id=None):
    """
    Registra uma compra parcelada no cartão.

    Args:
        cartao_id: ID do cartão
        descricao: Descrição da compra
        valor_total: Valor total da compra
        numero_parcelas: Número de parcelas
        data_compra: Data da compra
        categoria_id: ID da categoria (opcional)

    Returns:
        ID da compra parcelada criada
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        # Obter informações do cartão
        cur.execute("SELECT dia_fechamento FROM cartoes WHERE id = ?", (cartao_id,))
        resultado = cur.fetchone()
        if not resultado:
            raise ValueError(f"Cartão {cartao_id} não encontrado")

        dia_fechamento = resultado[0]
        valor_parcela = valor_total / numero_parcelas

        # Gerar ID único para agrupar as parcelas
        # Usar timestamp + cartao_id para garantir unicidade
        compra_parcelada_id = int(datetime.now().timestamp() * 1000) + cartao_id

        # Gerar as parcelas - converter data_compra para datetime
        if isinstance(data_compra, str):
            data_parcela = datetime.strptime(data_compra, '%Y-%m-%d')
        else:
            # Já é um objeto date ou datetime
            data_parcela = datetime.combine(data_compra, datetime.min.time()) if isinstance(data_compra, date) else data_compra

        for i in range(1, numero_parcelas + 1):
            mes_fatura = calcular_mes_fatura(data_parcela.strftime('%Y-%m-%d'), dia_fechamento)

            cur.execute("""
                INSERT INTO compras_cartao
                (cartao_id, descricao, valor, data_compra, mes_fatura, categoria_id,
                 parcela_atual, total_parcelas, compra_parcelada_id, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cartao_id, f"{descricao} ({i}/{numero_parcelas})", valor_parcela,
                  data_parcela.strftime('%Y-%m-%d'), mes_fatura, categoria_id,
                  i, numero_parcelas, compra_parcelada_id,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            # Avançar para o próximo mês
            data_parcela = data_parcela + relativedelta(months=1)

        conn.commit()
        return compra_parcelada_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()



@log_errors()
def editar_compra_cartao(compra_id, novos_dados):
    """
    Edita uma compra no cartão.
    
    Args:
        compra_id: ID da compra
        novos_dados: Dict com campos a atualizar
        
    Comportamento:
        - Se alterar valor ou data_compra: recalcula mes_fatura
        - Recalcula limite_utilizado
    """
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar compra atual
        cur.execute("""
            SELECT cartao_id, descricao, valor, data_compra, categoria_id, mes_fatura
            FROM compras_cartao
            WHERE id = ?
        """, (compra_id,))
        
        compra_atual = cur.fetchone()
        if not compra_atual:
            raise ValueError(f"Compra com ID {compra_id} não encontrada")
        
        cartao_id, descricao, valor, data_compra, categoria_id, mes_fatura = compra_atual
        
        # Aplicar novos dados
        if 'descricao' in novos_dados:
            descricao = novos_dados['descricao']
            if not descricao or not descricao.strip():
                raise ValueError("Descrição é obrigatória")
        
        if 'valor' in novos_dados:
            valor = novos_dados['valor']
            if valor <= 0:
                raise ValueError("Valor deve ser maior que zero")
        
        if 'data_compra' in novos_dados:
            data_compra = novos_dados['data_compra']
        
        if 'categoria_id' in novos_dados:
            categoria_id = novos_dados['categoria_id']
        
        # Recalcular mes_fatura se data ou valor mudaram
        if 'data_compra' in novos_dados or 'valor' in novos_dados:
            # Buscar dia_fechamento do cartão
            cur.execute("SELECT dia_fechamento FROM cartoes WHERE id = ?", (cartao_id,))
            dia_fechamento = cur.fetchone()[0]
            mes_fatura = calcular_mes_fatura(data_compra, dia_fechamento)
        
        # Atualizar compra
        cur.execute("""
            UPDATE compras_cartao
            SET descricao = ?, valor = ?, data_compra = ?, categoria_id = ?, mes_fatura = ?
            WHERE id = ?
        """, (descricao, valor, data_compra, categoria_id, mes_fatura, compra_id))
        
        conn.commit()
        
        logger.info(f"Compra editada: id={compra_id}, cartao_id={cartao_id}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao editar compra no cartão: {str(e)}", exc_info=True)
        raise
    finally:
        conn.close()


@log_errors()
def excluir_compra_cartao(compra_id):
    """
    Exclui uma compra do cartão.
    
    Comportamento:
        - Remove registro de compras_cartao
        - Recalcula limite_utilizado
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar informações da compra antes de excluir
        cur.execute("SELECT cartao_id, valor FROM compras_cartao WHERE id = ?", (compra_id,))
        compra = cur.fetchone()
        
        if not compra:
            raise ValueError(f"Compra com ID {compra_id} não encontrada")
        
        cartao_id, valor = compra
        
        # Excluir compra
        cur.execute("DELETE FROM compras_cartao WHERE id = ?", (compra_id,))
        
        conn.commit()
        
        logger.info(f"Compra excluída: id={compra_id}, cartao_id={cartao_id}, valor={valor:.2f}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao excluir compra no cartão: {str(e)}", exc_info=True)
        raise
    finally:
        conn.close()


@log_errors()
def excluir_compra_parcelada_cartao(compra_parcelada_id):
    """
    Exclui todas as parcelas de uma compra parcelada.
    
    Args:
        compra_parcelada_id: ID da compra parcelada
        
    Comportamento:
        - Remove todos os registros com esse compra_parcelada_id
        - Recalcula limite_utilizado
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar informações das parcelas antes de excluir
        cur.execute("""
            SELECT cartao_id, COUNT(*), SUM(valor)
            FROM compras_cartao
            WHERE compra_parcelada_id = ?
            GROUP BY cartao_id
        """, (compra_parcelada_id,))
        
        resultado = cur.fetchone()
        if not resultado:
            raise ValueError(f"Compra parcelada com ID {compra_parcelada_id} não encontrada")
        
        cartao_id, num_parcelas, valor_total = resultado
        
        # Excluir todas as parcelas
        cur.execute("DELETE FROM compras_cartao WHERE compra_parcelada_id = ?", (compra_parcelada_id,))
        
        conn.commit()
        
        logger.info(
            f"Compra parcelada excluída: compra_parcelada_id={compra_parcelada_id}, "
            f"cartao_id={cartao_id}, num_parcelas={num_parcelas}, valor_total={valor_total:.2f}"
        )
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao excluir compra parcelada no cartão: {str(e)}", exc_info=True)
        raise
    finally:
        conn.close()


@log_errors()
def editar_parcela_cartao(compra_id, novos_dados, aplicar_futuras=False):
    """
    Edita uma parcela específica de uma compra parcelada.
    
    Args:
        compra_id: ID da parcela
        novos_dados: Dict com campos a atualizar
        aplicar_futuras: Se True, aplica a todas parcelas futuras
        
    Comportamento:
        - Se aplicar_futuras=False: edita apenas esta parcela
        - Se aplicar_futuras=True: edita esta e todas com parcela_numero maior
    """
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar parcela atual
        cur.execute("""
            SELECT cartao_id, compra_parcelada_id, parcela_numero, descricao, 
                   valor, data_compra, categoria_id, mes_fatura
            FROM compras_cartao
            WHERE id = ?
        """, (compra_id,))
        
        parcela_atual = cur.fetchone()
        if not parcela_atual:
            raise ValueError(f"Parcela com ID {compra_id} não encontrada")
        
        (cartao_id, compra_parcelada_id, parcela_numero, descricao, 
         valor, data_compra, categoria_id, mes_fatura) = parcela_atual
        
        if not compra_parcelada_id:
            raise ValueError("Esta compra não é parcelada")
        
        # Aplicar novos dados
        if 'descricao' in novos_dados:
            descricao = novos_dados['descricao']
            if not descricao or not descricao.strip():
                raise ValueError("Descrição é obrigatória")
        
        if 'valor' in novos_dados:
            valor = novos_dados['valor']
            if valor <= 0:
                raise ValueError("Valor deve ser maior que zero")
        
        if 'data_compra' in novos_dados:
            data_compra = novos_dados['data_compra']
        
        if 'categoria_id' in novos_dados:
            categoria_id = novos_dados['categoria_id']
        
        # Recalcular mes_fatura se data mudou
        if 'data_compra' in novos_dados:
            cur.execute("SELECT dia_fechamento FROM cartoes WHERE id = ?", (cartao_id,))
            dia_fechamento = cur.fetchone()[0]
            mes_fatura = calcular_mes_fatura(data_compra, dia_fechamento)
        
        if aplicar_futuras:
            # Atualizar esta parcela e todas as futuras
            cur.execute("""
                UPDATE compras_cartao
                SET descricao = ?, valor = ?, categoria_id = ?
                WHERE compra_parcelada_id = ? AND parcela_numero >= ?
            """, (descricao, valor, categoria_id, compra_parcelada_id, parcela_numero))
            
            logger.info(
                f"Parcelas editadas (aplicar_futuras=True): compra_parcelada_id={compra_parcelada_id}, "
                f"a partir de parcela_numero={parcela_numero}"
            )
        else:
            # Atualizar apenas esta parcela
            cur.execute("""
                UPDATE compras_cartao
                SET descricao = ?, valor = ?, data_compra = ?, categoria_id = ?, mes_fatura = ?
                WHERE id = ?
            """, (descricao, valor, data_compra, categoria_id, mes_fatura, compra_id))
            
            logger.info(f"Parcela editada: id={compra_id}, parcela_numero={parcela_numero}")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao editar parcela no cartão: {str(e)}", exc_info=True)
        raise
    finally:
        conn.close()


def listar_compras_fatura(cartao_id, mes_fatura):
    """
    Lista todas as compras de uma fatura específica.
    
    Args:
        cartao_id: ID do cartão
        mes_fatura: Mês da fatura no formato YYYY-MM
        
    Returns:
        Lista de dicts com: id, descricao, valor, data_compra,
        categoria_nome, parcela_info (ex: "3/12" ou None)
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT c.id, c.descricao, c.valor, c.data_compra,
                   cat.nome AS categoria_nome,
                   c.parcela_numero, c.parcela_total
            FROM compras_cartao c
            LEFT JOIN categorias cat ON c.categoria_id = cat.id
            WHERE c.cartao_id = ? AND c.mes_fatura = ?
            ORDER BY c.data_compra ASC
        """, (cartao_id, mes_fatura))
        
        compras = []
        for row in cur.fetchall():
            compra = {
                'id': row[0],
                'descricao': row[1],
                'valor': row[2],
                'data_compra': row[3],
                'categoria_nome': row[4],
                'parcela_info': f"{row[5]}/{row[6]}" if row[5] else None
            }
            compras.append(compra)
        
        return compras
        
    finally:
        conn.close()


def obter_fatura(cartao_id, mes_fatura):
    """
    Obtém informações completas de uma fatura.
    
    Args:
        cartao_id: ID do cartão
        mes_fatura: Mês da fatura no formato YYYY-MM
        
    Returns:
        Dict com:
            - compras: Lista de todas as compras do período
            - valor_total: Soma de todas as compras
            - valor_pago: Soma de todos os pagamentos
            - saldo_devedor: valor_total - valor_pago
            - data_vencimento: Data de vencimento da fatura
            - status: 'pendente', 'paga_parcial', 'paga_total', 'vencida'
    """
    from datetime import datetime, date
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # 1. Buscar todas as compras do período
        compras = listar_compras_fatura(cartao_id, mes_fatura)
        
        # 2. Calcular valor total
        valor_total = sum(compra['valor'] for compra in compras)
        
        # 3. Buscar todos os pagamentos do período
        cur.execute("""
            SELECT COALESCE(SUM(valor_pago), 0)
            FROM pagamentos_fatura
            WHERE cartao_id = ? AND mes_fatura = ?
        """, (cartao_id, mes_fatura))
        valor_pago = cur.fetchone()[0]
        
        # 4. Calcular saldo devedor
        saldo_devedor = valor_total - valor_pago
        
        # 5. Buscar informações do cartão para calcular data de vencimento
        cur.execute("""
            SELECT dia_vencimento FROM cartoes WHERE id = ?
        """, (cartao_id,))
        resultado = cur.fetchone()
        if not resultado:
            raise ValueError(f"Cartão com ID {cartao_id} não encontrado")
        
        dia_vencimento = resultado[0]
        
        # 6. Calcular data de vencimento
        data_vencimento = calcular_data_vencimento(mes_fatura, dia_vencimento)
        
        # 7. Determinar status
        hoje = date.today()
        if saldo_devedor == 0:
            status = 'paga_total'
        elif valor_pago > 0:
            status = 'paga_parcial'
        elif datetime.strptime(data_vencimento, '%Y-%m-%d').date() < hoje:
            status = 'vencida'
        else:
            status = 'pendente'
        
        return {
            'compras': compras,
            'valor_total': valor_total,
            'valor_pago': valor_pago,
            'saldo_devedor': saldo_devedor,
            'data_vencimento': data_vencimento,
            'status': status
        }
        
    finally:
        conn.close()


def listar_faturas_cartao(cartao_id, data_inicio=None, data_fim=None):
    """
    Lista todas as faturas de um cartão em um período.
    
    Args:
        cartao_id: ID do cartão
        data_inicio: Data inicial (opcional, formato YYYY-MM)
        data_fim: Data final (opcional, formato YYYY-MM)
        
    Returns:
        Lista de dicts com: mes_fatura, valor_total, valor_pago,
        saldo_devedor, data_vencimento, status
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar todos os meses únicos que têm compras para este cartão
        query = """
            SELECT DISTINCT mes_fatura
            FROM compras_cartao
            WHERE cartao_id = ?
        """
        params = [cartao_id]
        
        if data_inicio:
            query += " AND mes_fatura >= ?"
            params.append(data_inicio)
        
        if data_fim:
            query += " AND mes_fatura <= ?"
            params.append(data_fim)
        
        query += " ORDER BY mes_fatura ASC"
        
        cur.execute(query, params)
        meses = [row[0] for row in cur.fetchall()]
        
        # Para cada mês, obter informações completas da fatura
        faturas = []
        for mes_fatura in meses:
            fatura = obter_fatura(cartao_id, mes_fatura)
            faturas.append({
                'mes_fatura': mes_fatura,
                'valor_total': fatura['valor_total'],
                'valor_pago': fatura['valor_pago'],
                'saldo_devedor': fatura['saldo_devedor'],
                'data_vencimento': fatura['data_vencimento'],
                'status': fatura['status']
            })
        
        return faturas
        
    finally:
        conn.close()


def registrar_pagamento_fatura(cartao_id, mes_fatura, valor_pago, 
                               data_pagamento, banco_id):
    """
    Registra um pagamento de fatura.
    
    Args:
        cartao_id: ID do cartão
        mes_fatura: Mês da fatura no formato YYYY-MM
        valor_pago: Valor do pagamento (deve ser > 0)
        data_pagamento: Data do pagamento (formato YYYY-MM-DD)
        banco_id: ID do banco de origem do pagamento
        
    Returns:
        ID do pagamento criado
        
    Raises:
        ValueError: Se valor_pago > saldo_devedor da fatura
        
    Comportamento:
        1. Valida que valor_pago <= saldo_devedor
        2. Insere registro em pagamentos_fatura
        3. Debita valor do banco (atualiza saldo)
        4. Cria despesa na tabela despesas com descrição 
           "Pagamento Fatura [Nome Cartão] - [Mês/Ano]"
        5. Vincula despesa_id no registro de pagamento
    """
    from datetime import datetime
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # 1. Obter informações da fatura
        fatura = obter_fatura(cartao_id, mes_fatura)
        
        # 2. Validar valor do pagamento
        if valor_pago <= 0:
            raise ValueError("Valor do pagamento deve ser maior que zero")
        
        if valor_pago > fatura['saldo_devedor']:
            raise ValueError(f"Valor do pagamento (R$ {valor_pago:.2f}) "
                           f"excede o saldo devedor (R$ {fatura['saldo_devedor']:.2f})")
        
        # 3. Buscar nome do cartão para descrição da despesa
        cur.execute("SELECT nome FROM cartoes WHERE id = ?", (cartao_id,))
        result = cur.fetchone()
        if not result:
            raise ValueError(f"Cartão com ID {cartao_id} não encontrado")
        nome_cartao = result[0]
        
        # 4. Criar despesa na tabela despesas (já paga, pois é pagamento de fatura)
        mes_ano = datetime.strptime(mes_fatura, '%Y-%m').strftime('%m/%Y')
        descricao_despesa = f"Pagamento Fatura {nome_cartao} - {mes_ano}"
        
        cur.execute("""
            INSERT INTO despesas (descricao, valor, data, banco_id, pago)
            VALUES (?, ?, ?, ?, 1)
        """, (descricao_despesa, valor_pago, data_pagamento, banco_id))
        
        despesa_id = cur.lastrowid
        
        # 5. Debitar valor do banco
        cur.execute("""
            UPDATE bancos SET saldo_inicial = saldo_inicial - ?
            WHERE id = ?
        """, (valor_pago, banco_id))
        
        # 6. Registrar pagamento em pagamentos_fatura
        cur.execute("""
            INSERT INTO pagamentos_fatura 
            (cartao_id, mes_fatura, valor_pago, data_pagamento, 
             banco_id, despesa_id, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cartao_id,
            mes_fatura,
            valor_pago,
            data_pagamento,
            banco_id,
            despesa_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        pagamento_id = cur.lastrowid
        
        conn.commit()
        
        # Emitir sinal de atualização (se disponível)
        try:
            from PyQt6.QtCore import QObject
            # Tentar emitir sinal se o sistema de sinais estiver configurado
            # Isso será implementado quando a UI for criada
        except ImportError as e:
            logger.debug(f"PyQt6 não disponível para emissão de sinais: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao tentar emitir sinal: {e}")
        
        return pagamento_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def listar_pagamentos_fatura(cartao_id, mes_fatura=None):
    """
    Lista pagamentos de uma fatura ou de todas as faturas de um cartão.
    
    Args:
        cartao_id: ID do cartão
        mes_fatura: Mês da fatura (opcional, formato YYYY-MM)
        
    Returns:
        Lista de dicts com: id, mes_fatura, valor_pago, data_pagamento,
        banco_nome, despesa_id
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Construir query com JOIN para obter nome do banco
        query = """
            SELECT p.id, p.mes_fatura, p.valor_pago, p.data_pagamento,
                   b.nome AS banco_nome, p.despesa_id
            FROM pagamentos_fatura p
            LEFT JOIN bancos b ON p.banco_id = b.id
            WHERE p.cartao_id = ?
        """
        params = [cartao_id]
        
        # Filtrar por mês da fatura se especificado
        if mes_fatura:
            query += " AND p.mes_fatura = ?"
            params.append(mes_fatura)
        
        query += " ORDER BY p.data_pagamento DESC"
        
        cur.execute(query, params)
        
        pagamentos = []
        for row in cur.fetchall():
            pagamentos.append({
                'id': row[0],
                'mes_fatura': row[1],
                'valor_pago': row[2],
                'data_pagamento': row[3],
                'banco_nome': row[4],
                'despesa_id': row[5]
            })
        
        return pagamentos
        
    finally:
        conn.close()


def listar_compras_cartao(cartao_id, data_inicio=None, data_fim=None, categoria_id=None):
    """
    Lista compras de um cartão com filtros opcionais.
    
    Args:
        cartao_id: ID do cartão
        data_inicio: Data inicial (opcional, formato YYYY-MM-DD)
        data_fim: Data final (opcional, formato YYYY-MM-DD)
        categoria_id: Filtrar por categoria (opcional)
        
    Returns:
        Lista de dicts com todas as informações das compras
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Construir query com JOIN para obter nome da categoria
        query = """
            SELECT c.id, c.descricao, c.valor, c.data_compra, c.mes_fatura,
                   c.parcela_numero, c.parcela_total, c.compra_parcelada_id,
                   cat.nome AS categoria_nome
            FROM compras_cartao c
            LEFT JOIN categorias cat ON c.categoria_id = cat.id
            WHERE c.cartao_id = ?
        """
        params = [cartao_id]
        
        # Adicionar filtros opcionais
        if data_inicio:
            query += " AND c.data_compra >= ?"
            params.append(data_inicio)
        
        if data_fim:
            query += " AND c.data_compra <= ?"
            params.append(data_fim)
        
        if categoria_id:
            query += " AND c.categoria_id = ?"
            params.append(categoria_id)
        
        query += " ORDER BY c.data_compra DESC"
        
        cur.execute(query, params)
        
        compras = []
        for row in cur.fetchall():
            # Formatar informação de parcela
            parcela_info = None
            if row[5] is not None and row[6] is not None:
                parcela_info = f"{row[5]}/{row[6]}"
            
            compras.append({
                'id': row[0],
                'descricao': row[1],
                'valor': row[2],
                'data_compra': row[3],
                'mes_fatura': row[4],
                'parcela_numero': row[5],
                'parcela_total': row[6],
                'compra_parcelada_id': row[7],
                'categoria_nome': row[8],
                'parcela_info': parcela_info
            })
        
        return compras
        
    finally:
        conn.close()


@log_errors()
def calcular_total_por_categoria(cartao_id, data_inicio, data_fim):
    """
    Calcula total gasto por categoria em um período.
    
    Args:
        cartao_id: ID do cartão
        data_inicio: Data inicial (formato YYYY-MM-DD)
        data_fim: Data final (formato YYYY-MM-DD)
        
    Returns:
        Lista de dicts com: categoria_nome, total
    """
    conn = conectar()
    cur = conn.cursor()
    
    try:
        query = """
            SELECT cat.nome AS categoria_nome, 
                   COALESCE(SUM(c.valor), 0) AS total
            FROM compras_cartao c
            LEFT JOIN categorias cat ON c.categoria_id = cat.id
            WHERE c.cartao_id = ?
              AND c.data_compra >= ?
              AND c.data_compra <= ?
            GROUP BY c.categoria_id, cat.nome
            ORDER BY total DESC
        """
        
        cur.execute(query, (cartao_id, data_inicio, data_fim))
        
        totais = []
        for row in cur.fetchall():
            totais.append({
                'categoria_nome': row[0] if row[0] else 'Sem categoria',
                'total': row[1]
            })
        
        return totais
        
    finally:
        conn.close()


@log_errors()
def calcular_media_gastos_mensais(cartao_id, numero_meses=6):
    """
    Calcula a média de gastos mensais de um cartão.
    
    Args:
        cartao_id: ID do cartão
        numero_meses: Número de meses para calcular a média (padrão: 6)
        
    Returns:
        Float com a média de gastos mensais
    """
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Calcular data de início (N meses atrás)
        data_fim = datetime.now().date()
        data_inicio = data_fim - relativedelta(months=numero_meses)
        
        # Buscar total de compras no período
        query = """
            SELECT COALESCE(SUM(valor), 0) AS total
            FROM compras_cartao
            WHERE cartao_id = ?
              AND data_compra >= ?
              AND data_compra <= ?
        """
        
        cur.execute(query, (cartao_id, data_inicio.strftime('%Y-%m-%d'), 
                           data_fim.strftime('%Y-%m-%d')))
        
        total = cur.fetchone()[0]
        
        # Calcular média
        if numero_meses > 0:
            media = total / numero_meses
        else:
            media = 0.0
        
        return media
        
    finally:
        conn.close()


def listar_compras_parceladas_andamento(cartao_id):
    """
    Lista compras parceladas que ainda têm parcelas futuras.
    
    Args:
        cartao_id: ID do cartão
        
    Returns:
        Lista de dicts com: compra_parcelada_id, descricao, valor_total,
        parcelas_pagas, parcelas_pendentes, valor_parcela
    """
    from datetime import datetime
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Obter mês atual no formato YYYY-MM
        mes_atual = datetime.now().strftime('%Y-%m')
        
        # Buscar compras parceladas que têm parcelas futuras
        query = """
            SELECT compra_parcelada_id,
                   descricao,
                   parcela_total,
                   valor AS valor_parcela,
                   COUNT(*) AS total_parcelas,
                   SUM(CASE WHEN mes_fatura <= ? THEN 1 ELSE 0 END) AS parcelas_pagas,
                   SUM(CASE WHEN mes_fatura > ? THEN 1 ELSE 0 END) AS parcelas_pendentes
            FROM compras_cartao
            WHERE cartao_id = ?
              AND compra_parcelada_id IS NOT NULL
            GROUP BY compra_parcelada_id
            HAVING parcelas_pendentes > 0
            ORDER BY descricao
        """
        
        cur.execute(query, (mes_atual, mes_atual, cartao_id))
        
        compras = []
        for row in cur.fetchall():
            compra_parcelada_id = row[0]
            descricao = row[1]
            parcela_total = row[2]
            valor_parcela = row[3]
            parcelas_pagas = row[5]
            parcelas_pendentes = row[6]
            
            # Calcular valor total
            valor_total = valor_parcela * parcela_total
            
            compras.append({
                'compra_parcelada_id': compra_parcelada_id,
                'descricao': descricao,
                'valor_total': valor_total,
                'parcelas_pagas': parcelas_pagas,
                'parcelas_pendentes': parcelas_pendentes,
                'valor_parcela': valor_parcela
            })
        
        return compras
        
    finally:
        conn.close()


# ============================================================================
# FASE 4: INTEGRAÇÃO DE DESPESAS AUTOMÁTICAS
# ============================================================================

def verificar_parcela_existe(despesa_parcelada_id, parcela_numero):
    """
    Verifica se uma parcela específica já foi gerada.
    
    Args:
        despesa_parcelada_id: ID da despesa parcelada
        parcela_numero: Número da parcela (1-indexed)
        
    Returns:
        bool: True se a parcela já existe, False caso contrário
    """
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM despesas
            WHERE despesa_parcelada_id = ?
            AND parcela_numero = ?
        """, (despesa_parcelada_id, parcela_numero))
        
        count = cur.fetchone()[0]
        return count > 0


def verificar_despesa_fatura_existe(cartao_id, mes_fatura):
    """
    Verifica se já existe despesa para uma fatura específica.
    
    Args:
        cartao_id: ID do cartão
        mes_fatura: Mês da fatura (YYYY-MM)
        
    Returns:
        bool: True se a despesa já existe, False caso contrário
    """
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM despesas
            WHERE cartao_id = ?
            AND mes_fatura = ?
        """, (cartao_id, mes_fatura))
        
        count = cur.fetchone()[0]
        return count > 0


def calcular_valor_fatura(cartao_id, mes_fatura):
    """
    Calcula o valor total de uma fatura.
    
    Args:
        cartao_id: ID do cartão
        mes_fatura: Mês da fatura (YYYY-MM)
        
    Returns:
        float: Valor total da fatura (soma de todas as compras)
    """
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(valor), 0) FROM compras_cartao
            WHERE cartao_id = ?
            AND mes_fatura = ?
        """, (cartao_id, mes_fatura))
        
        valor_total = cur.fetchone()[0]
        return float(valor_total)


def obter_ou_criar_categoria_cartao():
    """
    Obtém o ID da categoria "Cartão de Crédito" ou cria se não existir.
    
    Returns:
        int: ID da categoria "Cartão de Crédito"
    """
    from datetime import datetime
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Tentar buscar categoria existente
        cur.execute("""
            SELECT id FROM categorias
            WHERE nome = 'Cartão de Crédito'
            AND tipo = 'despesa'
        """)
        
        resultado = cur.fetchone()
        
        if resultado:
            return resultado[0]
        
        # Criar categoria se não existir
        cur.execute("""
            INSERT INTO categorias (nome, tipo, criado_em)
            VALUES ('Cartão de Crédito', 'despesa', ?)
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        
        return cur.lastrowid



def gerar_parcelas_pendentes():
    """
    Gera parcelas faltantes de todas as despesas parceladas ativas.
    Chamada no startup do sistema.
    
    Lógica:
    - Busca todas as despesas_parceladas
    - Para cada uma, verifica quais parcelas já foram geradas
    - Gera apenas parcelas com data >= mês atual
    - Evita duplicação verificando existência antes de criar
    
    Returns:
        int: Número de parcelas criadas
    """
    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta
    from utils.logger import logger
    
    db = get_db_manager()
    hoje = date.today()
    mes_atual = date(hoje.year, hoje.month, 1)  # Primeiro dia do mês atual
    parcelas_criadas = 0
    
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            
            # 1. Buscar todas as despesas parceladas
            cur.execute("""
                SELECT id, descricao, valor_total, numero_parcelas,
                       data_primeira_parcela, categoria_id, banco_id
                FROM despesas_parceladas
            """)
            
            despesas_parceladas = cur.fetchall()
            
            for dp in despesas_parceladas:
                dp_id, descricao, valor_total, num_parcelas, data_primeira, cat_id, banco_id = dp
                
                # 2. Calcular valor de cada parcela
                valor_parcela = valor_total / num_parcelas
                
                # 3. Converter data_primeira_parcela
                if isinstance(data_primeira, str):
                    data_base = datetime.strptime(data_primeira, '%Y-%m-%d').date()
                else:
                    # Já é um objeto date ou datetime
                    data_base = data_primeira if isinstance(data_primeira, date) else data_primeira.date()
                
                # 4. Para cada parcela
                for i in range(num_parcelas):
                    # Calcular data da parcela
                    data_parcela = data_base + relativedelta(months=i)
                    
                    # Gerar apenas se data >= mês atual
                    if data_parcela < mes_atual:
                        continue
                    
                    # 5. Verificar se parcela já existe
                    if verificar_parcela_existe(dp_id, i + 1):
                        logger.debug(f"Parcela {i+1} já existe para despesa_parcelada_id={dp_id}")
                        continue
                    
                    # 6. Criar parcela
                    cur.execute("""
                        INSERT INTO despesas
                        (descricao, valor, data, categoria_id, banco_id,
                         parcela_numero, parcela_total, despesa_parcelada_id, pago)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (descricao, valor_parcela, data_parcela.strftime('%Y-%m-%d'),
                          cat_id, banco_id, i + 1, num_parcelas, dp_id))
                    
                    parcelas_criadas += 1
                    logger.debug(f"Parcela {i+1}/{num_parcelas} criada para despesa_parcelada_id={dp_id}")
            
            # Commit automático pelo context manager
        
        if parcelas_criadas > 0:
            logger.info(f"Geradas {parcelas_criadas} parcelas pendentes")
        
        return parcelas_criadas
        
    except Exception as e:
        logger.error(f"Erro ao gerar parcelas pendentes: {e}", exc_info=True)
        return 0



def gerar_despesas_faturas_vencidas():
    """
    Gera despesas para faturas de cartão vencidas.
    Chamada no startup do sistema.
    
    Lógica:
    - Busca todos os cartões ativos
    - Para cada cartão, identifica faturas vencidas (data_vencimento <= hoje)
    - Calcula valor total de cada fatura
    - Verifica se já existe despesa para essa fatura
    - Se não existe, cria despesa com:
      * descricao: "Fatura [Nome Cartão] - [Mês/Ano]"
      * valor: valor total da fatura
      * categoria: "Cartão de Crédito" (cria se não existir)
      * banco_id: NULL
      * cartao_id: ID do cartão
      * mes_fatura: mês da fatura (YYYY-MM)
      * pago: 0
    
    Returns:
        int: Número de despesas de fatura criadas
    """
    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta
    from utils.logger import logger
    from database.cards import calcular_data_vencimento
    
    db = get_db_manager()
    hoje = date.today()
    despesas_criadas = 0
    
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            
            # 1. Obter ou criar categoria "Cartão de Crédito"
            categoria_id = obter_ou_criar_categoria_cartao()
            
            # 2. Buscar todos os cartões ativos
            cur.execute("""
                SELECT id, nome, dia_fechamento, dia_vencimento
                FROM cartoes
                WHERE status = 1
            """)
            
            cartoes = cur.fetchall()
            
            for cartao in cartoes:
                cartao_id, cartao_nome, dia_fechamento, dia_vencimento = cartao
                
                # 3. Identificar faturas vencidas
                # Começar de 12 meses atrás até o mês atual
                data_inicio = hoje - relativedelta(months=12)
                mes_atual = date(hoje.year, hoje.month, 1)
                
                mes_iteracao = date(data_inicio.year, data_inicio.month, 1)
                
                while mes_iteracao <= mes_atual:
                    mes_fatura = mes_iteracao.strftime('%Y-%m')
                    
                    # 4. Calcular data de vencimento da fatura
                    try:
                        data_vencimento_str = calcular_data_vencimento(mes_fatura, dia_vencimento)
                        data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date()
                    except Exception as e:
                        logger.error(f"Erro ao calcular data de vencimento para cartao_id={cartao_id}, mes={mes_fatura}: {e}")
                        mes_iteracao += relativedelta(months=1)
                        continue
                    
                    # 5. Verificar se fatura está vencida
                    if data_vencimento > hoje:
                        mes_iteracao += relativedelta(months=1)
                        continue
                    
                    # 6. Verificar se já existe despesa para essa fatura
                    if verificar_despesa_fatura_existe(cartao_id, mes_fatura):
                        logger.debug(f"Despesa de fatura já existe para cartao_id={cartao_id}, mes={mes_fatura}")
                        mes_iteracao += relativedelta(months=1)
                        continue
                    
                    # 7. Calcular valor total da fatura
                    valor_fatura = calcular_valor_fatura(cartao_id, mes_fatura)
                    
                    # Se fatura está vazia, não criar despesa
                    if valor_fatura <= 0:
                        logger.debug(f"Fatura vazia para cartao_id={cartao_id}, mes={mes_fatura}")
                        mes_iteracao += relativedelta(months=1)
                        continue
                    
                    # 8. Criar despesa
                    # Formato da descrição: "Fatura Nubank - 01/2024"
                    mes_ano = datetime.strptime(mes_fatura, '%Y-%m').strftime('%m/%Y')
                    descricao = f"Fatura {cartao_nome} - {mes_ano}"
                    
                    cur.execute("""
                        INSERT INTO despesas
                        (descricao, valor, data, categoria_id, banco_id,
                         cartao_id, mes_fatura, pago)
                        VALUES (?, ?, ?, ?, NULL, ?, ?, 0)
                    """, (descricao, valor_fatura, data_vencimento_str,
                          categoria_id, cartao_id, mes_fatura))
                    
                    despesas_criadas += 1
                    logger.debug(f"Despesa de fatura criada: {descricao}, valor={valor_fatura}")
                    
                    # Avançar para próximo mês
                    mes_iteracao += relativedelta(months=1)
            
            # Commit automático pelo context manager
        
        if despesas_criadas > 0:
            logger.info(f"Geradas {despesas_criadas} despesas de faturas vencidas")
        
        return despesas_criadas
        
    except Exception as e:
        logger.error(f"Erro ao gerar despesas de faturas vencidas: {e}", exc_info=True)
        return 0



# ==============================
# 📅 VALIDAÇÃO DE DATAS
# ==============================

def validar_datas_despesa(data_lancamento, data_vencimento=None, data_pagamento=None):
    """
    Valida as datas de uma despesa.
    
    Args:
        data_lancamento: Data de lançamento (YYYY-MM-DD)
        data_vencimento: Data de vencimento opcional (YYYY-MM-DD)
        data_pagamento: Data de pagamento opcional (YYYY-MM-DD)
    
    Raises:
        ValueError: Se alguma data for inválida
    
    Requirements: 3.4, 3.5, 11.1, 11.2, 11.7
    """
    # Validar formato de data_lancamento
    try:
        dt_lancamento = datetime.strptime(data_lancamento, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Data de lançamento inválida: {data_lancamento}. Use o formato YYYY-MM-DD")
    
    # Validar data_vencimento
    if data_vencimento and data_vencimento != '':
        try:
            dt_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d')
            if dt_vencimento.date() < dt_lancamento.date():
                raise ValueError(
                    "Data de vencimento não pode ser anterior à data de lançamento"
                )
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError(f"Data de vencimento inválida: {data_vencimento}. Use o formato YYYY-MM-DD")
            raise
    
    # Validar data_pagamento
    if data_pagamento and data_pagamento != '':
        try:
            dt_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d')
            if dt_pagamento.date() < dt_lancamento.date():
                raise ValueError(
                    "Data de pagamento não pode ser anterior à data de lançamento"
                )
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError(f"Data de pagamento inválida: {data_pagamento}. Use o formato YYYY-MM-DD")
            raise


def converter_data_br_para_iso(data_br):
    """
    Converte data do formato brasileiro (DD/MM/YYYY) para ISO (YYYY-MM-DD).
    
    Args:
        data_br: Data em formato DD/MM/YYYY ou None/string vazia
    
    Returns:
        Data em formato YYYY-MM-DD ou string vazia se data_br for None/vazia
    
    Raises:
        ValueError: Se data for inválida
    
    Requirements: 11.5, 11.6, 5.5
    """
    # Tratar valores NULL retornando string vazia
    if not data_br or data_br == '':
        return ''
    
    try:
        dt = datetime.strptime(data_br, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Data inválida: {data_br}. Use o formato DD/MM/YYYY")


def converter_data_iso_para_br(data_iso):
    """
    Converte data do formato ISO (YYYY-MM-DD) para brasileiro (DD/MM/YYYY).
    
    Args:
        data_iso: Data em formato YYYY-MM-DD ou None/string vazia
    
    Returns:
        Data em formato DD/MM/YYYY ou string vazia se data_iso for None/vazia
    
    Raises:
        ValueError: Se data for inválida
    
    Requirements: 11.5, 11.6, 5.5
    """
    # Tratar valores NULL retornando string vazia
    if not data_iso or data_iso == '':
        return ''
    
    try:
        dt = datetime.strptime(data_iso, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except ValueError:
        raise ValueError(f"Data inválida: {data_iso}. Use o formato YYYY-MM-DD")


# ==============================
# 💰 FUNÇÕES DE DESPESAS
# ==============================

def criar_despesa_com_datas(descricao, valor, data, categoria_id, banco_id,
                           data_vencimento=None, data_pagamento=None):
    """
    Cria uma nova despesa com campos de vencimento e pagamento.
    
    Args:
        descricao: Descrição da despesa
        valor: Valor da despesa
        data: Data de lançamento (YYYY-MM-DD)
        categoria_id: ID da categoria
        banco_id: ID do banco
        data_vencimento: Data de vencimento opcional (YYYY-MM-DD)
        data_pagamento: Data de pagamento opcional (YYYY-MM-DD)
    
    Returns:
        ID da despesa criada
    
    Raises:
        ValueError: Se datas forem inválidas
    
    Requirements: 3.1, 3.2, 3.3, 3.6, 3.7
    """
    from utils.logger import logger
    
    # Validar datas
    validar_datas_despesa(data, data_vencimento, data_pagamento)
    
    # Determinar valor de pago baseado em data_pagamento
    pago = 1 if data_pagamento else 0
    
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO despesas 
            (descricao, valor, data, categoria_id, banco_id, 
             data_vencimento, data_pagamento, pago)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (descricao, float(valor), data, categoria_id, banco_id,
              data_vencimento, data_pagamento, pago))
        
        despesa_id = cur.lastrowid
    
    logger.info(f"Despesa {despesa_id} criada com vencimento={data_vencimento}, pagamento={data_pagamento}")
    return despesa_id


def atualizar_despesa_com_datas(despesa_id, descricao=None, valor=None, data=None,
                                categoria_id=None, banco_id=None,
                                data_vencimento=None, data_pagamento=None):
    """
    Atualiza uma despesa existente, incluindo campos de data.

    Args:
        despesa_id: ID da despesa a atualizar
        descricao: Nova descrição (opcional)
        valor: Novo valor (opcional)
        data: Nova data de lançamento (opcional)
        categoria_id: Novo ID de categoria (opcional)
        banco_id: Novo ID de banco (opcional)
        data_vencimento: Nova data de vencimento (opcional, use '' para remover)
        data_pagamento: Nova data de pagamento (opcional, use '' para remover)

    Returns:
        True se atualização bem-sucedida

    Raises:
        ValueError: Se datas forem inválidas

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """
    from utils.logger import logger

    db = get_db_manager()

    with db.get_connection() as conn:
        cur = conn.cursor()

        # Buscar dados atuais
        cur.execute("SELECT data FROM despesas WHERE id = ?", (despesa_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Despesa {despesa_id} não encontrada")

        data_lancamento = data if data else row[0]

        # Validar datas
        validar_datas_despesa(data_lancamento, data_vencimento, data_pagamento)

        # Construir UPDATE dinamicamente
        campos = []
        valores = []

        if descricao is not None:
            campos.append("descricao = ?")
            valores.append(descricao)
        if valor is not None:
            campos.append("valor = ?")
            valores.append(float(valor))
        if data is not None:
            campos.append("data = ?")
            valores.append(data)
        if categoria_id is not None:
            campos.append("categoria_id = ?")
            valores.append(categoria_id)
        if banco_id is not None:
            campos.append("banco_id = ?")
            valores.append(banco_id)

        # Tratar data_vencimento
        if data_vencimento is not None:
            campos.append("data_vencimento = ?")
            valores.append(data_vencimento if data_vencimento != '' else None)

        # Tratar data_pagamento e sincronizar pago
        if data_pagamento is not None:
            campos.append("data_pagamento = ?")
            campos.append("pago = ?")
            if data_pagamento == '':  # Remover data_pagamento
                valores.append(None)
                valores.append(0)
            else:  # Definir data_pagamento
                valores.append(data_pagamento)
                valores.append(1)

        if not campos:
            return True  # Nada para atualizar

        valores.append(despesa_id)
        sql = f"UPDATE despesas SET {', '.join(campos)} WHERE id = ?"
        cur.execute(sql, valores)

    logger.info(f"Despesa {despesa_id} atualizada")
    return True


def definir_data_pagamento(despesa_id, data_pagamento=None):
    """
    Define ou remove a data de pagamento de uma despesa.
    Sincroniza automaticamente o campo pago.
    
    Args:
        despesa_id: ID da despesa
        data_pagamento: Data de pagamento (YYYY-MM-DD) ou None para remover
    
    Returns:
        True se operação bem-sucedida
    
    Requirements: 2.1, 2.2
    """
    from utils.logger import logger
    
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        if data_pagamento:
            # Definir data_pagamento e marcar como pago
            cur.execute("""
                UPDATE despesas 
                SET data_pagamento = ?, pago = 1
                WHERE id = ?
            """, (data_pagamento, despesa_id))
        else:
            # Remover data_pagamento e desmarcar pago
            cur.execute("""
                UPDATE despesas 
                SET data_pagamento = NULL, pago = 0
                WHERE id = ?
            """, (despesa_id,))
        
        if cur.rowcount == 0:
            logger.warning(f"Despesa {despesa_id} não encontrada")
            return False
    
    logger.info(f"Data de pagamento da despesa {despesa_id} atualizada: {data_pagamento}")
    return True


def marcar_despesa_paga_com_data(despesa_id, pago=True, data_pagamento=None):
    """
    Marca uma despesa como paga ou não paga, com sincronização de data_pagamento.
    
    Args:
        despesa_id: ID da despesa
        pago: True para marcar como paga, False para desmarcar
        data_pagamento: Data de pagamento (YYYY-MM-DD), opcional
    
    Returns:
        True se operação bem-sucedida
    
    Requirements: 2.3, 2.4
    """
    from utils.logger import logger
    
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        if pago:
            # Marcar como pago
            if data_pagamento is None:
                # Manter data_pagamento como NULL se não fornecida
                cur.execute("""
                    UPDATE despesas 
                    SET pago = 1
                    WHERE id = ?
                """, (despesa_id,))
            else:
                # Definir data_pagamento fornecida
                cur.execute("""
                    UPDATE despesas 
                    SET pago = 1, data_pagamento = ?
                    WHERE id = ?
                """, (data_pagamento, despesa_id))
        else:
            # Desmarcar como pago e remover data_pagamento
            cur.execute("""
                UPDATE despesas 
                SET pago = 0, data_pagamento = NULL
                WHERE id = ?
            """, (despesa_id,))
        
        if cur.rowcount == 0:
            logger.warning(f"Despesa {despesa_id} não encontrada")
            return False
    
    logger.info(f"Despesa {despesa_id} marcada como {'paga' if pago else 'não paga'}")
    return True


def marcar_despesa_paga(despesa_id, pago=True):
    """
    Marca uma despesa como paga ou não paga.
    
    Args:
        despesa_id: ID da despesa
        pago: True para marcar como paga, False para desmarcar
        
    Emite:
        Sinal dados_atualizados após atualização
    """
    from utils.logger import logger
    
    db = get_db_manager()
    
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE despesas
                SET pago = ?
                WHERE id = ?
            """, (1 if pago else 0, despesa_id))
            
            if cur.rowcount == 0:
                logger.warning(f"Despesa com ID {despesa_id} não encontrada")
                return False
            
            # Commit automático pelo context manager
        
        logger.debug(f"Despesa {despesa_id} marcada como {'paga' if pago else 'não paga'}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao marcar despesa como paga: {e}", exc_info=True)
        return False


def listar_despesas_vencidas(incluir_pagas=False):
    """
    Lista despesas vencidas (data_vencimento < hoje e pago = 0).
    
    Args:
        incluir_pagas: Se True, inclui despesas pagas vencidas
    
    Returns:
        Lista de tuplas com dados das despesas vencidas:
        (id, descricao, valor, data, data_vencimento, data_pagamento, pago, 
         categoria, banco, dias_atraso)
    
    Requirements: 6.2, 6.5, 7.1, 7.6
    """
    from datetime import date
    from utils.logger import logger
    
    db = get_db_manager()
    hoje = date.today().strftime('%Y-%m-%d')
    
    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()
            
            if incluir_pagas:
                where_clause = "WHERE d.data_vencimento < ?"
                params = (hoje,)
            else:
                where_clause = "WHERE d.data_vencimento < ? AND d.pago = 0"
                params = (hoje,)
            
            cur.execute(f"""
                SELECT 
                    d.id, d.descricao, d.valor, d.data, d.data_vencimento,
                    d.data_pagamento, d.pago, c.nome as categoria, b.nome as banco,
                    julianday(?) - julianday(d.data_vencimento) as dias_atraso
                FROM despesas d
                LEFT JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN bancos b ON d.banco_id = b.id
                {where_clause}
                ORDER BY d.data_vencimento ASC
            """, (hoje,) + params)
            
            resultados = cur.fetchall()
            logger.debug(f"Listadas {len(resultados)} despesas vencidas (incluir_pagas={incluir_pagas})")
            return resultados
            
    except Exception as e:
        logger.error(f"Erro ao listar despesas vencidas: {e}", exc_info=True)
        return []


def listar_despesas_vencendo_em(dias):
    """
    Lista despesas que vencem nos próximos N dias.

    Args:
        dias: Número de dias à frente (ex: 7 para próximos 7 dias)

    Returns:
        Lista de tuplas com dados das despesas:
        (id, descricao, valor, data, data_vencimento, data_pagamento, pago,
         categoria, banco)

    Requirements: 7.2
    """
    from datetime import date, timedelta
    from utils.logger import logger

    db = get_db_manager()
    hoje = date.today()
    data_limite = (hoje + timedelta(days=dias)).strftime('%Y-%m-%d')
    hoje_str = hoje.strftime('%Y-%m-%d')

    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    d.id, d.descricao, d.valor, d.data, d.data_vencimento,
                    d.data_pagamento, d.pago, c.nome as categoria, b.nome as banco
                FROM despesas d
                LEFT JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN bancos b ON d.banco_id = b.id
                WHERE d.data_vencimento >= ?
                  AND d.data_vencimento <= ?
                  AND d.pago = 0
                ORDER BY d.data_vencimento ASC
            """, (hoje_str, data_limite))

            resultados = cur.fetchall()
            logger.debug(f"Listadas {len(resultados)} despesas vencendo em {dias} dias")
            return resultados

    except Exception as e:
        logger.error(f"Erro ao listar despesas vencendo em {dias} dias: {e}", exc_info=True)
        return []


def listar_despesas_por_periodo_pagamento(data_inicio, data_fim,
                                          categoria_id=None,
                                          banco_id=None):
    """
    Lista despesas pagas em um período específico.

    Args:
        data_inicio: Data inicial do período (YYYY-MM-DD)
        data_fim: Data final do período (YYYY-MM-DD)
        categoria_id: Filtro opcional por categoria
        banco_id: Filtro opcional por banco

    Returns:
        Lista de tuplas com dados das despesas pagas no período:
        (id, descricao, valor, data, data_vencimento, data_pagamento,
         categoria, banco)

    Requirements: 7.4, 8.1, 8.2, 7.5
    """
    from utils.logger import logger

    db = get_db_manager()

    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()

            where_clauses = ["d.data_pagamento >= ?", "d.data_pagamento <= ?"]
            params = [data_inicio, data_fim]

            if categoria_id:
                where_clauses.append("d.categoria_id = ?")
                params.append(categoria_id)

            if banco_id:
                where_clauses.append("d.banco_id = ?")
                params.append(banco_id)

            where_sql = " AND ".join(where_clauses)

            cur.execute(f"""
                SELECT
                    d.id, d.descricao, d.valor, d.data, d.data_vencimento,
                    d.data_pagamento, c.nome as categoria, b.nome as banco
                FROM despesas d
                LEFT JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN bancos b ON d.banco_id = b.id
                WHERE {where_sql}
                ORDER BY d.data_pagamento ASC
            """, params)

            resultados = cur.fetchall()
            logger.debug(f"Listadas {len(resultados)} despesas pagas entre {data_inicio} e {data_fim}")
            return resultados

    except Exception as e:
        logger.error(f"Erro ao listar despesas por período de pagamento: {e}", exc_info=True)
        return []




def filtrar_despesas_por_pagamento(status='todas', categoria_id=None, banco_id=None, 
                                   data_inicio=None, data_fim=None):
    """
    Filtra despesas por status de pagamento.
    
    Args:
        status: 'pagas', 'nao_pagas' ou 'todas'
        categoria_id: Filtro opcional por categoria
        banco_id: Filtro opcional por banco
        data_inicio: Filtro opcional por data inicial (YYYY-MM-DD)
        data_fim: Filtro opcional por data final (YYYY-MM-DD)
        
    Returns:
        Lista de despesas filtradas
    """
    from utils.logger import logger
    
    db = get_db_manager()
    
    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()
            
            # Construir query base
            query = """
                SELECT d.id, d.descricao, d.valor, d.data, d.categoria_id, d.banco_id,
                       d.parcela_numero, d.parcela_total, d.despesa_parcelada_id,
                       d.despesa_recorrente_id, d.cartao_id, d.mes_fatura, d.pago,
                       c.nome as categoria_nome, b.nome as banco_nome
                FROM despesas d
                LEFT JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN bancos b ON d.banco_id = b.id
                WHERE 1=1
            """
            
            params = []
            
            # Filtro de status de pagamento
            if status == 'pagas':
                query += " AND d.pago = 1"
            elif status == 'nao_pagas':
                query += " AND d.pago = 0"
            # 'todas' não adiciona filtro
            
            # Filtros opcionais
            if categoria_id is not None:
                query += " AND d.categoria_id = ?"
                params.append(categoria_id)
            
            if banco_id is not None:
                query += " AND d.banco_id = ?"
                params.append(banco_id)
            
            if data_inicio is not None:
                query += " AND d.data >= ?"
                params.append(data_inicio)
            
            if data_fim is not None:
                query += " AND d.data <= ?"
                params.append(data_fim)
            
            query += " ORDER BY d.data DESC, d.id DESC"
            
            cur.execute(query, params)
            
            despesas = []
            for row in cur.fetchall():
                despesas.append({
                    'id': row[0],
                    'descricao': row[1],
                    'valor': row[2],
                    'data': row[3],
                    'categoria_id': row[4],
                    'banco_id': row[5],
                    'parcela_numero': row[6],
                    'parcela_total': row[7],
                    'despesa_parcelada_id': row[8],
                    'despesa_recorrente_id': row[9],
                    'cartao_id': row[10],
                    'mes_fatura': row[11],
                    'pago': bool(row[12]),
                    'categoria_nome': row[13],
                    'banco_nome': row[14]
                })
            
            return despesas
        
    except Exception as e:
        logger.error(f"Erro ao filtrar despesas por pagamento: {e}", exc_info=True)
        return []


def sincronizar_pagamento_fatura(cartao_id, mes_fatura):
    """
    Quando uma fatura é paga, marca a despesa correspondente como paga.
    
    Args:
        cartao_id: ID do cartão
        mes_fatura: Mês da fatura (YYYY-MM)
        
    Lógica:
    - Busca despesa com cartao_id e mes_fatura correspondentes
    - Marca como paga (pago=1)
    - Emite sinal dados_atualizados
    """
    from utils.logger import logger
    
    db = get_db_manager()
    
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            
            # Buscar despesa correspondente
            cur.execute("""
                SELECT id FROM despesas
                WHERE cartao_id = ?
                AND mes_fatura = ?
            """, (cartao_id, mes_fatura))
            
            resultado = cur.fetchone()
            
            if not resultado:
                logger.warning(f"Despesa de fatura não encontrada para cartao_id={cartao_id}, mes={mes_fatura}")
                return False
            
            despesa_id = resultado[0]
            
            # Marcar como paga
            cur.execute("""
                UPDATE despesas
                SET pago = 1
                WHERE id = ?
            """, (despesa_id,))
            
            # Commit automático pelo context manager
        
        logger.info(f"Despesa de fatura marcada como paga: cartao_id={cartao_id}, mes={mes_fatura}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar pagamento de fatura: {e}", exc_info=True)
        return False


def obter_categorias():
    """
    Obtém todas as categorias ativas do sistema.
    
    Returns:
        list[dict]: Lista de categorias com id, nome e tipo
    """
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nome, tipo
            FROM categorias
            ORDER BY tipo, nome
        """)
        
        categorias = []
        for row in cur.fetchall():
            categorias.append({
                'id': row[0],
                'nome': row[1],
                'tipo': row[2]
            })
        
        return categorias


def criar_categoria(nome: str, tipo: str) -> int:
    """
    Cria uma nova categoria.
    
    Args:
        nome: Nome da categoria
        tipo: Tipo da categoria ('receita' ou 'despesa')
    
    Returns:
        int: ID da categoria criada
    """
    from datetime import datetime
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO categorias (nome, tipo, criado_em)
            VALUES (?, ?, ?)
        """, (nome, tipo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        return cur.lastrowid


# ============================================================================
# FUNÇÕES DE CÁLCULO PARA DASHBOARD
# ============================================================================

def calcular_total_despesas_vencidas():
    """
    Calcula quantidade e valor total de despesas vencidas.
    
    Returns:
        Tupla (quantidade, valor_total) de despesas vencidas
    
    Requirements: 9.1, 9.2
    """
    from datetime import date
    from utils.logger import logger
    
    db = get_db_manager()
    hoje = date.today().strftime('%Y-%m-%d')
    
    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT COUNT(*), COALESCE(SUM(valor), 0)
                FROM despesas
                WHERE data_vencimento < ? AND pago = 0
            """, (hoje,))
            
            resultado = cur.fetchone()
            quantidade = resultado[0] if resultado else 0
            valor_total = float(resultado[1]) if resultado else 0.0
            
            logger.debug(f"Despesas vencidas: {quantidade} despesas, total R$ {valor_total:.2f}")
            return (quantidade, valor_total)
            
    except Exception as e:
        logger.error(f"Erro ao calcular total de despesas vencidas: {e}", exc_info=True)
        return (0, 0.0)


def calcular_despesas_vencendo_periodo(dias):
    """
    Calcula quantidade e valor total de despesas vencendo em N dias.
    
    Args:
        dias: Número de dias para considerar (ex: 7, 30)
    
    Returns:
        Tupla (quantidade, valor_total) de despesas vencendo no período
    
    Requirements: 9.3, 9.4
    """
    from datetime import date, timedelta
    from utils.logger import logger
    
    db = get_db_manager()
    hoje = date.today()
    data_limite = (hoje + timedelta(days=dias)).strftime('%Y-%m-%d')
    hoje_str = hoje.strftime('%Y-%m-%d')
    
    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT COUNT(*), COALESCE(SUM(valor), 0)
                FROM despesas
                WHERE data_vencimento >= ? 
                  AND data_vencimento <= ? 
                  AND pago = 0
            """, (hoje_str, data_limite))
            
            resultado = cur.fetchone()
            quantidade = resultado[0] if resultado else 0
            valor_total = float(resultado[1]) if resultado else 0.0
            
            logger.debug(f"Despesas vencendo em {dias} dias: {quantidade} despesas, total R$ {valor_total:.2f}")
            return (quantidade, valor_total)
            
    except Exception as e:
        logger.error(f"Erro ao calcular despesas vencendo em {dias} dias: {e}", exc_info=True)
        return (0, 0.0)


def calcular_despesas_vencendo_mes_atual():
    """
    Calcula quantidade e valor total de despesas vencendo no mês atual.
    
    Returns:
        Tupla (quantidade, valor_total) de despesas vencendo no mês atual
    
    Requirements: 9.5, 9.6
    """
    from datetime import date
    from calendar import monthrange
    from utils.logger import logger
    
    db = get_db_manager()
    hoje = date.today()
    
    # Primeiro e último dia do mês atual
    primeiro_dia = date(hoje.year, hoje.month, 1).strftime('%Y-%m-%d')
    ultimo_dia_num = monthrange(hoje.year, hoje.month)[1]
    ultimo_dia = date(hoje.year, hoje.month, ultimo_dia_num).strftime('%Y-%m-%d')
    
    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT COUNT(*), COALESCE(SUM(valor), 0)
                FROM despesas
                WHERE data_vencimento >= ? 
                  AND data_vencimento <= ? 
                  AND pago = 0
            """, (primeiro_dia, ultimo_dia))
            
            resultado = cur.fetchone()
            quantidade = resultado[0] if resultado else 0
            valor_total = float(resultado[1]) if resultado else 0.0
            
            logger.debug(f"Despesas vencendo no mês atual: {quantidade} despesas, total R$ {valor_total:.2f}")
            return (quantidade, valor_total)
            
    except Exception as e:
        logger.error(f"Erro ao calcular despesas vencendo no mês atual: {e}", exc_info=True)
        return (0, 0.0)


# ============================================================================
# FUNÇÕES DE AGRUPAMENTO PARA RELATÓRIOS
# ============================================================================

def agrupar_despesas_pagas_por_categoria(data_inicio, data_fim):
    """
    Agrupa despesas pagas por categoria em um período.
    
    Args:
        data_inicio: Data inicial do período (YYYY-MM-DD)
        data_fim: Data final do período (YYYY-MM-DD)
    
    Returns:
        Lista de tuplas (nome_categoria, quantidade, total) ordenada por total DESC
    
    Requirements: 8.4
    """
    from utils.logger import logger
    
    db = get_db_manager()
    
    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    COALESCE(c.nome, 'Sem Categoria') as categoria,
                    COUNT(*) as quantidade,
                    SUM(d.valor) as total
                FROM despesas d
                LEFT JOIN categorias c ON d.categoria_id = c.id
                WHERE d.data_pagamento >= ? 
                  AND d.data_pagamento <= ?
                GROUP BY c.nome
                ORDER BY total DESC
            """, (data_inicio, data_fim))
            
            resultados = cur.fetchall()
            logger.debug(f"Agrupadas {len(resultados)} categorias entre {data_inicio} e {data_fim}")
            return resultados
            
    except Exception as e:
        logger.error(f"Erro ao agrupar despesas por categoria: {e}", exc_info=True)
        return []


def agrupar_despesas_pagas_por_banco(data_inicio, data_fim):
    """
    Agrupa despesas pagas por banco em um período.
    
    Args:
        data_inicio: Data inicial do período (YYYY-MM-DD)
        data_fim: Data final do período (YYYY-MM-DD)
    
    Returns:
        Lista de tuplas (nome_banco, quantidade, total) ordenada por total DESC
    
    Requirements: 8.5
    """
    from utils.logger import logger
    
    db = get_db_manager()
    
    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    COALESCE(b.nome, 'Sem Banco') as banco,
                    COUNT(*) as quantidade,
                    SUM(d.valor) as total
                FROM despesas d
                LEFT JOIN bancos b ON d.banco_id = b.id
                WHERE d.data_pagamento >= ? 
                  AND d.data_pagamento <= ?
                GROUP BY b.nome
                ORDER BY total DESC
            """, (data_inicio, data_fim))
            
            resultados = cur.fetchall()
            logger.debug(f"Agrupadas {len(resultados)} bancos entre {data_inicio} e {data_fim}")
            return resultados
            
    except Exception as e:
        logger.error(f"Erro ao agrupar despesas por banco: {e}", exc_info=True)
        return []


# ============================================================================
# FUNÇÕES DE PAGAMENTO EM LOTE DE PARCELAS
# ============================================================================

def marcar_parcelas_em_lote(despesa_parcelada_id, parcelas_ids, data_pagamento):
    """
    Marca múltiplas parcelas como pagas em lote.
    
    Args:
        despesa_parcelada_id: ID da despesa parcelada
        parcelas_ids: Lista de IDs das parcelas a marcar como pagas
        data_pagamento: Data do pagamento (YYYY-MM-DD)
    
    Requirements: 10.6
    """
    from utils.logger import logger
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Validar que todas as parcelas pertencem à despesa parcelada
        placeholders = ','.join('?' * len(parcelas_ids))
        cur.execute(f"""
            SELECT id FROM despesas
            WHERE id IN ({placeholders})
              AND despesa_parcelada_id = ?
        """, parcelas_ids + [despesa_parcelada_id])
        
        parcelas_validas = [row[0] for row in cur.fetchall()]
        
        if len(parcelas_validas) != len(parcelas_ids):
            invalidas = set(parcelas_ids) - set(parcelas_validas)
            raise ValueError(f"Parcelas inválidas ou não pertencem à despesa parcelada: {invalidas}")
        
        # Atualizar todas as parcelas
        cur.execute(f"""
            UPDATE despesas
            SET data_pagamento = ?, pago = 1
            WHERE id IN ({placeholders})
        """, [data_pagamento] + parcelas_ids)
        
        conn.commit()
        logger.info(f"Marcadas {len(parcelas_ids)} parcelas como pagas em lote")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao marcar parcelas em lote: {e}", exc_info=True)
        raise e
    finally:
        conn.close()


def atualizar_vencimento_parcelas_futuras(despesa_parcelada_id, nova_data_base):
    """
    Atualiza data_vencimento de parcelas futuras não pagas.
    
    Args:
        despesa_parcelada_id: ID da despesa parcelada
        nova_data_base: Nova data base para recalcular vencimentos (YYYY-MM-DD)
    
    Requirements: 10.7
    """
    from utils.logger import logger
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar parcelas não pagas
        cur.execute("""
            SELECT id, parcela_numero
            FROM despesas
            WHERE despesa_parcelada_id = ? AND pago = 0
            ORDER BY parcela_numero
        """, (despesa_parcelada_id,))
        
        parcelas_nao_pagas = cur.fetchall()
        
        if not parcelas_nao_pagas:
            logger.info("Nenhuma parcela não paga para atualizar")
            return
        
        # Converter nova_data_base
        if isinstance(nova_data_base, str):
            data_base = datetime.strptime(nova_data_base, '%Y-%m-%d').date()
        else:
            data_base = nova_data_base
        
        # Atualizar cada parcela
        for parcela_id, parcela_numero in parcelas_nao_pagas:
            # Calcular nova data de vencimento (incremento mensal a partir da data base)
            nova_data_vencimento = data_base + relativedelta(months=parcela_numero - 1)
            
            cur.execute("""
                UPDATE despesas
                SET data_vencimento = ?
                WHERE id = ?
            """, (nova_data_vencimento.strftime('%Y-%m-%d'), parcela_id))
        
        conn.commit()
        logger.info(f"Atualizadas {len(parcelas_nao_pagas)} parcelas futuras")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao atualizar vencimento de parcelas futuras: {e}", exc_info=True)
        raise e
    finally:
        conn.close()
