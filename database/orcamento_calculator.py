"""
Classe de cálculos e análises de orçamento.

Esta classe encapsula a lógica de negócio para cálculos complexos
relacionados a orçamentos, incluindo status, percentuais e análises.
"""
from typing import Optional, Tuple
from database.orcamento import (
    obter_orcamento,
    listar_itens_orcamento,
    calcular_valores_realizados,
    calcular_percentual_execucao,
    calcular_totais_mensais,
    calcular_totais_categorias
)
from database.migrations import get_db_manager


class OrcamentoCalculator:
    """
    Calculadora de métricas e análises de orçamento.
    """
    
    def __init__(self, orcamento_id: int):
        """
        Inicializa o calculador com um orçamento específico.
        
        Args:
            orcamento_id: ID do orçamento
        """
        self.orcamento_id = orcamento_id
        self.orcamento = obter_orcamento(orcamento_id)
        if not self.orcamento:
            raise ValueError(f"Orçamento {orcamento_id} não encontrado")
        
        self.itens = listar_itens_orcamento(orcamento_id)
        self.valores_realizados = calcular_valores_realizados(orcamento_id)
        self.percentuais = calcular_percentual_execucao(orcamento_id)
    
    def calcular_status_item(self, categoria_id: int, mes: int, 
                            tipo_categoria: str) -> str:
        """
        Calcula status visual de um item (verde/amarelo/vermelho).
        
        Regras para despesas:
        - Verde: <= 80%
        - Amarelo: 80% < x <= 100%
        - Vermelho: > 100%
        
        Regras para receitas:
        - Verde: >= 80%
        - Amarelo: 50% <= x < 80%
        - Vermelho: < 50%
        
        Args:
            categoria_id: ID da categoria
            mes: Mês (1-12)
            tipo_categoria: Tipo da categoria ('receita' ou 'despesa')
        
        Returns:
            'verde', 'amarelo' ou 'vermelho'
        """
        # Obter percentual de execução
        percentual = 0
        if categoria_id in self.percentuais and mes in self.percentuais[categoria_id]:
            percentual = self.percentuais[categoria_id][mes]
        
        if tipo_categoria == 'despesa':
            if percentual <= 80:
                return 'verde'
            elif percentual <= 100:
                return 'amarelo'
            else:
                return 'vermelho'
        else:  # receita
            if percentual >= 80:
                return 'verde'
            elif percentual >= 50:
                return 'amarelo'
            else:
                return 'vermelho'
    
    def calcular_percentual_execucao_geral(self) -> float:
        """
        Calcula percentual de execução geral do orçamento.
        
        Considera apenas meses decorridos do ano.
        
        Returns:
            Percentual de execução geral (0-100+)
        """
        from datetime import datetime
        
        # Obter mês atual se for o ano corrente
        ano_atual = datetime.now().year
        mes_atual = datetime.now().month
        
        if self.orcamento['ano'] == ano_atual:
            meses_considerar = mes_atual
        elif self.orcamento['ano'] < ano_atual:
            meses_considerar = 12
        else:
            # Ano futuro - não há dados realizados ainda
            return 0.0
        
        # Calcular totais
        total_planejado = 0
        total_realizado = 0
        
        for item in self.itens:
            if item['mes'] <= meses_considerar:
                categoria_id = item['categoria_id']
                mes = item['mes']
                
                total_planejado += item['valor_planejado']
                
                if categoria_id in self.valores_realizados and mes in self.valores_realizados[categoria_id]:
                    total_realizado += self.valores_realizados[categoria_id][mes]
        
        if total_planejado == 0:
            return 0.0
        
        return round((total_realizado / total_planejado) * 100, 2)
    
    def identificar_melhor_pior_mes(self) -> Tuple[Optional[int], Optional[int]]:
        """
        Identifica mês com melhor e pior desempenho.
        
        Desempenho = proximidade entre planejado e realizado.
        Quanto mais próximo de 100%, melhor o desempenho.
        
        Returns:
            Tupla (melhor_mes, pior_mes)
        """
        from datetime import datetime
        
        # Obter mês atual se for o ano corrente
        ano_atual = datetime.now().year
        mes_atual = datetime.now().month
        
        if self.orcamento['ano'] == ano_atual:
            meses_considerar = mes_atual
        elif self.orcamento['ano'] < ano_atual:
            meses_considerar = 12
        else:
            # Ano futuro - não há dados
            return (None, None)
        
        totais_mensais = calcular_totais_mensais(self.orcamento_id)
        
        desempenhos = {}
        
        for mes in range(1, meses_considerar + 1):
            if mes not in totais_mensais:
                continue
            
            planejado = totais_mensais[mes]['saldo_planejado']
            realizado = totais_mensais[mes]['saldo_realizado']
            
            # Calcular desvio (quanto menor, melhor)
            if planejado == 0:
                desvio = abs(realizado)
            else:
                desvio = abs((realizado - planejado) / planejado * 100)
            
            desempenhos[mes] = desvio
        
        if not desempenhos:
            return (None, None)
        
        # Melhor mês = menor desvio
        melhor_mes = min(desempenhos, key=desempenhos.get)
        # Pior mês = maior desvio
        pior_mes = max(desempenhos, key=desempenhos.get)
        
        return (melhor_mes, pior_mes)
    
    def calcular_variacao_ano_anterior(self, ano_anterior: int) -> dict:
        """
        Calcula variação percentual em relação ao ano anterior.
        
        Args:
            ano_anterior: Ano para comparação
            
        Returns:
            Dict: {
                categoria_id: {
                    'variacao_planejado': float,
                    'variacao_realizado': float
                }
            }
        """
        db = get_db_manager()
        with db.get_connection() as conn:
            cur = conn.cursor()
            
            # Obter orçamento do ano anterior
            cur.execute("SELECT id FROM orcamentos WHERE ano = ?", (ano_anterior,))
            row = cur.fetchone()
            if not row:
                return {}
            
            orcamento_anterior_id = row[0]
            
            # Calcular totais do ano anterior
            totais_anterior = calcular_totais_categorias(orcamento_anterior_id)
            valores_realizados_anterior = calcular_valores_realizados(orcamento_anterior_id)
            
            # Calcular totais do ano atual
            totais_atual = calcular_totais_categorias(self.orcamento_id)
            
            variacoes = {}
            
            # Comparar categorias
            for categoria_id in totais_atual:
                if categoria_id not in totais_anterior:
                    # Categoria nova - não há comparação
                    continue
                
                planejado_anterior = totais_anterior[categoria_id]['planejado']
                planejado_atual = totais_atual[categoria_id]['planejado']
                
                realizado_anterior = totais_anterior[categoria_id]['realizado']
                realizado_atual = totais_atual[categoria_id]['realizado']
                
                # Calcular variações
                if planejado_anterior == 0:
                    variacao_planejado = 0
                else:
                    variacao_planejado = ((planejado_atual - planejado_anterior) / planejado_anterior) * 100
                
                if realizado_anterior == 0:
                    variacao_realizado = 0
                else:
                    variacao_realizado = ((realizado_atual - realizado_anterior) / realizado_anterior) * 100
                
                variacoes[categoria_id] = {
                    'variacao_planejado': round(variacao_planejado, 2),
                    'variacao_realizado': round(variacao_realizado, 2)
                }
            
            return variacoes
