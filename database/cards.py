"""
Módulo de operações relacionadas a cartões de crédito.
"""
import sqlite3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from database.connection import DatabaseManager
from database.migrations import get_db_manager
from utils.logger import logger, log_errors


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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO cartoes
            (nome, limite_total, dia_fechamento, dia_vencimento, bandeira, status, criado_em)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (nome, limite_total, dia_fechamento, dia_vencimento, bandeira,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        return cur.lastrowid


def listar_cartoes(apenas_ativos=True):
    """
    Lista todos os cartões cadastrados.
    
    Args:
        apenas_ativos: Se True, retorna apenas cartões com status=1
        
    Returns:
        Lista de dicts com: id, nome, bandeira, limite_total, 
        limite_disponivel, limite_utilizado, percentual_uso,
        dia_fechamento, dia_vencimento, status
        
    Otimização:
        Usa JOINs para calcular limite_utilizado em uma única query,
        eliminando o problema N+1 (2 queries por cartão).
    """
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
        # Query otimizada com JOINs para calcular limites em uma única query
        # LEFT JOIN para compras e pagamentos, GROUP BY para agregar
        query = """
            SELECT 
                c.id, c.nome, c.bandeira, c.limite_total,
                c.dia_fechamento, c.dia_vencimento, c.status, c.criado_em,
                COALESCE(SUM(cc.valor), 0) as total_compras,
                COALESCE(SUM(pf.valor_pago), 0) as total_pagamentos
            FROM cartoes c
            LEFT JOIN compras_cartao cc ON c.id = cc.cartao_id
            LEFT JOIN pagamentos_fatura pf ON c.id = pf.cartao_id
        """
        
        # Adicionar filtro de status
        if apenas_ativos:
            query += " WHERE c.status = 1"
        
        query += """
            GROUP BY c.id, c.nome, c.bandeira, c.limite_total,
                     c.dia_fechamento, c.dia_vencimento, c.status, c.criado_em
            ORDER BY c.nome ASC
        """
        
        cur.execute(query)
        
        cartoes = []
        for row in cur.fetchall():
            # Calcular limite utilizado: compras - pagamentos
            limite_utilizado = max(0, row[8] - row[9])
            limite_disponivel = row[3] - limite_utilizado
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
    
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Verificar se o cartão existe
        cur.execute("SELECT id FROM cartoes WHERE id = ?", (cartao_id,))
        
        if not cur.fetchone():
            raise ValueError(f"Cartão com id {cartao_id} não encontrado")
        
        # Desativar o cartão
        cur.execute("""
            UPDATE cartoes SET status = 0
            WHERE id = ?
        """, (cartao_id,))


@log_errors()
def excluir_cartao(cartao_id):
    """
    Exclui um cartão.
    
    Args:
        cartao_id: ID do cartão
        
    Raises:
        ValueError: Se existem compras associadas ao cartão ou cartão não encontrado
    """
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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

        return cur.lastrowid


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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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

        return compra_parcelada_id


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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
        
        logger.info(f"Compra editada: id={compra_id}, cartao_id={cartao_id}")


@log_errors()
def excluir_compra_cartao(compra_id):
    """
    Exclui uma compra do cartão.
    
    Comportamento:
        - Remove registro de compras_cartao
        - Recalcula limite_utilizado
    """
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Buscar informações da compra antes de excluir
        cur.execute("SELECT cartao_id, valor FROM compras_cartao WHERE id = ?", (compra_id,))
        compra = cur.fetchone()
        
        if not compra:
            raise ValueError(f"Compra com ID {compra_id} não encontrada")
        
        cartao_id, valor = compra
        
        # Excluir compra
        cur.execute("DELETE FROM compras_cartao WHERE id = ?", (compra_id,))
        
        logger.info(f"Compra excluída: id={compra_id}, cartao_id={cartao_id}, valor={valor:.2f}")


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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
        
        logger.info(
            f"Compra parcelada excluída: compra_parcelada_id={compra_parcelada_id}, "
            f"cartao_id={cartao_id}, num_parcelas={num_parcelas}, valor_total={valor_total:.2f}"
        )


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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Buscar parcela atual
        cur.execute("""
            SELECT cartao_id, compra_parcelada_id, parcela_atual, descricao, 
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
                WHERE compra_parcelada_id = ? AND parcela_atual >= ?
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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT c.id, c.descricao, c.valor, c.data_compra,
                   cat.nome AS categoria_nome,
                   c.parcela_atual, c.total_parcelas
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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
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
        
        # 4. Criar despesa na tabela despesas
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
        
        # Commit automático pelo context manager
    
    # 7. Sincronizar pagamento da fatura (marcar despesa de fatura como paga)
    try:
        from database.db import sincronizar_pagamento_fatura
        sincronizar_pagamento_fatura(cartao_id, mes_fatura)
    except Exception as e:
        logger.warning(f"Erro ao sincronizar pagamento de fatura: {e}")
    
    return pagamento_id


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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
        # Construir query com JOIN para obter nome da categoria
        query = """
            SELECT c.id, c.descricao, c.valor, c.data_compra, c.mes_fatura,
                   c.parcela_atual, c.total_parcelas, c.compra_parcelada_id,
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
                'parcela_atual': row[5],
                'total_parcelas': row[6],
                'compra_parcelada_id': row[7],
                'categoria_nome': row[8],
                'parcela_info': parcela_info
            })
        
        return compras


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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
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


def listar_compras_parceladas_andamento(cartao_id):
    """
    Lista compras parceladas que ainda têm parcelas futuras.
    
    Args:
        cartao_id: ID do cartão
        
    Returns:
        Lista de dicts com: compra_parcelada_id, descricao, valor_total,
        parcelas_pagas, parcelas_pendentes, valor_parcela
    """
    db = get_db_manager()
    
    with db.get_connection(readonly=True) as conn:
        cur = conn.cursor()
        
        # Obter mês atual no formato YYYY-MM
        mes_atual = datetime.now().strftime('%Y-%m')
        
        # Buscar compras parceladas que têm parcelas futuras
        query = """
            SELECT compra_parcelada_id,
                   descricao,
                   total_parcelas,
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
