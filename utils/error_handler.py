"""
Sistema de códigos de erro e mensagens formatadas.

Este módulo fornece um sistema consistente para gerar mensagens de erro
amigáveis ao usuário com códigos únicos para facilitar suporte e debugging.
"""

from utils.logger import logger
from typing import Dict, Any, Optional


class ErrorCode:
    """Códigos de erro do sistema organizados por categoria."""
    
    # Erros de validação (1000-1999)
    VALIDATION_EMPTY_FIELD = 1001
    VALIDATION_INVALID_VALUE = 1002
    VALIDATION_CONSTRAINT_VIOLATION = 1003
    VALIDATION_INVALID_DATE = 1004
    VALIDATION_INVALID_AMOUNT = 1005
    VALIDATION_REQUIRED_FIELD = 1006
    
    # Erros de banco de dados (2000-2999)
    DB_CONNECTION_FAILED = 2001
    DB_FOREIGN_KEY_VIOLATION = 2002
    DB_UNIQUE_CONSTRAINT = 2003
    DB_NOT_FOUND = 2004
    DB_QUERY_ERROR = 2005
    DB_TRANSACTION_ERROR = 2006
    
    # Erros de operação (3000-3999)
    OP_INSUFFICIENT_BALANCE = 3001
    OP_LIMIT_EXCEEDED = 3002
    OP_INVALID_STATE = 3003
    OP_DUPLICATE_ENTRY = 3004
    OP_OPERATION_NOT_ALLOWED = 3005
    
    # Erros de arquivo (4000-4999)
    FILE_NOT_FOUND = 4001
    FILE_PERMISSION_DENIED = 4002
    FILE_READ_ERROR = 4003
    FILE_WRITE_ERROR = 4004
    
    # Erros de autenticação (5000-5999)
    AUTH_INVALID_CREDENTIALS = 5001
    AUTH_USER_NOT_FOUND = 5002
    AUTH_SESSION_EXPIRED = 5003
    AUTH_PERMISSION_DENIED = 5004


