"""
Script para medir performance de queries antes e depois da indexação.
"""

from utils.performance import PerformanceMonitor
from database import listar_despesas, listar_receitas, calcular_saldo_banco
from database.cards import listar_cartoes, listar_faturas
from utils.logger import logger


def medir_queries_comuns():
    """
    Mede performance de queries comuns e compara com baselines.
    
    Returns:
        dict: Resultados das medições
    """
    resultados = {}
    
    # Medir listar_cartoes
    try:
        _, tempo = PerformanceMonitor.medir_query(
            'listar_cartoes',
            listar_cartoes,
            apenas_ativos=True
        )
        comparacao = PerformanceMonitor.comparar_com_baseline('listar_cartoes', tempo)
        resultados['listar_cartoes'] = comparacao
    except Exception as e:
        logger.error(f"Erro ao medir listar_cartoes: {e}")
        resultados['listar_cartoes'] = {'erro': str(e)}
    
    # Medir listar_despesas_mes
    try:
        from datetime import datetime
        mes_atual = datetime.now().strftime('%Y-%m')
        _, tempo = PerformanceMonitor.medir_query(
            'listar_despesas_mes',
            listar_despesas,
            mes=mes_atual
        )
        comparacao = PerformanceMonitor.comparar_com_baseline('listar_despesas_mes', tempo)
        resultados['listar_despesas_mes'] = comparacao
    except Exception as e:
        logger.error(f"Erro ao medir listar_despesas_mes: {e}")
        resultados['listar_despesas_mes'] = {'erro': str(e)}
    
    # Medir calcular_saldo_banco
    try:
        # Pegar primeiro banco disponível
        from database import listar_bancos
        bancos = listar_bancos()
        if bancos:
            banco_id = bancos[0]['id']
            _, tempo = PerformanceMonitor.medir_query(
                'calcular_saldo_banco',
                calcular_saldo_banco,
                banco_id
            )
            comparacao = PerformanceMonitor.comparar_com_baseline('calcular_saldo_banco', tempo)
            resultados['calcular_saldo_banco'] = comparacao
    except Exception as e:
        logger.error(f"Erro ao medir calcular_saldo_banco: {e}")
        resultados['calcular_saldo_banco'] = {'erro': str(e)}
    
    # Medir listar_faturas
    try:
        cartoes = listar_cartoes(apenas_ativos=True)
        if cartoes:
            cartao_id = cartoes[0]['id']
            _, tempo = PerformanceMonitor.medir_query(
                'listar_faturas',
                listar_faturas,
                cartao_id
            )
            comparacao = PerformanceMonitor.comparar_com_baseline('listar_faturas', tempo)
            resultados['listar_faturas'] = comparacao
    except Exception as e:
        logger.error(f"Erro ao medir listar_faturas: {e}")
        resultados['listar_faturas'] = {'erro': str(e)}
    
    return resultados


def gerar_relatorio_performance(resultados):
    """
    Gera relatório de performance formatado.
    
    Args:
        resultados: Dict com resultados das medições
    """
    logger.info("=" * 60)
    logger.info("RELATÓRIO DE PERFORMANCE")
    logger.info("=" * 60)
    
    for query_nome, dados in resultados.items():
        if 'erro' in dados:
            logger.error(f"{query_nome}: ERRO - {dados['erro']}")
            continue
        
        baseline = dados.get('baseline')
        tempo_atual = dados.get('tempo_atual')
        diferenca_percentual = dados.get('diferenca_percentual')
        degradado = dados.get('degradado')
        
        if baseline is None:
            logger.info(f"{query_nome}: {tempo_atual:.2f}ms (sem baseline)")
        else:
            status = "⚠️ DEGRADADO" if degradado else "✓ OK"
            logger.info(
                f"{query_nome}: {tempo_atual:.2f}ms "
                f"(baseline: {baseline:.2f}ms, {diferenca_percentual:+.1f}%) {status}"
            )
    
    logger.info("=" * 60)


if __name__ == "__main__":
    # Executar medições
    resultados = medir_queries_comuns()
    gerar_relatorio_performance(resultados)
