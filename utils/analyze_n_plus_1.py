"""
Script para identificar e documentar queries N+1 no código.
"""

import os
import re
from pathlib import Path


def analisar_arquivo(filepath):
    """
    Analisa um arquivo Python em busca de padrões N+1.
    
    Args:
        filepath: Caminho do arquivo
        
    Returns:
        Lista de dicts com problemas encontrados
    """
    problemas = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        
        # Padrão 1: Loop com execute() dentro
        for i, linha in enumerate(linhas, 1):
            # Detectar início de loop
            if re.search(r'^\s*for\s+\w+\s+in\s+', linha):
                # Verificar se há execute() nas próximas 20 linhas
                for j in range(i, min(i + 20, len(linhas))):
                    if 'execute(' in linhas[j] or 'cur.execute(' in linhas[j]:
                        problemas.append({
                            'arquivo': str(filepath),
                            'linha': i,
                            'tipo': 'loop_com_query',
                            'descricao': f'Loop na linha {i} com query na linha {j+1}',
                            'codigo': linha.strip()
                        })
                        break
            
            # Padrão 2: Chamada de função que faz query dentro de loop
            if re.search(r'^\s*for\s+\w+\s+in\s+', linha):
                # Verificar se há chamadas de função nas próximas 20 linhas
                for j in range(i, min(i + 20, len(linhas))):
                    # Funções conhecidas que fazem queries
                    funcoes_query = [
                        'calcular_limite_utilizado',
                        'calcular_saldo_banco',
                        'obter_fatura',
                        'listar_compras_fatura'
                    ]
                    
                    for func in funcoes_query:
                        if func in linhas[j]:
                            problemas.append({
                                'arquivo': str(filepath),
                                'linha': i,
                                'tipo': 'funcao_query_em_loop',
                                'descricao': f'Loop na linha {i} chama {func}() na linha {j+1}',
                                'codigo': linha.strip(),
                                'funcao': func
                            })
                            break
    
    except Exception as e:
        print(f"Erro ao analisar {filepath}: {e}")
    
    return problemas


def gerar_relatorio(problemas):
    """
    Gera relatório formatado dos problemas N+1 encontrados.
    
    Args:
        problemas: Lista de problemas encontrados
    """
    print("=" * 80)
    print("RELATÓRIO DE ANÁLISE N+1")
    print("=" * 80)
    print()
    
    if not problemas:
        print("✓ Nenhum problema N+1 detectado!")
        return
    
    # Agrupar por arquivo
    por_arquivo = {}
    for problema in problemas:
        arquivo = problema['arquivo']
        if arquivo not in por_arquivo:
            por_arquivo[arquivo] = []
        por_arquivo[arquivo].append(problema)
    
    # Imprimir por arquivo
    for arquivo, probs in por_arquivo.items():
        print(f"\n📁 {arquivo}")
        print("-" * 80)
        
        for prob in probs:
            print(f"  Linha {prob['linha']}: {prob['descricao']}")
            print(f"  Tipo: {prob['tipo']}")
            print(f"  Código: {prob['codigo']}")
            
            # Estimar número de queries
            if prob['tipo'] == 'funcao_query_em_loop':
                func = prob.get('funcao', '')
                if func == 'calcular_limite_utilizado':
                    print(f"  ⚠️  Estimativa: 2 queries por iteração (compras + pagamentos)")
                elif func == 'obter_fatura':
                    print(f"  ⚠️  Estimativa: 3+ queries por iteração")
                else:
                    print(f"  ⚠️  Estimativa: 1+ query por iteração")
            
            print()
    
    print("=" * 80)
    print(f"Total de problemas encontrados: {len(problemas)}")
    print("=" * 80)


def main():
    """Executa análise N+1 no código."""
    # Diretórios para analisar
    diretorios = ['database', 'screens']
    
    todos_problemas = []
    
    for diretorio in diretorios:
        if not os.path.exists(diretorio):
            continue
        
        # Analisar todos os arquivos .py
        for filepath in Path(diretorio).rglob('*.py'):
            problemas = analisar_arquivo(filepath)
            todos_problemas.extend(problemas)
    
    # Gerar relatório
    gerar_relatorio(todos_problemas)
    
    return todos_problemas


if __name__ == "__main__":
    main()
