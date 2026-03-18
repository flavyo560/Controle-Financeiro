"""
Módulo de gerenciamento de índices de banco de dados.

Este módulo é responsável por criar e gerenciar índices em colunas
frequentemente consultadas para otimizar a performance de queries.
"""

import sqlite3
from utils.logger import logger
from database.db import get_db_manager


def verificar_indice_existe(cursor, tabela: str, coluna: str) -> bool:
    """
    Verifica se um índice já existe em uma coluna.
    
    Args:
        cursor: Cursor do banco de dados
        tabela: Nome da tabela
        coluna: Nome da coluna
        
    Returns:
        bool: True se índice existe, False caso contrário
    """
    try:
        # Buscar todos os índices da tabela
        cursor.execute(f"PRAGMA index_list({tabela})")
        indices = cursor.fetchall()
        
        # Para cada índice, verificar se ele indexa a coluna especificada
        for indice in indices:
            nome_indice = indice[1]  # index_list retorna (seq, name, unique, origin, partial)
            
            # Buscar informações sobre as colunas do índice
            cursor.execute(f"PRAGMA index_info({nome_indice})")
            colunas_indice = cursor.fetchall()
            
            # Verificar se a coluna está neste índice
            for col_info in colunas_indice:
                nome_coluna = col_info[2]  # index_info retorna (seqno, cid, name)
                if nome_coluna == coluna:
                    return True
        
        return False
        
    except sqlite3.Error as e:
        logger.error(f"Erro ao verificar índice em {tabela}.{coluna}: {e}")
        return False


def criar_indices_performance():
    """
    Cria índices para otimizar queries comuns.
    
    Índices criados:
    - despesas(data), despesas(categoria_id), despesas(banco_id)
    - receitas(data), receitas(categoria_id), receitas(banco_id)
    - investimentos(data)
    - abastecimentos(data), abastecimentos(veiculo_id)
    - manutencoes(data), manutencoes(veiculo_id)
    - transferencias(data)
    
    Comportamento:
    - Verifica existência antes de criar (idempotente)
    - Executa dentro de transação
    - Loga erros sem interromper aplicação
    """
    db = get_db_manager()
    
    # Definir índices a serem criados: (tabela, coluna, nome_indice)
    indices = [
        # Tabela despesas
        ('despesas', 'data', 'idx_despesas_data'),
        ('despesas', 'categoria_id', 'idx_despesas_categoria'),
        ('despesas', 'banco_id', 'idx_despesas_banco'),
        
        # Tabela receitas
        ('receitas', 'data', 'idx_receitas_data'),
        ('receitas', 'categoria_id', 'idx_receitas_categoria'),
        ('receitas', 'banco_id', 'idx_receitas_banco'),
        
        # Tabela investimentos
        ('investimentos', 'data', 'idx_investimentos_data'),
        
        # Tabela abastecimentos
        ('abastecimentos', 'data', 'idx_abastecimentos_data'),
        ('abastecimentos', 'veiculo_id', 'idx_abastecimentos_veiculo'),
        
        # Tabela manutencoes
        ('manutencoes', 'data', 'idx_manutencoes_data'),
        ('manutencoes', 'veiculo_id', 'idx_manutencoes_veiculo'),
        
        # Tabela transferencias
        ('transferencias', 'data', 'idx_transferencias_data'),
    ]
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            indices_criados = 0
            indices_existentes = 0
            
            for tabela, coluna, nome_indice in indices:
                try:
                    # Verificar se índice já existe
                    if verificar_indice_existe(cursor, tabela, coluna):
                        logger.info(f"Índice já existe: {tabela}.{coluna}")
                        indices_existentes += 1
                        continue
                    
                    # Criar índice
                    query = f"CREATE INDEX IF NOT EXISTS {nome_indice} ON {tabela}({coluna})"
                    cursor.execute(query)
                    logger.info(f"Índice criado com sucesso: {nome_indice} em {tabela}.{coluna}")
                    indices_criados += 1
                    
                except sqlite3.Error as e:
                    # Logar erro mas continuar com próximos índices
                    logger.error(f"Erro ao criar índice em {tabela}.{coluna}: {e}")
            
            # Log final
            logger.info(
                f"Criação de índices concluída: "
                f"{indices_criados} criados, {indices_existentes} já existiam"
            )
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao criar índices de performance: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao criar índices: {e}", exc_info=True)
