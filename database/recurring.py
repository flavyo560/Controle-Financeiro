"""
Módulo de operações relacionadas a despesas parceladas e recorrentes.
"""
import sqlite3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from database.connection import DatabaseManager
from database.migrations import get_db_manager
from utils.logger import logger, log_errors


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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
        _gerar_parcelas_interno(cur, despesa_parcelada_id, descricao, valor_total,
                      numero_parcelas, data_primeira_parcela, categoria_id, banco_id)

        return despesa_parcelada_id


def _gerar_parcelas_interno(cur, despesa_parcelada_id, descricao, valor_total,
                           numero_parcelas, data_primeira_parcela, categoria_id, banco_id):
    """
    Função interna para gerar parcelas dentro de uma transação existente.
    """
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
        
        # Inserir na tabela despesas com pago = 0 (padrão)
        cur.execute("""
            INSERT INTO despesas 
            (descricao, valor, data, categoria_id, banco_id, 
             parcela_numero, parcela_total, despesa_parcelada_id, pago)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            descricao,
            valor_parcela,
            data_parcela.strftime('%Y-%m-%d'),
            categoria_id,
            banco_id,
            i + 1,  # parcela_numero (1-indexed)
            numero_parcelas,
            despesa_parcelada_id
        ))


def gerar_parcelas(despesa_parcelada_id):
    """
    Gera os lançamentos individuais de uma despesa parcelada.
    Chamada externamente quando necessário regenerar parcelas.
    
    Calcula valor_parcela = valor_total / numero_parcelas
    Incrementa data em 1 mês para cada parcela
    Cria registros em 'despesas' com referência à despesa_parcelada_id
    """
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
        
        # Gerar parcelas
        _gerar_parcelas_interno(cur, despesa_parcelada_id, descricao, valor_total,
                               numero_parcelas, data_primeira_parcela, categoria_id, banco_id)


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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
    
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO despesas_recorrentes
            (descricao, valor, dia_mes, categoria_id, banco_id,
             data_inicio, data_fim, ativa, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (descricao, valor, dia_mes, categoria_id, banco_id,
              data_inicio, data_fim, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        return cur.lastrowid


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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
        # Query usando strftime para verificar mês e ano
        cur.execute("""
            SELECT COUNT(*) FROM despesas
            WHERE despesa_recorrente_id = ?
            AND strftime('%m', data) = ?
            AND strftime('%Y', data) = ?
        """, (recorrente_id, f'{mes:02d}', str(ano)))
        
        count = cur.fetchone()[0]
        return count > 0


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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year
        lancamentos_criados = 0

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
                continue

            # 4. Calcular dia do lançamento
            # Obter o último dia do mês atual
            ultimo_dia_mes = monthrange(ano_atual, mes_atual)[1]
            # Usar o menor valor entre dia_mes configurado e último dia do mês
            dia_lancamento = min(dia_mes, ultimo_dia_mes)
            data_lancamento = date(ano_atual, mes_atual, dia_lancamento)

            # 5. Inserir em despesas com despesa_recorrente_id e pago = 0 (padrão)
            cur.execute("""
                INSERT INTO despesas
                (descricao, valor, data, categoria_id, banco_id, despesa_recorrente_id, pago)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (
                descricao,
                valor,
                data_lancamento.strftime('%Y-%m-%d'),
                categoria_id,
                banco_id,
                recorrente_id
            ))

            lancamentos_criados += 1

        return lancamentos_criados


def listar_despesas_recorrentes(incluir_inativas=False):
    """
    Lista todas as despesas recorrentes.

    Args:
        incluir_inativas: Se True, inclui despesas desativadas

    Returns:
        Lista de dicts com todos os campos da despesa recorrente
    """
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
    
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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


def listar_lancamentos_recorrente(recorrente_id):
    """
    Lista todos os lançamentos gerados de uma despesa recorrente.

    Args:
        recorrente_id: ID da despesa recorrente

    Returns:
        Lista de dicts com dados dos lançamentos ordenados por data
    """
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
