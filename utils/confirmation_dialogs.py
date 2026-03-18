"""
Sistema de diálogos de confirmação para ações críticas.

Este módulo fornece diálogos de confirmação com preview de impacto
para operações que modificam ou excluem dados.
"""

import time
from typing import Dict, List, Tuple, Optional, Any
from PyQt6.QtWidgets import QMessageBox
from database.migrations import get_db_manager
from utils.logger import logger


class ConfirmationDialog:
    """Gerenciador de diálogos de confirmação."""
    
    @staticmethod
    def confirmar_exclusao(parent, item_nome: str, item_tipo: str, 
                          impacto: Optional[Dict[str, Any]] = None) -> bool:
        """
        Exibe diálogo de confirmação para exclusão.
        
        Args:
            parent: Widget pai (para centralizar o diálogo)
            item_nome: Nome do item sendo excluído
            item_tipo: Tipo do item (ex: "despesa", "categoria", "cartão")
            impacto: Dict com informações de impacto (opcional)
                - registros_afetados: Número total de registros relacionados
                - detalhes: Lista de tuplas (tipo, quantidade)
                
        Returns:
            bool: True se usuário confirmou, False se cancelou
            
        Exemplo:
            >>> impacto = ConfirmationDialog.calcular_impacto_exclusao('categorias', 5)
            >>> if ConfirmationDialog.confirmar_exclusao(self, "Alimentação", "categoria", impacto):
            ...     excluir_categoria(5)
        """
        # Construir mensagem
        mensagem = f"Tem certeza que deseja excluir {item_tipo} '{item_nome}'?"
        
        # Adicionar informações de impacto se disponíveis
        if impacto and impacto.get('registros_afetados', 0) > 0:
            mensagem += f"\n\n⚠️ ATENÇÃO: Esta ação afetará {impacto['registros_afetados']} registro(s):"
            
            detalhes = impacto.get('detalhes', [])
            for tipo_registro, quantidade in detalhes:
                mensagem += f"\n  • {quantidade} {tipo_registro}(s)"
            
            mensagem += "\n\nTodos os registros relacionados serão removidos."
        
        mensagem += "\n\n⚠️ Esta ação não pode ser desfeita!"
        
        # Exibir diálogo
        resposta = QMessageBox.warning(
            parent,
            f"Confirmar Exclusão de {item_tipo.title()}",
            mensagem,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Botão padrão é "Não"
        )
        
        return resposta == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def confirmar_reset(parent, escopo: str, impacto: Dict[str, Any]) -> bool:
        """
        Exibe diálogo de confirmação para reset.
        
        Args:
            parent: Widget pai
            escopo: Descrição do que será resetado
            impacto: Dict com informações de impacto
                - total_registros: Total de registros que serão removidos
                - tipos: Lista de tipos de dados afetados
                
        Returns:
            bool: True se usuário confirmou, False se cancelou
            
        Exemplo:
            >>> impacto = {'total_registros': 150, 'tipos': ['despesas', 'receitas', 'categorias']}
            >>> if ConfirmationDialog.confirmar_reset(self, "todos os dados", impacto):
            ...     resetar_banco()
        """
        # Construir mensagem
        mensagem = f"⚠️ ATENÇÃO: Você está prestes a resetar {escopo}!"
        mensagem += f"\n\nEsta ação removerá {impacto['total_registros']} registro(s):"
        
        tipos = impacto.get('tipos', [])
        for tipo in tipos:
            mensagem += f"\n  • {tipo}"
        
        mensagem += "\n\n🚨 ESTA AÇÃO É IRREVERSÍVEL!"
        mensagem += "\n\nTodos os dados serão permanentemente perdidos."
        mensagem += "\n\nTem certeza absoluta que deseja continuar?"
        
        # Exibir diálogo crítico
        resposta = QMessageBox.critical(
            parent,
            "⚠️ Confirmar Reset - AÇÃO IRREVERSÍVEL",
            mensagem,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        return resposta == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def calcular_impacto_exclusao(tabela: str, registro_id: int) -> Dict[str, Any]:
        """
        Calcula o impacto de excluir um registro.
        
        Args:
            tabela: Nome da tabela
            registro_id: ID do registro
            
        Returns:
            dict: Informações de impacto
                - registros_afetados: Número total
                - detalhes: Lista de tuplas (tipo, quantidade)
                
        Comportamento:
            - Executa em menos de 500ms
            - Conta registros relacionados via foreign keys
            - Retorna 0 se não houver impacto
            
        Exemplo:
            >>> impacto = ConfirmationDialog.calcular_impacto_exclusao('categorias', 5)
            >>> print(impacto)
            {'registros_afetados': 25, 'detalhes': [('despesas', 15), ('receitas', 10)]}
        """
        inicio = time.perf_counter()
        
        db = get_db_manager()
        detalhes = []
        total = 0
        
        try:
            with db.get_connection(readonly=True) as conn:
                cur = conn.cursor()
                
                # Mapear relacionamentos por tabela
                relacionamentos = {
                    'categorias': [
                        ('despesas', 'categoria_id'),
                        ('receitas', 'categoria_id'),
                        ('compras_cartao', 'categoria_id')
                    ],
                    'bancos': [
                        ('despesas', 'banco_id'),
                        ('receitas', 'banco_id'),
                        ('transferencias', 'banco_origem_id'),
                        ('transferencias', 'banco_destino_id'),
                        ('pagamentos_fatura', 'banco_id')
                    ],
                    'veiculos': [
                        ('abastecimentos', 'veiculo_id'),
                        ('manutencoes', 'veiculo_id')
                    ],
                    'cartoes': [
                        ('compras_cartao', 'cartao_id'),
                        ('pagamentos_fatura', 'cartao_id')
                    ],
                    'despesas_parceladas': [
                        ('despesas', 'despesa_parcelada_id')
                    ],
                    'despesas_recorrentes': [
                        ('despesas', 'despesa_recorrente_id')
                    ]
                }
                
                # Obter relacionamentos para esta tabela
                rels = relacionamentos.get(tabela, [])
                
                for tabela_relacionada, coluna_fk in rels:
                    try:
                        cur.execute(f"""
                            SELECT COUNT(*) 
                            FROM {tabela_relacionada}
                            WHERE {coluna_fk} = ?
                        """, (registro_id,))
                        
                        count = cur.fetchone()[0]
                        if count > 0:
                            detalhes.append((tabela_relacionada, count))
                            total += count
                    except Exception as e:
                        logger.error(f"Erro ao contar {tabela_relacionada}: {e}")
        
        except Exception as e:
            logger.error(f"Erro ao calcular impacto de exclusão: {e}")
        
        # Verificar tempo de execução
        tempo_ms = (time.perf_counter() - inicio) * 1000
        if tempo_ms > 500:
            logger.warning(f"Cálculo de impacto levou {tempo_ms:.2f}ms (limite: 500ms)")
        
        return {
            'registros_afetados': total,
            'detalhes': detalhes
        }
    
    @staticmethod
    def confirmar_acao_critica(parent, titulo: str, mensagem: str, 
                               detalhes: Optional[str] = None) -> bool:
        """
        Exibe diálogo genérico de confirmação para ação crítica.
        
        Args:
            parent: Widget pai
            titulo: Título do diálogo
            mensagem: Mensagem principal
            detalhes: Detalhes adicionais (opcional)
            
        Returns:
            bool: True se confirmado, False se cancelado
        """
        texto_completo = mensagem
        
        if detalhes:
            texto_completo += f"\n\n{detalhes}"
        
        resposta = QMessageBox.warning(
            parent,
            titulo,
            texto_completo,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        return resposta == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def mostrar_info(parent, titulo: str, mensagem: str) -> None:
        """
        Exibe diálogo informativo.
        
        Args:
            parent: Widget pai
            titulo: Título do diálogo
            mensagem: Mensagem
        """
        QMessageBox.information(parent, titulo, mensagem)
    
    @staticmethod
    def mostrar_erro(parent, titulo: str, mensagem: str) -> None:
        """
        Exibe diálogo de erro.
        
        Args:
            parent: Widget pai
            titulo: Título do diálogo
            mensagem: Mensagem de erro
        """
        QMessageBox.critical(parent, titulo, mensagem)
    
    @staticmethod
    def mostrar_aviso(parent, titulo: str, mensagem: str) -> None:
        """
        Exibe diálogo de aviso.
        
        Args:
            parent: Widget pai
            titulo: Título do diálogo
            mensagem: Mensagem de aviso
        """
        QMessageBox.warning(parent, titulo, mensagem)


# Funções auxiliares para uso comum

def confirmar_exclusao_com_impacto(parent, tabela: str, registro_id: int, 
                                   item_nome: str, item_tipo: str) -> bool:
    """
    Confirma exclusão calculando e mostrando impacto automaticamente.
    
    Args:
        parent: Widget pai
        tabela: Nome da tabela
        registro_id: ID do registro
        item_nome: Nome do item
        item_tipo: Tipo do item
        
    Returns:
        bool: True se confirmado
        
    Exemplo:
        >>> if confirmar_exclusao_com_impacto(self, 'categorias', 5, "Alimentação", "categoria"):
        ...     excluir_categoria(5)
    """
    impacto = ConfirmationDialog.calcular_impacto_exclusao(tabela, registro_id)
    return ConfirmationDialog.confirmar_exclusao(parent, item_nome, item_tipo, impacto)
