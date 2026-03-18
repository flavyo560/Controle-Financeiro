"""Validadores para prevenir SQL injection."""

# Whitelist de nomes de tabelas válidos
VALID_TABLES = {
    'usuarios', 'bancos', 'categorias', 'receitas', 'despesas',
    'investimentos', 'dividendos', 'transferencias', 'veiculos',
    'abastecimentos', 'manutencoes', 'configuracoes',
    'despesas_parceladas', 'despesas_recorrentes',
    'cartoes', 'compras_cartao', 'pagamentos_fatura',
    'orcamentos', 'itens_orcamento', 'historico_orcamento'
}

# Whitelist de colunas comuns
VALID_COLUMNS = {
    'id', 'nome', 'email', 'senha_hash', 'senha_hash_bcrypt', 'cpf', 'telefone',
    'descricao', 'valor', 'data', 'categoria_id', 'banco_id',
    'ativo', 'status', 'criado_em', 'tipo', 'saldo_inicial',
    'perfil', 'placa', 'modelo', 'nome_identificador',
    'valor_investido', 'valor_atual', 'valor_total', 'valor_pago',
    'numero_parcelas', 'data_primeira_parcela', 'data_inicio', 'data_fim',
    'dia_mes', 'ativa', 'parcela_numero', 'parcela_total',
    'despesa_parcelada_id', 'despesa_recorrente_id',
    'limite_total', 'dia_fechamento', 'dia_vencimento', 'bandeira',
    'cartao_id', 'data_compra', 'mes_fatura', 'compra_parcelada_id',
    'data_pagamento', 'despesa_id', 'banco_origem_id', 'banco_destino_id',
    'investimento_id', 'veiculo_id', 'litros', 'km_atual', 'km',
    'posto', 'servico', 'chave', 'valor', 'litros_gasolina', 'litros_etanol',
    'pago', 'ano', 'mes', 'valor_planejado', 'atualizado_em',
    'orcamento_id', 'item_orcamento_id', 'data_alteracao', 'valor_anterior',
    'valor_novo', 'usuario_id', 'parcela_atual', 'total_parcelas'
}

def validate_table_name(table_name: str) -> str:
    """
    Valida nome de tabela contra whitelist.
    
    Args:
        table_name: Nome da tabela a validar
        
    Returns:
        Nome da tabela validado
        
    Raises:
        ValueError: Se nome de tabela inválido
    """
    if not table_name:
        raise ValueError("Nome de tabela não pode ser vazio")
    
    if table_name not in VALID_TABLES:
        raise ValueError(f"Nome de tabela inválido: {table_name}")
    
    return table_name

def validate_column_name(column_name: str) -> str:
    """
    Valida nome de coluna contra whitelist.
    
    Args:
        column_name: Nome da coluna a validar
        
    Returns:
        Nome da coluna validado
        
    Raises:
        ValueError: Se nome de coluna inválido
    """
    if not column_name:
        raise ValueError("Nome de coluna não pode ser vazio")
    
    if column_name not in VALID_COLUMNS:
        raise ValueError(f"Nome de coluna inválido: {column_name}")
    
    return column_name

def validate_identifier(identifier: str) -> str:
    """
    Valida identificador SQL (apenas alfanumérico e underscore).
    Usado como fallback quando whitelist não é aplicável.
    
    Args:
        identifier: Identificador a validar
        
    Returns:
        Identificador validado
        
    Raises:
        ValueError: Se identificador inválido
    """
    if not identifier:
        raise ValueError("Identificador não pode ser vazio")
    
    # Permitir apenas letras, números e underscore
    if not identifier.replace('_', '').isalnum():
        raise ValueError(f"Identificador inválido: {identifier}")
    
    # Não permitir que comece com número
    if identifier[0].isdigit():
        raise ValueError(f"Identificador não pode começar com número: {identifier}")
    
    return identifier
