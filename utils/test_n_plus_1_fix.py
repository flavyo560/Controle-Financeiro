"""
Script para testar e medir a melhoria da otimização N+1 em listar_cartoes().
"""

import time
from database.cards import listar_cartoes
from utils.logger import logger


def medir_listar_cartoes(num_execucoes=5):
    """
    Mede o tempo de execução de listar_cartoes().
    
    Args:
        num_execucoes: Número de vezes para executar (média)
        
    Returns:
        dict: Estatísticas de performance
    """
    tempos = []
    
    for i in range(num_execucoes):
        inicio = time.perf_counter()
        cartoes = listar_cartoes(apenas_ativos=True)
        fim = time.perf_counter()
        
        tempo_ms = (fim - inicio) * 1000
        tempos.append(tempo_ms)
        
        logger.info(f"Execução {i+1}: {tempo_ms:.2f}ms - {len(cartoes)} cartões")
    
    # Calcular estatísticas
    tempo_medio = sum(tempos) / len(tempos)
    tempo_min = min(tempos)
    tempo_max = max(tempos)
    
    return {
        'tempo_medio_ms': tempo_medio,
        'tempo_min_ms': tempo_min,
        'tempo_max_ms': tempo_max,
        'num_execucoes': num_execucoes,
        'tempos': tempos
    }


def main():
    """Executa teste de performance."""
    logger.info("=" * 60)
    logger.info("TESTE DE PERFORMANCE - listar_cartoes() OTIMIZADO")
    logger.info("=" * 60)
    
    # Medir performance
    stats = medir_listar_cartoes(num_execucoes=5)
    
    logger.info("")
    logger.info("RESULTADOS:")
    logger.info(f"  Tempo médio: {stats['tempo_medio_ms']:.2f}ms")
    logger.info(f"  Tempo mínimo: {stats['tempo_min_ms']:.2f}ms")
    logger.info(f"  Tempo máximo: {stats['tempo_max_ms']:.2f}ms")
    logger.info("")
    
    # Comparar com baseline
    baseline = 50.0  # ms (definido em PerformanceMonitor.BASELINES)
    
    if stats['tempo_medio_ms'] <= baseline:
        logger.info(f"✓ Performance OK - Dentro do baseline ({baseline}ms)")
    elif stats['tempo_medio_ms'] <= baseline * 1.5:
        logger.info(f"⚠️  Performance aceitável - Próximo ao baseline ({baseline}ms)")
    else:
        logger.warning(f"❌ Performance degradada - Excede baseline em {((stats['tempo_medio_ms']/baseline - 1) * 100):.1f}%")
    
    logger.info("=" * 60)
    
    return stats


if __name__ == "__main__":
    main()
