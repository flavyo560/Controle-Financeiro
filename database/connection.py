import sqlite3
from contextlib import contextmanager
from typing import Generator
import time
from pathlib import Path
from utils.logger import logger

class DatabaseManager:
    """
    Gerenciador de conexões thread-safe para SQLite.
    
    Remove a necessidade de check_same_thread=False através de
    context managers que garantem uma conexão por thread.
    """
    
    def __init__(self, db_path: str, timeout: int = 10, max_retries: int = 5):
        """
        Inicializa o gerenciador de banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco
            timeout: Timeout em segundos para operações
            max_retries: Número máximo de tentativas em caso de erro
        """
        self.db_path = db_path
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Garantir que o diretório existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self, readonly: bool = False) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager para conexões seguras.
        
        Garante que:
        - Conexão é sempre fechada
        - Transações são commitadas em sucesso
        - Rollback em caso de erro
        - Foreign keys estão habilitadas
        
        Args:
            readonly: Se True, abre em modo somente leitura
            
        Yields:
            Conexão SQLite configurada
            
        Example:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM despesas")
        """
        conn = None
        retries = 0
        last_error = None
        
        # Tentar conectar com retry
        while retries < self.max_retries:
            try:
                # Conectar sem check_same_thread (thread-safe via context manager)
                uri = f"file:{self.db_path}?mode=ro" if readonly else self.db_path
                conn = sqlite3.connect(
                    uri,
                    timeout=self.timeout,
                    isolation_level='DEFERRED',  # Transações explícitas
                    uri=readonly
                )
                
                # Configurações de segurança e performance
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA busy_timeout = 5000")
                conn.row_factory = sqlite3.Row  # Acesso por nome de coluna
                
                logger.info(f"Conexão estabelecida: {self.db_path}")
                break  # Conexão bem-sucedida, sair do loop
                
            except sqlite3.OperationalError as e:
                last_error = e
                retries += 1
                
                if retries < self.max_retries:
                    # Backoff exponencial: 0.1s, 0.2s, 0.4s, 0.8s, 1.6s
                    wait_time = 0.1 * (2 ** retries)
                    logger.warning(
                        f"Erro de conexão (tentativa {retries}/{self.max_retries}): {e}. "
                        f"Aguardando {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Falha após {self.max_retries} tentativas: {e}")
                    raise
        
        # Agora yield a conexão e trata exceções do código do usuário
        try:
            yield conn
            
            # Commit apenas se não for readonly
            if not readonly:
                conn.commit()
                logger.info("Transação commitada com sucesso")
                    
        except Exception as e:
            logger.error(f"Erro durante execução: {e}", exc_info=True)
            if conn:
                conn.rollback()
                logger.info("Rollback executado")
            raise
                
        finally:
            if conn:
                conn.close()
                logger.info("Conexão fechada")
    
    def execute_query(self, query: str, params: tuple = (), readonly: bool = False):
        """
        Executa query com gerenciamento automático de conexão.
        
        Args:
            query: Query SQL a executar
            params: Parâmetros da query
            readonly: Se True, usa conexão somente leitura
            
        Returns:
            Resultado da query
        """
        with self.get_connection(readonly=readonly) as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.fetchall()
    
    def execute_write(self, query: str, params: tuple = ()):
        """
        Executa operação de escrita com gerenciamento automático.
        
        Args:
            query: Query SQL a executar
            params: Parâmetros da query
            
        Returns:
            ID do último registro inserido
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.lastrowid
