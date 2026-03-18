"""
Módulo de migrações e gerenciamento de schema do banco de dados.
"""
import sqlite3
import os
from pathlib import Path
from utils.logger import logger

# ==============================
# 📂 IMPORTAR MÓDULO CENTRALIZADO
# ==============================
# CORREÇÃO: Bug de Perda de Dados em Banco de Produção
# Usar módulo centralizado db_config.py como única fonte de verdade
from database.db_config import (
    get_persistent_db_path,
    get_db_manager_instance,
    conectar as conectar_centralizado,
    _is_test_mode
)

# ==============================
# 🔧 FUNÇÕES DE COMPATIBILIDADE
# ==============================
# Expor _TEST_MODE para compatibilidade com código existente
_TEST_MODE = _is_test_mode()

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


def criar_backup_antes_migracao():
    """
    Cria backup do banco de dados antes de executar migração.
    
    Returns:
        str: Caminho do arquivo de backup criado
    
    Requirements: 12.1
    """
    from datetime import datetime
    import shutil
    
    db_path = get_db_path()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    shutil.copy2(db_path, backup_path)
    logger.info(f"Backup criado: {backup_path}")
    
    return backup_path


def migrar_controle_vencimento_pagamento(cur=None):
    """
    Migração: Adiciona campos de vencimento e pagamento nas despesas.
    
    - Adiciona data_vencimento (TEXT, NULL)
    - Adiciona data_pagamento (TEXT, NULL)
    - Cria índices para otimização
    - Preserva todos os dados existentes
    - Registra execução para evitar duplicação
    
    Args:
        cur: Cursor do banco de dados (opcional). Se não fornecido, cria nova conexão.
    
    Requirements: 1.1, 1.2, 1.3, 1.6, 1.7
    """
    from datetime import datetime
    
    # Se cursor não foi fornecido, criar nova conexão
    if cur is None:
        db = get_db_manager()
        with db.get_connection() as conn:
            cur = conn.cursor()
            _executar_migracao_vencimento_pagamento(cur)
    else:
        # Usar cursor fornecido
        _executar_migracao_vencimento_pagamento(cur)


