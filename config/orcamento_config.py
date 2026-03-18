"""
Configurações do módulo de Orçamento e Planejamento Financeiro.

Este arquivo centraliza todas as constantes e configurações utilizadas
pelo sistema de orçamento.
"""

# ==============================
# VALIDAÇÕES E LIMITES
# ==============================

# Limites de ano
ANO_MINIMO = 2000
ANO_MAXIMO = 2100

# Limites de valores monetários
VALOR_MAXIMO = 999999999.99  # ~1 bilhão
CASAS_DECIMAIS = 2

# Limites de mês
MES_MINIMO = 1
MES_MAXIMO = 12


# ==============================
# THRESHOLDS DE STATUS
# ==============================

# Status para DESPESAS (percentual de execução)
STATUS_VERDE_DESPESA_MAX = 80.0  # <= 80% = verde
STATUS_AMARELO_DESPESA_MAX = 100.0  # 80% < x <= 100% = amarelo
# > 100% = vermelho

# Status para RECEITAS (percentual de execução)
STATUS_VERDE_RECEITA_MIN = 80.0  # >= 80% = verde
STATUS_AMARELO_RECEITA_MIN = 50.0  # 50% <= x < 80% = amarelo
# < 50% = vermelho


# ==============================
# CONFIGURAÇÕES DE ALERTAS
# ==============================

# Percentual padrão para alertas
PERCENTUAL_ALERTA_PADRAO = 90.0  # Alertar quando atingir 90% do planejado


# ==============================
# CONFIGURAÇÕES DE SUGESTÕES
# ==============================

# Número mínimo de meses decorridos para gerar sugestões
MESES_MINIMOS_SUGESTAO = 3

# Thresholds para sugestões de ajuste
SUGESTAO_AUMENTO_THRESHOLD = 100.0  # Sugerir aumento se consistentemente > 100%
SUGESTAO_REDUCAO_THRESHOLD = 50.0  # Sugerir redução se consistentemente < 50%

# Número de meses consecutivos para considerar "consistente"
MESES_CONSECUTIVOS_SUGESTAO = 2


# ==============================
# CONFIGURAÇÕES DE PROJEÇÕES
# ==============================

# Número mínimo de meses para calcular média
MESES_MINIMOS_PROJECAO = 2

# Margem de segurança para projeções (%)
MARGEM_SEGURANCA_PROJECAO = 10.0


# ==============================
# CONFIGURAÇÕES DE INTERFACE
# ==============================

# Cores de status (RGB com transparência)
COR_VERDE = (34, 139, 34, 100)  # Verde com transparência
COR_AMARELA = (255, 193, 7, 100)  # Amarelo com transparência
COR_VERMELHA = (220, 53, 69, 100)  # Vermelho com transparência

# Formato de exibição de valores
FORMATO_MOEDA = "R$ {:,.2f}"
FORMATO_PERCENTUAL = "{:.1f}%"


# ==============================
# CONFIGURAÇÕES DE EXPORTAÇÃO
# ==============================

# Formatos suportados
FORMATOS_EXPORTACAO = ['csv', 'pdf']

# Encoding padrão para CSV
CSV_ENCODING = 'utf-8-sig'  # UTF-8 com BOM para Excel

# Separador CSV
CSV_SEPARATOR = ';'


# ==============================
# CONFIGURAÇÕES DE PERFORMANCE
# ==============================

# Cache de valores realizados (em segundos)
CACHE_VALORES_REALIZADOS_TTL = 300  # 5 minutos

# Timeout para operações de banco (em segundos)
DB_TIMEOUT = 30


# ==============================
# MENSAGENS DE ERRO
# ==============================

MSG_ERRO_ANO_INVALIDO = f"Ano deve estar entre {ANO_MINIMO} e {ANO_MAXIMO}"
MSG_ERRO_MES_INVALIDO = f"Mês deve estar entre {MES_MINIMO} e {MES_MAXIMO}"
MSG_ERRO_VALOR_NEGATIVO = "Valor não pode ser negativo"
MSG_ERRO_VALOR_MAXIMO = f"Valor não pode exceder {FORMATO_MOEDA.format(VALOR_MAXIMO)}"
MSG_ERRO_ORCAMENTO_EXISTENTE = "Já existe um orçamento para este ano"
MSG_ERRO_ORCAMENTO_NAO_ENCONTRADO = "Orçamento não encontrado"
MSG_ERRO_CATEGORIA_NAO_ENCONTRADA = "Categoria não encontrada"
MSG_ERRO_ORCAMENTO_INATIVO = "Este orçamento está arquivado e não pode ser editado"


# ==============================
# MENSAGENS DE SUCESSO
# ==============================

MSG_SUCESSO_ORCAMENTO_CRIADO = "Orçamento criado com sucesso!"
MSG_SUCESSO_ORCAMENTO_COPIADO = "Orçamento copiado com sucesso!"
MSG_SUCESSO_VALOR_ATUALIZADO = "Valor atualizado com sucesso!"
MSG_SUCESSO_VALOR_PADRAO_APLICADO = "Valor padrão aplicado a todos os meses!"
MSG_SUCESSO_ORCAMENTO_DESATIVADO = "Orçamento arquivado com sucesso!"
MSG_SUCESSO_ORCAMENTO_REATIVADO = "Orçamento reativado com sucesso!"
MSG_SUCESSO_EXPORTACAO = "Dados exportados com sucesso!"