class ErrorMessage:
    """Gerador de mensagens de erro formatadas."""
    
    @staticmethod
    def format_error(code: int, what_failed: str, why_failed: str, how_to_fix: str) -> str:
        """
        Formata mensagem de erro no padrão consistente.
        
        Args:
            code: Código do erro (ErrorCode)
            what_failed: O que falhou (ex: "Não foi possível salvar a despesa")
            why_failed: Por que falhou (ex: "O campo descrição está vazio")
            how_to_fix: Como corrigir (ex: "Preencha a descrição e tente novamente")
            
        Returns:
            str: Mensagem formatada "Error [CODE]: [What]. [Why]. [How]"
            
        Exemplo:
            >>> ErrorMessage.format_error(
            ...     ErrorCode.VALIDATION_EMPTY_FIELD,
            ...     "Não foi possível salvar a despesa",
            ...     "O campo descrição está vazio",
            ...     "Preencha a descrição e tente novamente"
            ... )
            'Error [1001]: Não foi possível salvar a despesa. O campo descrição está vazio. Preencha a descrição e tente novamente'
        """
        msg = f"Error [{code}]: {what_failed}. {why_failed}. {how_to_fix}"
        
        # Limitar a 200 caracteres para mensagens de usuário
        if len(msg) > 200:
            msg = msg[:197] + "..."
        
        return msg
    
    @staticmethod
    def log_technical_details(code: int, exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loga detalhes técnicos completos para debugging.
        
        Args:
            code: Código do erro
            exception: Exceção original
            context: Contexto adicional (dict com informações relevantes)
            
        Exemplo:
            >>> try:
            ...     # operação que falha
            ...     pass
            ... except ValueError as e:
            ...     ErrorMessage.log_technical_details(
            ...         ErrorCode.VALIDATION_EMPTY_FIELD,
            ...         e,
            ...         {'campo': 'descricao', 'valor': ''}
            ...     )
        """
        context_info = context or {}
        
        logger.error(
            f"Error [{code}]: {str(exception)}",
            extra={'context': context_info},
            exc_info=True
        )
    
    @staticmethod
    def format_validation_error(field_name: str, value: Any, reason: str) -> str:
        """
        Formata erro de validação de campo.
        
        Args:
            field_name: Nome do campo
            value: Valor inválido
            reason: Razão da invalidação
            
        Returns:
            str: Mensagem formatada
        """
        return ErrorMessage.format_error(
            ErrorCode.VALIDATION_INVALID_VALUE,
            f"Valor inválido no campo '{field_name}'",
            reason,
            "Corrija o valor e tente novamente"
        )
    
    @staticmethod
    def format_db_foreign_key_error(entity_name: str, related_entity: str, count: int = 0) -> str:
        """
        Formata erro de violação de chave estrangeira.
        
        Args:
            entity_name: Nome da entidade sendo excluída
            related_entity: Nome da entidade relacionada
            count: Número de registros relacionados (opcional)
            
        Returns:
            str: Mensagem formatada
        """
        if count > 0:
            why = f"Existem {count} {related_entity}(s) associado(s)"
        else:
            why = f"Existem {related_entity}s associados"
        
        return ErrorMessage.format_error(
            ErrorCode.DB_FOREIGN_KEY_VIOLATION,
            f"Não foi possível excluir {entity_name}",
            why,
            f"Remova os {related_entity}s associados primeiro"
        )
    
    @staticmethod
    def format_not_found_error(entity_name: str, entity_id: Any) -> str:
        """
        Formata erro de registro não encontrado.
        
        Args:
            entity_name: Nome da entidade
            entity_id: ID do registro
            
        Returns:
            str: Mensagem formatada
        """
        return ErrorMessage.format_error(
            ErrorCode.DB_NOT_FOUND,
            f"{entity_name} não encontrado",
            f"O registro com ID {entity_id} não existe",
            "Verifique o ID e tente novamente"
        )
    
    @staticmethod
    def format_insufficient_balance_error(available: float, required: float) -> str:
        """
        Formata erro de saldo insuficiente.
        
        Args:
            available: Saldo disponível
            required: Valor necessário
            
        Returns:
            str: Mensagem formatada
        """
        return ErrorMessage.format_error(
            ErrorCode.OP_INSUFFICIENT_BALANCE,
            "Saldo insuficiente",
            f"Disponível: R$ {available:.2f}, Necessário: R$ {required:.2f}",
            "Adicione fundos ou reduza o valor"
        )
    
    @staticmethod
    def format_limit_exceeded_error(limit: float, attempted: float) -> str:
        """
        Formata erro de limite excedido.
        
        Args:
            limit: Limite máximo
            attempted: Valor tentado
            
        Returns:
            str: Mensagem formatada
        """
        return ErrorMessage.format_error(
            ErrorCode.OP_LIMIT_EXCEEDED,
            "Limite excedido",
            f"Limite: R$ {limit:.2f}, Tentado: R$ {attempted:.2f}",
            "Reduza o valor ou aumente o limite"
        )


# Funções auxiliares para uso comum

def handle_validation_error(field_name: str, value: Any, reason: str, exception: Exception) -> str:
    """
    Trata erro de validação completo (mensagem + log).
    
    Args:
        field_name: Nome do campo
        value: Valor inválido
        reason: Razão da invalidação
        exception: Exceção original
        
    Returns:
        str: Mensagem formatada para o usuário
    """
    msg = ErrorMessage.format_validation_error(field_name, value, reason)
    ErrorMessage.log_technical_details(
        ErrorCode.VALIDATION_INVALID_VALUE,
        exception,
        {'campo': field_name, 'valor': str(value), 'razao': reason}
    )
    return msg


def handle_db_error(operation: str, exception: Exception, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Trata erro de banco de dados genérico.
    
    Args:
        operation: Operação que falhou
        exception: Exceção original
        context: Contexto adicional
        
    Returns:
        str: Mensagem formatada para o usuário
    """
    msg = ErrorMessage.format_error(
        ErrorCode.DB_QUERY_ERROR,
        f"Erro ao {operation}",
        "Ocorreu um erro no banco de dados",
        "Tente novamente ou contate o suporte"
    )
    ErrorMessage.log_technical_details(
        ErrorCode.DB_QUERY_ERROR,
        exception,
        context
    )
    return msg
