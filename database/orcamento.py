"""
Módulo de funções de banco de dados para Orçamento e Planejamento Financeiro.

Este módulo contém todas as operações de banco de dados relacionadas a:
- CRUD de orçamentos
- CRUD de itens de orçamento
- Cálculos e agregações
- Projeções e sugestões
- Histórico de alterações
- Alertas
"""
import sqlite3
from datetime import datetime
from typing import Optional
from utils.logger import logger
from database.migrations import get_db_manager


# ==============================
# 📊 CRUD DE ORÇAMENTOS
# ==============================

def criar_orcamento(ano: int) -> int:
    """
    Cria um novo orçamento para o ano especificado.
    
    Args:
        ano: Ano do orçamento (2000-2100)
        
    Returns:
        ID do orçamento criado
        
    Raises:
        ValueError: Se ano inválido ou já existe orçamento para o ano
        sqlite3.IntegrityError: Se violação de constraint
    """
    # Validar ano
    if ano < 2000 or ano > 2100:
        raise ValueError(f"Ano deve estar entre 2000 e 2100. Recebido: {ano}")
    
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Verificar se já existe orçamento para o ano
        cur.execute("SELECT id FROM orcamentos WHERE ano = ?", (ano,))
        if cur.fetchone():
            raise ValueError(f"Já existe um orçamento para o ano {ano}")
        
        # Criar orçamento
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cur.execute("""
                INSERT INTO orcamentos (ano, status, criado_em, atualizado_em)
                VALUES (?, 'ativo', ?, ?)
            """, (ano, agora, agora))
            
            orcamento_id = cur.lastrowid
            logger.info(f"Orçamento criado: ID={orcamento_id}, Ano={ano}")
            return orcamento_id
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Erro de integridade ao criar orçamento: {e}")
            raise


def obter_orcamento(orcamento_id: int) -> Optional[dict]:
    """
    Obtém dados de um orçamento específico.
    
    Args:
        orcamento_id: ID do orçamento
    
    Returns:
        Dict com: id, ano, status, criado_em, atualizado_em
        ou None se não encontrado
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, ano, status, criado_em, atualizado_em
            FROM orcamentos
            WHERE id = ?
        """, (orcamento_id,))
        
        row = cur.fetchone()
        if row:
            return {
                'id': row[0],
                'ano': row[1],
                'status': row[2],
                'criado_em': row[3],
                'atualizado_em': row[4]
            }
        return None


def listar_orcamentos(apenas_ativos: bool = True) -> list[dict]:
    """
    Lista todos os orçamentos ordenados por ano decrescente.
    
    Args:
        apenas_ativos: Se True, retorna apenas orçamentos ativos
        
    Returns:
        Lista de dicts com dados dos orçamentos
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        if apenas_ativos:
            query = """
                SELECT id, ano, status, criado_em, atualizado_em
                FROM orcamentos
                WHERE status = 'ativo'
                ORDER BY ano DESC
            """
            cur.execute(query)
        else:
            query = """
                SELECT id, ano, status, criado_em, atualizado_em
                FROM orcamentos
                ORDER BY ano DESC
            """
            cur.execute(query)
        
        orcamentos = []
        for row in cur.fetchall():
            orcamentos.append({
                'id': row[0],
                'ano': row[1],
                'status': row[2],
                'criado_em': row[3],
                'atualizado_em': row[4]
            })
        
        return orcamentos


def atualizar_status_orcamento(orcamento_id: int, status: str) -> None:
    """
    Atualiza o status de um orçamento (ativo/inativo).
    
    Args:
        orcamento_id: ID do orçamento
        status: Novo status ('ativo' ou 'inativo')
        
    Raises:
        ValueError: Se status inválido
    """
    if status not in ('ativo', 'inativo'):
        raise ValueError(f"Status deve ser 'ativo' ou 'inativo'. Recebido: {status}")
    
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            UPDATE orcamentos
            SET status = ?, atualizado_em = ?
            WHERE id = ?
        """, (status, agora, orcamento_id))
        
        if cur.rowcount == 0:
            logger.warning(f"Orçamento {orcamento_id} não encontrado para atualizar status")
        else:
            logger.info(f"Status do orçamento {orcamento_id} atualizado para '{status}'")


