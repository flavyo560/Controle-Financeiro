import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from pathlib import Path
import re
import os
from typing import Any, Callable

# Criar diretório de logs no AppData do usuário (não em Program Files)
if os.name == 'nt':  # Windows
    LOG_DIR = Path(os.getenv('LOCALAPPDATA')) / 'ControleFinanceiro' / 'logs'
else:  # Linux/Mac
    LOG_DIR = Path.home() / '.controle_financeiro' / 'logs'

LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str = 'finance_app') -> logging.Logger:
    """
    Configura logger com rotação de arquivos.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        LOG_DIR / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Handler para console (apenas erros)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    
    # Formato detalhado
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def sanitize_log_data(data: Any) -> Any:
    """
    Remove dados sensíveis de logs.
    
    Args:
        data: Dados a sanitizar
        
    Returns:
        Dados sanitizados
    """
    if isinstance(data, dict):
        sanitized = {}
        sensitive_keys = {'senha', 'password', 'token', 'secret', 'senha_hash', 'senha_hash_bcrypt'}
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = '***REDACTED***'
            else:
                sanitized[key] = sanitize_log_data(value)
        return sanitized
    elif isinstance(data, (list, tuple)):
        return [sanitize_log_data(item) for item in data]
    elif isinstance(data, str):
        # Remover possíveis senhas em strings
        return re.sub(r'senha[=:]\s*\S+', 'senha=***REDACTED***', data, flags=re.IGNORECASE)
    return data

def log_errors(logger: logging.Logger = None):
    """
    Decorador para logging automático de erros.
    
    Args:
        logger: Logger a usar (opcional)
    """
    if logger is None:
        logger = setup_logger()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logger.info(f"Função {func.__name__} executada com sucesso")
                return result
            except Exception as e:
                # Sanitizar argumentos antes de logar
                safe_args = sanitize_log_data(args)
                safe_kwargs = sanitize_log_data(kwargs)
                
                logger.error(
                    f"Erro em {func.__name__}: {type(e).__name__}: {str(e)} - "
                    f"Args: {safe_args}, Kwargs: {safe_kwargs}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator

# Logger global
logger = setup_logger()
