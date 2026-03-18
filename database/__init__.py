"""
Módulo de banco de dados modular.

Exports principais funções mantendo compatibilidade com código existente.
"""

# Connection management
from database.connection import DatabaseManager
from database.migrations import get_db_manager, get_db_path, conectar

# Users
from database.users import (
    existe_usuario,
    criar_usuario,
    validar_login,
    hash_senha_bcrypt,
    verificar_senha_bcrypt,
    hash_senha  # Deprecated
)

# Expenses (simple - not implemented yet)
# from database.expenses import ...

# Revenues (not implemented yet)
# from database.revenues import ...

# Recurring and parceladas
from database.recurring import (
    criar_despesa_parcelada,
    gerar_parcelas,
    listar_despesas_parceladas,
    editar_parcela,
    excluir_parcela,
    criar_despesa_recorrente,
    verificar_lancamento_mes_atual,
    gerar_lancamentos_recorrentes,
    listar_despesas_recorrentes,
    editar_despesa_recorrente,
    desativar_despesa_recorrente,
    excluir_despesa_recorrente,
    listar_lancamentos_recorrente
)

# Cards
from database.cards import (
    criar_cartao,
    listar_cartoes,
    editar_cartao,
    desativar_cartao,
    excluir_cartao,
    calcular_limite_utilizado,
    calcular_limite_disponivel,
    obter_info_limite,
    calcular_mes_fatura,
    calcular_data_vencimento,
    criar_compra_cartao,
    criar_compra_parcelada_cartao,
    editar_compra_cartao,
    excluir_compra_cartao,
    excluir_compra_parcelada_cartao,
    editar_parcela_cartao,
    listar_compras_fatura,
    obter_fatura,
    listar_faturas_cartao,
    registrar_pagamento_fatura,
    listar_pagamentos_fatura,
    listar_compras_cartao,
    calcular_total_por_categoria,
    calcular_media_gastos_mensais,
    listar_compras_parceladas_andamento
)

# Fleet
from database.fleet import (
    listar_veiculos_ativos
)

# Investments (not implemented yet)
# from database.investments import ...

# Migrations
from database.migrations import (
    criar_tabelas,
    resetar_banco
)

# Legacy functions from db.py (to be modularized)
from database.db import (
    calcular_saldo_banco,
    executar_escrita,
    # Funções de controle de vencimento e pagamento
    validar_datas_despesa,
    converter_data_br_para_iso,
    converter_data_iso_para_br,
    criar_despesa_com_datas,
    atualizar_despesa_com_datas,
    definir_data_pagamento,
    marcar_despesa_paga_com_data,
    listar_despesas_vencidas,
    listar_despesas_vencendo_em,
    listar_despesas_por_periodo_pagamento,
    calcular_total_despesas_vencidas,
    calcular_despesas_vencendo_periodo,
    calcular_despesas_vencendo_mes_atual,
    agrupar_despesas_pagas_por_categoria,
    agrupar_despesas_pagas_por_banco,
    marcar_parcelas_em_lote,
    atualizar_vencimento_parcelas_futuras,
)

__all__ = [
    # Connection
    'DatabaseManager',
    'get_db_manager',
    'get_db_path',
    'conectar',  # Deprecated but kept for backward compatibility
    # Users
    'existe_usuario',
    'criar_usuario',
    'validar_login',
    'hash_senha_bcrypt',
    'verificar_senha_bcrypt',
    'hash_senha',
    # Recurring
    'criar_despesa_parcelada',
    'gerar_parcelas',
    'listar_despesas_parceladas',
    'editar_parcela',
    'excluir_parcela',
    'criar_despesa_recorrente',
    'verificar_lancamento_mes_atual',
    'gerar_lancamentos_recorrentes',
    'listar_despesas_recorrentes',
    'editar_despesa_recorrente',
    'desativar_despesa_recorrente',
    'excluir_despesa_recorrente',
    'listar_lancamentos_recorrente',
    # Cards
    'criar_cartao',
    'listar_cartoes',
    'editar_cartao',
    'desativar_cartao',
    'excluir_cartao',
    'calcular_limite_utilizado',
    'calcular_limite_disponivel',
    'obter_info_limite',
    'calcular_mes_fatura',
    'calcular_data_vencimento',
    'criar_compra_cartao',
    'criar_compra_parcelada_cartao',
    'editar_compra_cartao',
    'excluir_compra_cartao',
    'excluir_compra_parcelada_cartao',
    'editar_parcela_cartao',
    'listar_compras_fatura',
    'obter_fatura',
    'listar_faturas_cartao',
    'registrar_pagamento_fatura',
    'listar_pagamentos_fatura',
    'listar_compras_cartao',
    'calcular_total_por_categoria',
    'calcular_media_gastos_mensais',
    'listar_compras_parceladas_andamento',
    # Fleet
    'listar_veiculos_ativos',
    # Migrations
    'criar_tabelas',
    'resetar_banco',
    # Legacy functions (to be modularized)
    'calcular_saldo_banco',
    'executar_escrita',
    # Controle de vencimento e pagamento
    'validar_datas_despesa',
    'converter_data_br_para_iso',
    'converter_data_iso_para_br',
    'criar_despesa_com_datas',
    'atualizar_despesa_com_datas',
    'definir_data_pagamento',
    'marcar_despesa_paga_com_data',
    'listar_despesas_vencidas',
    'listar_despesas_vencendo_em',
    'listar_despesas_por_periodo_pagamento',
    'calcular_total_despesas_vencidas',
    'calcular_despesas_vencendo_periodo',
    'calcular_despesas_vencendo_mes_atual',
    'agrupar_despesas_pagas_por_categoria',
    'agrupar_despesas_pagas_por_banco',
    'marcar_parcelas_em_lote',
    'atualizar_vencimento_parcelas_futuras',
]