def excluir_orcamento(orcamento_id: int) -> None:
    """
    Exclui um orçamento e todos os seus itens (CASCADE).
    
    Args:
        orcamento_id: ID do orçamento
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("DELETE FROM orcamentos WHERE id = ?", (orcamento_id,))
        
        if cur.rowcount == 0:
            logger.warning(f"Orçamento {orcamento_id} não encontrado para exclusão")
        else:
            logger.info(f"Orçamento {orcamento_id} excluído com sucesso")


# ==============================
# 📝 CRUD DE ITENS DE ORÇAMENTO
# ==============================

def criar_item_orcamento(orcamento_id: int, categoria_id: int, 
                        mes: int, valor_planejado: float) -> int:
    """
    Cria ou atualiza um item de orçamento.
    
    Se já existe item para a combinação (orcamento_id, categoria_id, mes),
    atualiza o valor e registra no histórico.
    
    Args:
        orcamento_id: ID do orçamento
        categoria_id: ID da categoria
        mes: Mês (1-12)
        valor_planejado: Valor planejado (>= 0)
        
    Returns:
        ID do item criado/atualizado
        
    Raises:
        ValueError: Se parâmetros inválidos
    """
    # Validações
    if mes < 1 or mes > 12:
        raise ValueError(f"Mês deve estar entre 1 e 12. Recebido: {mes}")
    if valor_planejado < 0:
        raise ValueError(f"Valor planejado não pode ser negativo. Recebido: {valor_planejado}")
    
    # Arredondar para 2 casas decimais
    valor_planejado = round(valor_planejado, 2)
    
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Verificar se item já existe
        cur.execute("""
            SELECT id, valor_planejado
            FROM itens_orcamento
            WHERE orcamento_id = ? AND categoria_id = ? AND mes = ?
        """, (orcamento_id, categoria_id, mes))
        
        row = cur.fetchone()
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if row:
            # Item existe - atualizar
            item_id = row[0]
            valor_anterior = row[1]
            
            cur.execute("""
                UPDATE itens_orcamento
                SET valor_planejado = ?, atualizado_em = ?
                WHERE id = ?
            """, (valor_planejado, agora, item_id))
            
            # Registrar no histórico se valor mudou (usar mesma conexão)
            if valor_anterior != valor_planejado:
                cur.execute("""
                    INSERT INTO historico_orcamento 
                    (item_orcamento_id, data_alteracao, valor_anterior, valor_novo, usuario_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (item_id, agora, valor_anterior, valor_planejado, None))
                logger.info(f"Alteração registrada no histórico para item {item_id}")
            
            logger.info(f"Item de orçamento atualizado: ID={item_id}")
            return item_id
        else:
            # Item não existe - criar
            cur.execute("""
                INSERT INTO itens_orcamento 
                (orcamento_id, categoria_id, mes, valor_planejado, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (orcamento_id, categoria_id, mes, valor_planejado, agora, agora))
            
            item_id = cur.lastrowid
            logger.info(f"Item de orçamento criado: ID={item_id}")
            return item_id


def obter_item_orcamento(orcamento_id: int, categoria_id: int, mes: int) -> Optional[dict]:
    """
    Obtém um item específico do orçamento.
    
    Args:
        orcamento_id: ID do orçamento
        categoria_id: ID da categoria
        mes: Mês (1-12)
    
    Returns:
        Dict com: id, orcamento_id, categoria_id, mes, valor_planejado
        ou None se não encontrado
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, orcamento_id, categoria_id, mes, valor_planejado
            FROM itens_orcamento
            WHERE orcamento_id = ? AND categoria_id = ? AND mes = ?
        """, (orcamento_id, categoria_id, mes))
        
        row = cur.fetchone()
        if row:
            return {
                'id': row[0],
                'orcamento_id': row[1],
                'categoria_id': row[2],
                'mes': row[3],
                'valor_planejado': row[4]
            }
        return None


def listar_itens_orcamento(orcamento_id: int) -> list[dict]:
    """
    Lista todos os itens de um orçamento.
    
    Args:
        orcamento_id: ID do orçamento
    
    Returns:
        Lista de dicts com dados dos itens
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, orcamento_id, categoria_id, mes, valor_planejado
            FROM itens_orcamento
            WHERE orcamento_id = ?
            ORDER BY categoria_id, mes
        """, (orcamento_id,))
        
        itens = []
        for row in cur.fetchall():
            itens.append({
                'id': row[0],
                'orcamento_id': row[1],
                'categoria_id': row[2],
                'mes': row[3],
                'valor_planejado': row[4]
            })
        
        return itens


def aplicar_valor_padrao_categoria(orcamento_id: int, categoria_id: int, 
                                   valor: float) -> int:
    """
    Aplica um valor padrão para todos os 12 meses de uma categoria.
    
    Args:
        orcamento_id: ID do orçamento
        categoria_id: ID da categoria
        valor: Valor a ser aplicado
        
    Returns:
        Número de itens criados/atualizados
    """
    contador = 0
    for mes in range(1, 13):
        criar_item_orcamento(orcamento_id, categoria_id, mes, valor)
        contador += 1
    
    logger.info(f"Valor padrão {valor} aplicado para categoria {categoria_id} em {contador} meses")
    return contador


def copiar_orcamento_ano_anterior(ano_origem: int, ano_destino: int) -> int:
    """
    Copia todos os itens de um orçamento para outro ano.
    
    Args:
        ano_origem: Ano do orçamento a copiar
        ano_destino: Ano do novo orçamento
        
    Returns:
        ID do novo orçamento criado
        
    Raises:
        ValueError: Se ano_origem não existe ou ano_destino já existe
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Verificar se orçamento de origem existe
        cur.execute("SELECT id FROM orcamentos WHERE ano = ?", (ano_origem,))
        row_origem = cur.fetchone()
        if not row_origem:
            raise ValueError(f"Orçamento do ano {ano_origem} não encontrado")
        
        orcamento_origem_id = row_origem[0]
        
        # Criar novo orçamento para ano destino
        orcamento_destino_id = criar_orcamento(ano_destino)
        
        # Copiar todos os itens
        cur.execute("""
            SELECT categoria_id, mes, valor_planejado
            FROM itens_orcamento
            WHERE orcamento_id = ?
        """, (orcamento_origem_id,))
        
        itens_copiados = 0
        itens_ignorados = 0
        
        for row in cur.fetchall():
            categoria_id, mes, valor_planejado = row
            
            # Verificar se categoria ainda existe e está ativa
            cur.execute("SELECT id FROM categorias WHERE id = ?", (categoria_id,))
            if cur.fetchone():
                try:
                    criar_item_orcamento(orcamento_destino_id, categoria_id, mes, valor_planejado)
                    itens_copiados += 1
                except Exception as e:
                    logger.warning(f"Erro ao copiar item (categoria {categoria_id}, mês {mes}): {e}")
                    itens_ignorados += 1
            else:
                logger.warning(f"Categoria {categoria_id} não existe mais - item ignorado")
                itens_ignorados += 1
        
        logger.info(f"Orçamento copiado: {ano_origem} -> {ano_destino}. "
                   f"Itens copiados: {itens_copiados}, Ignorados: {itens_ignorados}")
        
        return orcamento_destino_id


# ==============================
# 📜 HISTÓRICO DE ALTERAÇÕES
# ==============================

def registrar_alteracao_historico(item_orcamento_id: int, 
                                  valor_anterior: float,
                                  valor_novo: float,
                                  usuario_id: Optional[int] = None) -> int:
    """
    Registra alteração de valor no histórico.
    
    Chamado automaticamente por criar_item_orcamento quando atualiza valor.
    
    Args:
        item_orcamento_id: ID do item de orçamento
        valor_anterior: Valor antes da alteração
        valor_novo: Valor após a alteração
        usuario_id: ID do usuário que fez a alteração (opcional)
    
    Returns:
        ID do registro de histórico criado
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute("""
            INSERT INTO historico_orcamento 
            (item_orcamento_id, data_alteracao, valor_anterior, valor_novo, usuario_id)
            VALUES (?, ?, ?, ?, ?)
        """, (item_orcamento_id, agora, valor_anterior, valor_novo, usuario_id))
        
        historico_id = cur.lastrowid
        logger.info(f"Alteração registrada no histórico: ID={historico_id}")
        return historico_id


def obter_historico_orcamento(orcamento_id: int, 
                              categoria_id: Optional[int] = None,
                              data_inicio: Optional[str] = None,
                              data_fim: Optional[str] = None) -> list[dict]:
    """
    Obtém histórico de alterações de um orçamento.
    
    Args:
        orcamento_id: ID do orçamento
        categoria_id: Filtrar por categoria (opcional)
        data_inicio: Data início do período (opcional)
        data_fim: Data fim do período (opcional)
        
    Returns:
        Lista de dicts com: id, item_orcamento_id, categoria_nome, mes,
        data_alteracao, valor_anterior, valor_novo, variacao_percentual
        Ordenada por data_alteracao DESC
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Construir query com filtros
        query = """
            SELECT 
                h.id,
                h.item_orcamento_id,
                c.nome as categoria_nome,
                i.mes,
                h.data_alteracao,
                h.valor_anterior,
                h.valor_novo,
                CASE 
                    WHEN h.valor_anterior = 0 THEN 0
                    ELSE ((h.valor_novo - h.valor_anterior) / h.valor_anterior * 100)
                END as variacao_percentual
            FROM historico_orcamento h
            JOIN itens_orcamento i ON h.item_orcamento_id = i.id
            JOIN categorias c ON i.categoria_id = c.id
            WHERE i.orcamento_id = ?
        """
        params = [orcamento_id]
        
        if categoria_id:
            query += " AND i.categoria_id = ?"
            params.append(categoria_id)
        
        if data_inicio:
            query += " AND h.data_alteracao >= ?"
            params.append(data_inicio)
        
        if data_fim:
            query += " AND h.data_alteracao <= ?"
            params.append(data_fim)
        
        query += " ORDER BY h.data_alteracao DESC"
        
        cur.execute(query, params)
        
        historico = []
        for row in cur.fetchall():
            historico.append({
                'id': row[0],
                'item_orcamento_id': row[1],
                'categoria_nome': row[2],
                'mes': row[3],
                'data_alteracao': row[4],
                'valor_anterior': row[5],
                'valor_novo': row[6],
                'variacao_percentual': round(row[7], 2) if row[7] else 0
            })
        
        return historico



# ==============================
# 🧮 CÁLCULOS E AGREGAÇÕES
# ==============================

def calcular_valores_realizados(orcamento_id: int) -> dict:
    """
    Calcula valores realizados para todas as categorias e meses.
    
    Agrega receitas e despesas do ano do orçamento por categoria e mês.
    
    Args:
        orcamento_id: ID do orçamento
    
    Returns:
        Dict aninhado: {categoria_id: {mes: valor_realizado}}
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Obter ano do orçamento
        cur.execute("SELECT ano FROM orcamentos WHERE id = ?", (orcamento_id,))
        row = cur.fetchone()
        if not row:
            logger.warning(f"Orçamento {orcamento_id} não encontrado")
            return {}
        
        ano = row[0]
        
        # Calcular valores realizados
        valores = {}
        
        # Receitas
        cur.execute("""
            SELECT 
                categoria_id,
                CAST(strftime('%m', data) AS INTEGER) as mes,
                SUM(valor) as total
            FROM receitas
            WHERE strftime('%Y', data) = ?
            AND categoria_id IS NOT NULL
            GROUP BY categoria_id, mes
        """, (str(ano),))
        
        for row in cur.fetchall():
            categoria_id, mes, total = row
            if categoria_id not in valores:
                valores[categoria_id] = {}
            valores[categoria_id][mes] = total
        
        # Despesas (valores negativos)
        cur.execute("""
            SELECT 
                categoria_id,
                CAST(strftime('%m', data) AS INTEGER) as mes,
                SUM(valor) as total
            FROM despesas
            WHERE strftime('%Y', data) = ?
            AND categoria_id IS NOT NULL
            GROUP BY categoria_id, mes
        """, (str(ano),))
        
        for row in cur.fetchall():
            categoria_id, mes, total = row
            if categoria_id not in valores:
                valores[categoria_id] = {}
            # Despesas já são valores positivos no banco, manter assim
            valores[categoria_id][mes] = total
        
        return valores


def calcular_percentual_execucao(orcamento_id: int) -> dict:
    """
    Calcula percentual de execução para todos os itens.
    
    Percentual = (valor_realizado / valor_planejado) * 100
    
    Args:
        orcamento_id: ID do orçamento
    
    Returns:
        Dict aninhado: {categoria_id: {mes: percentual}}
    """
    valores_realizados = calcular_valores_realizados(orcamento_id)
    itens = listar_itens_orcamento(orcamento_id)
    
    percentuais = {}
    
    for item in itens:
        categoria_id = item['categoria_id']
        mes = item['mes']
        valor_planejado = item['valor_planejado']
        
        if categoria_id not in percentuais:
            percentuais[categoria_id] = {}
        
        # Obter valor realizado
        valor_realizado = 0
        if categoria_id in valores_realizados and mes in valores_realizados[categoria_id]:
            valor_realizado = valores_realizados[categoria_id][mes]
        
        # Calcular percentual (tratar divisão por zero)
        if valor_planejado == 0:
            percentual = 0 if valor_realizado == 0 else 100
        else:
            percentual = (valor_realizado / valor_planejado) * 100
        
        percentuais[categoria_id][mes] = round(percentual, 2)
    
    return percentuais


def calcular_totais_mensais(orcamento_id: int) -> dict:
    """
    Calcula totais planejados e realizados por mês.
    
    Args:
        orcamento_id: ID do orçamento
    
    Returns:
        Dict: {
            mes: {
                'planejado_receitas': float,
                'planejado_despesas': float,
                'realizado_receitas': float,
                'realizado_despesas': float,
                'saldo_planejado': float,
                'saldo_realizado': float
            }
        }
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Inicializar estrutura
        totais = {}
        for mes in range(1, 13):
            totais[mes] = {
                'planejado_receitas': 0,
                'planejado_despesas': 0,
                'realizado_receitas': 0,
                'realizado_despesas': 0,
                'saldo_planejado': 0,
                'saldo_realizado': 0
            }
        
        # Obter totais planejados por mês e tipo de categoria
        cur.execute("""
            SELECT 
                i.mes,
                c.tipo,
                SUM(i.valor_planejado) as total
            FROM itens_orcamento i
            JOIN categorias c ON i.categoria_id = c.id
            WHERE i.orcamento_id = ?
            GROUP BY i.mes, c.tipo
        """, (orcamento_id,))
        
        for row in cur.fetchall():
            mes, tipo, total = row
            if tipo == 'receita':
                totais[mes]['planejado_receitas'] = total
            else:
                totais[mes]['planejado_despesas'] = total
        
        # Obter ano do orçamento
        cur.execute("SELECT ano FROM orcamentos WHERE id = ?", (orcamento_id,))
        row = cur.fetchone()
        if not row:
            return totais
        ano = row[0]
        
        # Obter totais realizados de receitas
        cur.execute("""
            SELECT 
                CAST(strftime('%m', data) AS INTEGER) as mes,
                SUM(valor) as total
            FROM receitas
            WHERE strftime('%Y', data) = ?
            GROUP BY mes
        """, (str(ano),))
        
        for row in cur.fetchall():
            mes, total = row
            if mes in totais:
                totais[mes]['realizado_receitas'] = total
        
        # Obter totais realizados de despesas
        cur.execute("""
            SELECT 
                CAST(strftime('%m', data) AS INTEGER) as mes,
                SUM(valor) as total
            FROM despesas
            WHERE strftime('%Y', data) = ?
            GROUP BY mes
        """, (str(ano),))
        
        for row in cur.fetchall():
            mes, total = row
            if mes in totais:
                totais[mes]['realizado_despesas'] = total
        
        # Calcular saldos
        for mes in totais:
            totais[mes]['saldo_planejado'] = (
                totais[mes]['planejado_receitas'] - totais[mes]['planejado_despesas']
            )
            totais[mes]['saldo_realizado'] = (
                totais[mes]['realizado_receitas'] - totais[mes]['realizado_despesas']
            )
        
        return totais


def calcular_totais_categorias(orcamento_id: int) -> dict:
    """
    Calcula totais planejados e realizados por categoria.
    
    Args:
        orcamento_id: ID do orçamento
    
    Returns:
        Dict: {
            categoria_id: {
                'planejado': float,
                'realizado': float,
                'diferenca': float,
                'percentual': float
            }
        }
    """
    itens = listar_itens_orcamento(orcamento_id)
    valores_realizados = calcular_valores_realizados(orcamento_id)
    
    totais = {}
    
    for item in itens:
        categoria_id = item['categoria_id']
        valor_planejado = item['valor_planejado']
        mes = item['mes']
        
        if categoria_id not in totais:
            totais[categoria_id] = {
                'planejado': 0,
                'realizado': 0,
                'diferenca': 0,
                'percentual': 0
            }
        
        # Somar planejado
        totais[categoria_id]['planejado'] += valor_planejado
        
        # Somar realizado
        if categoria_id in valores_realizados and mes in valores_realizados[categoria_id]:
            totais[categoria_id]['realizado'] += valores_realizados[categoria_id][mes]
    
    # Calcular diferença e percentual
    for categoria_id in totais:
        planejado = totais[categoria_id]['planejado']
        realizado = totais[categoria_id]['realizado']
        
        totais[categoria_id]['diferenca'] = realizado - planejado
        
        if planejado == 0:
            totais[categoria_id]['percentual'] = 0 if realizado == 0 else 100
        else:
            totais[categoria_id]['percentual'] = round((realizado / planejado) * 100, 2)
    
    return totais


# ==============================
# 📈 PROJEÇÕES E SUGESTÕES
# ==============================

def gerar_projecoes(orcamento_id: int, mes_atual: int) -> dict:
    """
    Gera projeções de gastos para meses futuros baseado em média.
    
    Calcula média mensal dos meses decorridos e projeta para meses futuros.
    Identifica categorias com risco de estouro.
    
    Args:
        orcamento_id: ID do orçamento
        mes_atual: Mês atual (1-12)
        
    Returns:
        Dict: {
            categoria_id: {
                'media_mensal': float,
                'projecao_total_ano': float,
                'planejado_total_ano': float,
                'risco_estouro': bool,
                'mes_estimado_estouro': int,
                'ajuste_necessario': float
            }
        }
    """
    if mes_atual < 1 or mes_atual > 12:
        raise ValueError(f"Mês atual deve estar entre 1 e 12. Recebido: {mes_atual}")
    
    valores_realizados = calcular_valores_realizados(orcamento_id)
    totais_categorias = calcular_totais_categorias(orcamento_id)
    
    projecoes = {}
    
    for categoria_id, totais in totais_categorias.items():
        # Calcular média dos meses decorridos
        soma_realizado = 0
        meses_com_dados = 0
        
        if categoria_id in valores_realizados:
            for mes in range(1, mes_atual + 1):
                if mes in valores_realizados[categoria_id]:
                    soma_realizado += valores_realizados[categoria_id][mes]
                    meses_com_dados += 1
        
        media_mensal = soma_realizado / meses_com_dados if meses_com_dados > 0 else 0
        
        # Projetar para o ano todo
        meses_restantes = 12 - mes_atual
        projecao_total_ano = soma_realizado + (media_mensal * meses_restantes)
        
        planejado_total_ano = totais['planejado']
        
        # Verificar risco de estouro
        risco_estouro = projecao_total_ano > planejado_total_ano
        
        # Estimar mês de estouro
        mes_estimado_estouro = None
        if risco_estouro and media_mensal > 0:
            saldo_restante = planejado_total_ano - soma_realizado
            meses_ate_estouro = saldo_restante / media_mensal
            mes_estimado_estouro = min(12, mes_atual + int(meses_ate_estouro) + 1)
        
        # Calcular ajuste necessário
        ajuste_necessario = 0
        if risco_estouro:
            ajuste_necessario = projecao_total_ano - planejado_total_ano
        
        projecoes[categoria_id] = {
            'media_mensal': round(media_mensal, 2),
            'projecao_total_ano': round(projecao_total_ano, 2),
            'planejado_total_ano': round(planejado_total_ano, 2),
            'risco_estouro': risco_estouro,
            'mes_estimado_estouro': mes_estimado_estouro,
            'ajuste_necessario': round(ajuste_necessario, 2)
        }
    
    return projecoes


def gerar_sugestoes_ajuste(orcamento_id: int, mes_atual: int) -> list[dict]:
    """
    Gera sugestões de ajuste baseadas em histórico de execução.
    
    Analisa percentual de execução dos meses decorridos e sugere ajustes
    para categorias consistentemente acima de 100% ou abaixo de 50%.
    
    Args:
        orcamento_id: ID do orçamento
        mes_atual: Mês atual (1-12)
        
    Returns:
        Lista de dicts: [
            {
                'categoria_id': int,
                'categoria_nome': str,
                'tipo': str,  # 'receita' ou 'despesa'
                'valor_atual': float,
                'valor_sugerido': float,
                'motivo': str,
                'percentual_medio': float,
                'impacto': float
            }
        ]
        Ordenada por impacto decrescente
    """
    if mes_atual < 1 or mes_atual > 12:
        raise ValueError(f"Mês atual deve estar entre 1 e 12. Recebido: {mes_atual}")
    
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        valores_realizados = calcular_valores_realizados(orcamento_id)
        percentuais = calcular_percentual_execucao(orcamento_id)
        
        sugestoes = []
        
        # Obter todas as categorias do orçamento
        cur.execute("""
            SELECT DISTINCT i.categoria_id, c.nome, c.tipo
            FROM itens_orcamento i
            JOIN categorias c ON i.categoria_id = c.id
            WHERE i.orcamento_id = ?
        """, (orcamento_id,))
        
        for row in cur.fetchall():
            categoria_id, categoria_nome, tipo = row
            
            # Calcular percentual médio dos meses decorridos
            percentuais_meses = []
            soma_planejado = 0
            soma_realizado = 0
            
            for mes in range(1, mes_atual + 1):
                if categoria_id in percentuais and mes in percentuais[categoria_id]:
                    percentuais_meses.append(percentuais[categoria_id][mes])
                
                # Somar valores para calcular média
                cur.execute("""
                    SELECT valor_planejado
                    FROM itens_orcamento
                    WHERE orcamento_id = ? AND categoria_id = ? AND mes = ?
                """, (orcamento_id, categoria_id, mes))
                row_item = cur.fetchone()
                if row_item:
                    soma_planejado += row_item[0]
                
                if categoria_id in valores_realizados and mes in valores_realizados[categoria_id]:
                    soma_realizado += valores_realizados[categoria_id][mes]
            
            if not percentuais_meses:
                continue
            
            percentual_medio = sum(percentuais_meses) / len(percentuais_meses)
            
            # Gerar sugestão se necessário
            sugestao = None
            
            if tipo == 'despesa' and percentual_medio > 100:
                # Despesa consistentemente acima do planejado
                valor_sugerido = soma_realizado / mes_atual * 12  # Projeção anual
                motivo = f"Despesa {percentual_medio:.1f}% acima do planejado nos últimos {mes_atual} meses"
                sugestao = {
                    'categoria_id': categoria_id,
                    'categoria_nome': categoria_nome,
                    'tipo': tipo,
                    'valor_atual': soma_planejado,
                    'valor_sugerido': round(valor_sugerido, 2),
                    'motivo': motivo,
                    'percentual_medio': round(percentual_medio, 2),
                    'impacto': abs(valor_sugerido - soma_planejado)
                }
            
            elif tipo == 'receita' and percentual_medio < 50:
                # Receita consistentemente abaixo do planejado
                valor_sugerido = soma_realizado / mes_atual * 12  # Projeção anual
                motivo = f"Receita {percentual_medio:.1f}% abaixo do planejado nos últimos {mes_atual} meses"
                sugestao = {
                    'categoria_id': categoria_id,
                    'categoria_nome': categoria_nome,
                    'tipo': tipo,
                    'valor_atual': soma_planejado,
                    'valor_sugerido': round(valor_sugerido, 2),
                    'motivo': motivo,
                    'percentual_medio': round(percentual_medio, 2),
                    'impacto': abs(valor_sugerido - soma_planejado)
                }
            
            elif tipo == 'despesa' and percentual_medio < 50:
                # Despesa consistentemente abaixo do planejado
                valor_sugerido = soma_realizado / mes_atual * 12  # Projeção anual
                motivo = f"Despesa {percentual_medio:.1f}% abaixo do planejado - considere reduzir"
                sugestao = {
                    'categoria_id': categoria_id,
                    'categoria_nome': categoria_nome,
                    'tipo': tipo,
                    'valor_atual': soma_planejado,
                    'valor_sugerido': round(valor_sugerido, 2),
                    'motivo': motivo,
                    'percentual_medio': round(percentual_medio, 2),
                    'impacto': abs(valor_sugerido - soma_planejado)
                }
            
            if sugestao:
                sugestoes.append(sugestao)
        
        # Ordenar por impacto decrescente
        sugestoes.sort(key=lambda x: x['impacto'], reverse=True)
        
        return sugestoes


# ==============================
# 🚨 ALERTAS
# ==============================

def obter_alertas_orcamento(orcamento_id: int, 
                           percentual_alerta: float = 90.0) -> list[dict]:
    """
    Obtém lista de categorias em alerta de estouro.
    
    Args:
        orcamento_id: ID do orçamento
        percentual_alerta: Percentual para considerar alerta (padrão 90%)
        
    Returns:
        Lista de dicts: [
            {
                'categoria_id': int,
                'categoria_nome': str,
                'tipo': str,  # 'receita' ou 'despesa'
                'mes': int,
                'valor_planejado': float,
                'valor_realizado': float,
                'percentual_execucao': float,
                'valor_restante': float,
                'status': str  # 'verde', 'amarelo', 'vermelho'
            }
        ]
        Ordenada por percentual_execucao DESC
    """
    # Validar percentual de alerta
    if percentual_alerta < 50 or percentual_alerta > 150:
        raise ValueError(f"Percentual de alerta deve estar entre 50% e 150%. Recebido: {percentual_alerta}")
    
    db = get_db_manager()
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        valores_realizados = calcular_valores_realizados(orcamento_id)
        percentuais = calcular_percentual_execucao(orcamento_id)
        
        alertas = []
        
        # Obter todos os itens do orçamento
        cur.execute("""
            SELECT i.categoria_id, c.nome, c.tipo, i.mes, i.valor_planejado
            FROM itens_orcamento i
            JOIN categorias c ON i.categoria_id = c.id
            WHERE i.orcamento_id = ?
        """, (orcamento_id,))
        
        for row in cur.fetchall():
            categoria_id, categoria_nome, tipo, mes, valor_planejado = row
            
            # Obter valor realizado
            valor_realizado = 0
            if categoria_id in valores_realizados and mes in valores_realizados[categoria_id]:
                valor_realizado = valores_realizados[categoria_id][mes]
            
            # Obter percentual de execução
            percentual_execucao = 0
            if categoria_id in percentuais and mes in percentuais[categoria_id]:
                percentual_execucao = percentuais[categoria_id][mes]
            
            # Verificar se está em alerta (apenas para despesas)
            if tipo == 'despesa' and percentual_execucao >= percentual_alerta:
                # Calcular status
                if percentual_execucao <= 80:
                    status = 'verde'
                elif percentual_execucao <= 100:
                    status = 'amarelo'
                else:
                    status = 'vermelho'
                
                # Calcular valor restante
                valor_restante = valor_planejado - valor_realizado
                
                alertas.append({
                    'categoria_id': categoria_id,
                    'categoria_nome': categoria_nome,
                    'tipo': tipo,
                    'mes': mes,
                    'valor_planejado': valor_planejado,
                    'valor_realizado': valor_realizado,
                    'percentual_execucao': percentual_execucao,
                    'valor_restante': round(valor_restante, 2),
                    'status': status
                })
        
        # Ordenar por percentual de execução decrescente
        alertas.sort(key=lambda x: x['percentual_execucao'], reverse=True)
        
        return alertas