def _executar_migracao_vencimento_pagamento(cur):
    """
    Executa a migração de vencimento e pagamento usando o cursor fornecido.
    
    Args:
        cur: Cursor do banco de dados
    """
    from datetime import datetime
    
    # Verificar se migração já foi executada
    cur.execute("""
        SELECT valor FROM configuracoes 
        WHERE chave = 'migracao_vencimento_pagamento'
    """)
    if cur.fetchone():
        logger.info("Migração de vencimento/pagamento já executada")
        return
    
    logger.info("Iniciando migração de vencimento/pagamento...")
    
    # Adicionar colunas se não existirem
    if not coluna_existe(cur, "despesas", "data_vencimento"):
        cur.execute("ALTER TABLE despesas ADD COLUMN data_vencimento TEXT")
        logger.info("Coluna data_vencimento adicionada")
    
    if not coluna_existe(cur, "despesas", "data_pagamento"):
        cur.execute("ALTER TABLE despesas ADD COLUMN data_pagamento TEXT")
        logger.info("Coluna data_pagamento adicionada")
    
    # Criar índices
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_despesas_data_vencimento 
        ON despesas(data_vencimento)
    """)
    logger.info("Índice idx_despesas_data_vencimento criado")
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_despesas_data_pagamento 
        ON despesas(data_pagamento)
    """)
    logger.info("Índice idx_despesas_data_pagamento criado")
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_despesas_vencimento_pago 
        ON despesas(data_vencimento, pago)
    """)
    logger.info("Índice idx_despesas_vencimento_pago criado")
    
    # Registrar migração
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute("""
        INSERT INTO configuracoes (chave, valor) 
        VALUES ('migracao_vencimento_pagamento', ?)
    """, (timestamp,))
    
    logger.info("Migração de vencimento/pagamento concluída com sucesso")


# ==============================
# 🏗️ CRIAÇÃO E MIGRAÇÃO SEGURA
# ==============================
def criar_tabelas():
    """Cria todas as tabelas do banco de dados e executa migrações."""
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
                parcela_atual INTEGER,
                total_parcelas INTEGER,
                compra_parcelada_id INTEGER,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (cartao_id) REFERENCES cartoes (id),
                FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                CHECK (valor > 0),
                CHECK (parcela_atual IS NULL OR parcela_atual > 0),
                CHECK (total_parcelas IS NULL OR total_parcelas >= 1)
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

        # Tabelas de Orçamento e Planejamento Financeiro
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orcamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ano INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'ativo',
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                CHECK (ano >= 2000 AND ano <= 2100),
                CHECK (status IN ('ativo', 'inativo'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS itens_orcamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                orcamento_id INTEGER NOT NULL,
                categoria_id INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                valor_planejado REAL NOT NULL,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
                CHECK (mes >= 1 AND mes <= 12),
                CHECK (valor_planejado >= 0),
                UNIQUE (orcamento_id, categoria_id, mes)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS historico_orcamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_orcamento_id INTEGER NOT NULL,
                data_alteracao TEXT NOT NULL,
                valor_anterior REAL NOT NULL,
                valor_novo REAL NOT NULL,
                usuario_id INTEGER,
                FOREIGN KEY (item_orcamento_id) REFERENCES itens_orcamento(id) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
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
            ("usuarios", "senha_hash_bcrypt", "TEXT"),
            # Fase 4: Integração de Despesas Automáticas
            ("despesas", "pago", "INTEGER DEFAULT 0 CHECK (pago IN (0, 1))"),
            ("despesas", "cartao_id", "INTEGER REFERENCES cartoes(id)"),
            ("despesas", "mes_fatura", "TEXT"),
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
            # Fase 4: Índices para despesas automáticas
            ("idx_despesas_parcelada_id", "despesas", "despesa_parcelada_id"),
            ("idx_despesas_recorrente_id", "despesas", "despesa_recorrente_id"),
            ("idx_despesas_pago", "despesas", "pago"),
            ("idx_despesas_cartao_id", "despesas", "cartao_id"),
            # Índices para Orçamento e Planejamento Financeiro
            ("idx_orcamentos_ano", "orcamentos", "ano"),
            ("idx_orcamentos_status", "orcamentos", "status"),
            ("idx_itens_orcamento_id", "itens_orcamento", "orcamento_id"),
            ("idx_itens_categoria_id", "itens_orcamento", "categoria_id"),
            ("idx_itens_mes", "itens_orcamento", "mes"),
            ("idx_historico_item", "historico_orcamento", "item_orcamento_id"),
            ("idx_historico_data", "historico_orcamento", "data_alteracao"),
        ]

        for nome_indice, tabela, coluna in indices:
            try:
                cur.execute(f"CREATE INDEX IF NOT EXISTS {nome_indice} ON {tabela}({coluna})")
            except sqlite3.OperationalError as e:
                logger.error(f"Erro ao criar índice {nome_indice}: {e}")
            except sqlite3.DatabaseError as e:
                logger.error(f"Erro de banco de dados ao criar índice {nome_indice}: {e}")
        
        # Fase 4: Índice composto para despesas de fatura
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_despesas_cartao_fatura ON despesas(cartao_id, mes_fatura)")
        except sqlite3.OperationalError as e:
            logger.error(f"Erro ao criar índice idx_despesas_cartao_fatura: {e}")
        except sqlite3.DatabaseError as e:
            logger.error(f"Erro de banco de dados ao criar índice idx_despesas_cartao_fatura: {e}")

        # Índice composto para itens de orçamento (otimiza consultas por orçamento + categoria + mês)
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_itens_composto ON itens_orcamento(orcamento_id, categoria_id, mes)")
        except sqlite3.OperationalError as e:
            logger.error(f"Erro ao criar índice idx_itens_composto: {e}")
        except sqlite3.DatabaseError as e:
            logger.error(f"Erro de banco de dados ao criar índice idx_itens_composto: {e}")

        # Migração: Controle de Vencimento e Pagamento de Despesas
        migrar_controle_vencimento_pagamento(cur)

        # Connection will be automatically committed and closed by context manager
    
    # Criar índices de performance para tabelas de transações
    try:
        from database.indexes import criar_indices_performance
        criar_indices_performance()
        logger.info("Índices de performance criados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar índices de performance: {e}")



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
            "despesas_parceladas", "despesas_recorrentes",
            "historico_orcamento", "itens_orcamento", "orcamentos"
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
