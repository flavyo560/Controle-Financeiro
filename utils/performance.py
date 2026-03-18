"""
Módulo de monitoramento de performance de queries.

Este módulo fornece ferramentas para medir e monitorar o tempo de execução
de queries do banco de dados, comparar com baselines e detectar degradação.
"""

import time
from typing import Any, Callable, Dict, Tuple
from utils.logger import logger


class PerformanceMonitor:
    """Monitor de performance de queries."""
    
    # Baselines de performance (em ms)
    # Estes valores serão estabelecidos após otimizações
    BASELINES: Dict[str, float] = {
        'listar_cartoes': 50.0,
        'listar_despesas_mes': 100.0,
        'calcular_saldo_banco': 30.0,
        'listar_faturas': 80.0,
    }
    
    @staticmethod
    def medir_query(nome_query: str, func: Callable, *args, **kwargs) -> Tuple[Any, float]:
        """
        Mede tempo de execução de uma função.
        
        Args:
            nome_query: Nome da query para logging
            func: Função a executar
            *args, **kwargs: Argumentos para a função
            
        Returns:
            tuple: (resultado, tempo_ms)
        """
        inicio = time.perf_counter()
        resultado = func(*args, **kwargs)
        fim = time.perf_counter()
        
        tempo_ms = (fim - inicio) * 1000
        
        # Verificar contra baseline
        baseline = PerformanceMonitor.BASELINES.get(nome_query)
        if baseline and tempo_ms > baseline * 1.5:
            logger.warning(
                f"Performance degradada: {nome_query} levou {tempo_ms:.2f}ms "
                f"(baseline: {baseline}ms, +{((tempo_ms/baseline - 1) * 100):.1f}%)"
            )
        
        logger.info(f"Query {nome_query}: {tempo_ms:.2f}ms")
        
        return resultado, tempo_ms
    
    @staticmethod
    def estabelecer_baseline(nome_query: str, tempo_ms: float) -> None:
        """
        Estabelece baseline de performance para uma query.
        
        Args:
            nome_query: Nome da query
            tempo_ms: Tempo em milissegundos
        """
        PerformanceMonitor.BASELINES[nome_query] = tempo_ms
        logger.info(f"Baseline estabelecido: {nome_query} = {tempo_ms:.2f}ms")
    
    @staticmethod
    def obter_baseline(nome_query: str) -> float:
        """
        Obtém o baseline de performance para uma query.
        
        Args:
            nome_query: Nome da query
            
        Returns:
            float: Tempo baseline em ms, ou None se não definido
        """
        return PerformanceMonitor.BASELINES.get(nome_query)
    
    @staticmethod
    def comparar_com_baseline(nome_query: str, tempo_ms: float) -> Dict[str, Any]:
        """
        Compara tempo de execução com baseline.
        
        Args:
            nome_query: Nome da query
            tempo_ms: Tempo medido em ms
            
        Returns:
            dict: Informações de comparação
                - baseline: Baseline em ms (ou None)
                - tempo_atual: Tempo medido em ms
                - diferenca_ms: Diferença em ms
                - diferenca_percentual: Diferença em %
                - degradado: True se excedeu baseline em mais de 50%
        """
        baseline = PerformanceMonitor.BASELINES.get(nome_query)
        
        if baseline is None:
            return {
                'baseline': None,
                'tempo_atual': tempo_ms,
                'diferenca_ms': None,
                'diferenca_percentual': None,
                'degradado': False
            }
        
        diferenca_ms = tempo_ms - baseline
        diferenca_percentual = ((tempo_ms / baseline) - 1) * 100
        degradado = tempo_ms > baseline * 1.5
        
        return {
            'baseline': baseline,
            'tempo_atual': tempo_ms,
            'diferenca_ms': diferenca_ms,
            'diferenca_percentual': diferenca_percentual,
            'degradado': degradado
        }
