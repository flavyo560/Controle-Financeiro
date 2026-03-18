"""
Módulo de operações relacionadas a usuários.
"""
import sqlite3
import hashlib
import bcrypt
from datetime import datetime
from database.connection import DatabaseManager
from database.migrations import get_db_manager
from utils.logger import logger, log_errors


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
    """Verifica se existe pelo menos um usuário cadastrado."""
    db = get_db_manager()
    try:
        with db.get_connection(readonly=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM usuarios")
            return cur.fetchone()[0] > 0
    except sqlite3.OperationalError as e:
        logger.error(f"Erro operacional ao verificar existência de usuário: {e}")
        return False
    except sqlite3.DatabaseError as e:
        logger.error(f"Erro de banco de dados ao verificar existência de usuário: {e}")
        return False


@log_errors()
def criar_usuario(nome, email, senha, perfil="admin"):
    """
    Cria um novo usuário no sistema.
    
    Args:
        nome: Nome do usuário
        email: Email do usuário
        senha: Senha em texto claro
        perfil: Perfil do usuário (padrão: "admin")
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        # Inserir com bcrypt (novo sistema) e um valor dummy para senha_hash (compatibilidade)
        cur.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, senha_hash_bcrypt, perfil, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, email, '', hash_senha_bcrypt(senha), perfil, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def validar_login(identificador, senha):
    """
    Valida login do usuário com suporte a migração automática de SHA-256 para bcrypt.
    
    Args:
        identificador: Email, nome ou CPF do usuário
        senha: Senha em texto claro
        
    Returns:
        Tupla (id, nome, email, cpf, telefone) se login válido, None caso contrário
    """
    db = get_db_manager()
    
    # Buscar usuário
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nome, email, cpf, telefone, senha_hash_bcrypt, senha_hash
            FROM usuarios
            WHERE email = ? OR nome = ? OR cpf = ?
        """, (identificador, identificador, identificador))
        
        row = cur.fetchone()
    
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
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE usuarios 
                    SET senha_hash_bcrypt = ?, senha_hash = ''
                    WHERE id = ?
                """, (hash_senha_bcrypt(senha), user_id))
            logger.info(f"Senha do usuário {user_id} migrada para bcrypt")
        except Exception as e:
            logger.error(f"Erro ao migrar senha: {e}")
        
        return (user_id, nome, email, cpf, telefone)
    
    return None
