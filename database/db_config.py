"""
Módulo Centralizado de Configuração do Banco de Dados

Este módulo é a ÚNICA fonte de verdade para o caminho do banco de dados.
Implementa persistência de caminho através de arquivo de configuração JSON,
garantindo que o sistema sempre use o mesmo banco entre execuções.

Correção para: Bug de Perda de Dados em Banco de Produção
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from utils.logger import logger
from database.connection import DatabaseManager


# ==============================
# 📂 CONSTANTES
# ==============================
CONFIG_FILE_NAME = ".db_config.json"
PROD_DB_NAME = "financas.db"
TEST_DB_NAME = "test_financas.db"


# ==============================
# 🔍 DETECÇÃO DE MODO DE TESTE
# ==============================
def _is_test_mode() -> bool:
    """
    Detecta se o sistema está em modo de teste.
    
    Returns:
        True se em modo de teste, False caso contrário
    """
    return (
        os.getenv("PYTEST_CURRENT_TEST") is not None or 
        os.getenv("TEST_MODE") == "1"
    )


# ==============================
# 📁 GERENCIAMENTO DE CONFIGURAÇÃO
# ==============================
def _get_config_file_path() -> Path:
    """
    Retorna o caminho do arquivo de configuração.
    
    Returns:
        Path para o arquivo .db_config.json
    """
    if _is_test_mode():
        # Em modo de teste, config fica em test_data/
        return Path.cwd() / "test_data" / CONFIG_FILE_NAME
    else:
        # Em produção, config fica em LOCALAPPDATA
        try:
            localappdata = Path(os.getenv("LOCALAPPDATA", ""))
            if localappdata.exists():
                config_dir = localappdata / "ControleFinanceiro"
                config_dir.mkdir(parents=True, exist_ok=True)
                return config_dir / CONFIG_FILE_NAME
        except Exception as e:
            logger.warning(f"Erro ao acessar LOCALAPPDATA: {e}")
        
        # Fallback: home directory
        home_dir = Path.home() / "ControleFinanceiro"
        home_dir.mkdir(parents=True, exist_ok=True)
        return home_dir / CONFIG_FILE_NAME


def load_db_path_config() -> Optional[str]:
    """
    Carrega o caminho do banco do arquivo de configuração.
    
    Returns:
        Caminho do banco se encontrado e válido, None caso contrário
    """
    config_file = _get_config_file_path()
    
    if not config_file.exists():
        logger.info(f"Arquivo de configuração não encontrado: {config_file}")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        db_path = config.get("db_path")
        if not db_path:
            logger.warning("Arquivo de configuração não contém 'db_path'")
            return None
        
        # Validar que o arquivo existe
        if not Path(db_path).exists():
            logger.warning(f"Banco configurado não existe: {db_path}")
            return None
        
        # Validar que o arquivo tem dados (não está vazio)
        if Path(db_path).stat().st_size == 0:
            logger.warning(f"Banco configurado está vazio: {db_path}")
            return None
        
        logger.info(f"✓ Caminho do banco carregado da configuração: {db_path}")
        return db_path
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON do arquivo de configuração: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar configuração: {e}")
        return None


def save_db_path_config(db_path: str) -> None:
    """
    Salva o caminho do banco no arquivo de configuração.
    
    Args:
        db_path: Caminho completo do banco de dados
    """
    config_file = _get_config_file_path()
    
    # Criar backup do arquivo anterior se existir
    if config_file.exists():
        backup_file = config_file.with_suffix('.json.bak')
        try:
            import shutil
            shutil.copy2(config_file, backup_file)
            logger.info(f"Backup da configuração criado: {backup_file}")
        except Exception as e:
            logger.warning(f"Erro ao criar backup da configuração: {e}")
    
    # Criar nova configuração
    config = {
        "db_path": str(db_path),
        "created_at": datetime.now().isoformat(),
        "last_accessed": datetime.now().isoformat(),
        "test_mode": _is_test_mode()
    }
    
    try:
        # Garantir que o diretório existe
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar configuração
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Configuração salva: {config_file}")
        logger.info(f"  Banco: {db_path}")
        
    except Exception as e:
        logger.error(f"Erro ao salvar configuração: {e}")


def update_last_accessed() -> None:
    """
    Atualiza o timestamp de último acesso no arquivo de configuração.
    """
    config_file = _get_config_file_path()
    
    if not config_file.exists():
        return
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config["last_accessed"] = datetime.now().isoformat()
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        logger.warning(f"Erro ao atualizar last_accessed: {e}")


# ==============================
# 🔎 BUSCA DE BANCO EXISTENTE
# ==============================
def find_existing_database() -> Optional[str]:
    """
    Procura por banco de dados existente em locais conhecidos.
    
    Ordem de busca:
    1. LOCALAPPDATA/ControleFinanceiro/financas.db
    2. home/ControleFinanceiro/financas.db
    3. diretório atual/financas.db
    
    Returns:
        Caminho do primeiro banco encontrado com dados, None se nenhum encontrado
    """
    db_name = TEST_DB_NAME if _is_test_mode() else PROD_DB_NAME
    
    search_locations = []
    
    if _is_test_mode():
        # Em modo de teste, procurar apenas em test_data/
        search_locations.append(Path.cwd() / "test_data" / db_name)
    else:
        # Em produção, procurar em múltiplos locais
        # 1. LOCALAPPDATA
        try:
            localappdata = Path(os.getenv("LOCALAPPDATA", ""))
            if localappdata.exists():
                search_locations.append(localappdata / "ControleFinanceiro" / db_name)
        except Exception:
            pass
        
        # 2. Home directory
        search_locations.append(Path.home() / "ControleFinanceiro" / db_name)
        
        # 3. Diretório atual
        search_locations.append(Path.cwd() / db_name)
    
    logger.info(f"Procurando banco existente em {len(search_locations)} locais...")
    
    found_databases = []
    
    for location in search_locations:
        if location.exists():
            size = location.stat().st_size
            if size > 0:
                logger.info(f"  ✓ Encontrado: {location} ({size} bytes)")
                found_databases.append((str(location.absolute()), size))
            else:
                logger.info(f"  ⚠ Encontrado mas vazio: {location}")
        else:
            logger.debug(f"  ✗ Não encontrado: {location}")
    
    if len(found_databases) == 0:
        logger.info("Nenhum banco existente encontrado")
        return None
    
    if len(found_databases) > 1:
        logger.warning(f"⚠ ATENÇÃO: Múltiplos bancos encontrados ({len(found_databases)})!")
        for db_path, size in found_databases:
            logger.warning(f"  - {db_path} ({size} bytes)")
        logger.warning("Usando o primeiro encontrado. Considere consolidar os bancos.")
    
    # Retornar o primeiro banco encontrado
    return found_databases[0][0]


# ==============================
# 🎯 FUNÇÃO PRINCIPAL
# ==============================
def get_persistent_db_path() -> str:
    """
    Retorna o caminho persistente do banco de dados.
    
    Esta é a ÚNICA função que deve ser usada para obter o caminho do banco.
    
    Lógica:
    1. Verifica modo de teste
    2. Tenta carregar caminho do arquivo de configuração
    3. Se não encontrar, busca banco existente em locais conhecidos
    4. Se não encontrar, cria novo banco no local padrão
    5. Salva o caminho no arquivo de configuração
    6. Retorna o caminho validado
    
    Returns:
        Caminho completo e absoluto do banco de dados
    """
    # 1. Verificar modo de teste
    test_mode = _is_test_mode()
    
    if test_mode:
        logger.info("⚠️  MODO DE TESTE ATIVO")
    
    # 2. Tentar carregar caminho da configuração
    configured_path = load_db_path_config()
    if configured_path:
        # Atualizar timestamp de acesso
        update_last_accessed()
        return configured_path
    
    # 3. Buscar banco existente
    logger.info("Configuração não encontrada. Buscando banco existente...")
    existing_db = find_existing_database()
    
    if existing_db:
        logger.info(f"✓ Banco existente encontrado: {existing_db}")
        # Salvar na configuração para próximas execuções
        save_db_path_config(existing_db)
        return existing_db
    
    # 4. Criar novo banco no local padrão
    logger.info("Nenhum banco encontrado. Criando novo banco...")
    
    if test_mode:
        # Modo de teste: test_data/test_financas.db
        db_dir = Path.cwd() / "test_data"
        db_path = db_dir / TEST_DB_NAME
        logger.info(f"⚠️  MODO DE TESTE - Usando: {db_path}")
    else:
        # Modo de produção: LOCALAPPDATA/ControleFinanceiro/financas.db
        try:
            localappdata = Path(os.getenv("LOCALAPPDATA", ""))
            if localappdata.exists():
                db_dir = localappdata / "ControleFinanceiro"
            else:
                raise Exception("LOCALAPPDATA não encontrado")
        except Exception as e:
            logger.warning(f"Erro ao acessar LOCALAPPDATA: {e}. Usando fallback.")
            # Fallback: home directory
            db_dir = Path.home() / "ControleFinanceiro"
        
        db_path = db_dir / PROD_DB_NAME
        logger.info(f"✓ Novo banco será criado em: {db_path}")
    
    # Criar diretório se não existir
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Salvar na configuração
    save_db_path_config(str(db_path.absolute()))
    
    return str(db_path.absolute())


# ==============================
# 🔧 GERENCIADOR DE BANCO
# ==============================
# Instância global do DatabaseManager
_db_manager: Optional[DatabaseManager] = None
_db_manager_path: Optional[str] = None


def get_db_manager_instance() -> DatabaseManager:
    """
    Retorna a instância global do DatabaseManager.
    
    Thread-safe e gerencia conexões automaticamente.
    Recria a instância se o caminho do banco mudou.
    
    Returns:
        Instância do DatabaseManager configurada
    """
    global _db_manager, _db_manager_path
    
    current_path = get_persistent_db_path()
    
    # Recriar se o caminho mudou (importante para testes)
    if _db_manager is None or _db_manager_path != current_path:
        logger.info(f"Criando DatabaseManager para: {current_path}")
        _db_manager = DatabaseManager(current_path, timeout=10, max_retries=5)
        _db_manager_path = current_path
    
    return _db_manager


# ==============================
# 🔄 COMPATIBILIDADE
# ==============================
def conectar() -> sqlite3.Connection:
    """
    DEPRECATED: Retorna uma conexão raw para compatibilidade.
    
    Para código novo, use get_db_manager_instance().get_connection() instead.
    
    WARNING: Caller é responsável por fechar a conexão!
    
    Returns:
        Conexão SQLite configurada
    """
    path = get_persistent_db_path()
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
    except Exception as e:
        logger.error(f"Erro ao configurar conexão: {e}")
    return conn
