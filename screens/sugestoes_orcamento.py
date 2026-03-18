"""
Tela de Sugestões de Ajuste do Orçamento.

Exibe sugestões automáticas de ajuste baseadas em histórico de execução,
permitindo aplicar ajustes individuais ou em lote.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QHeaderView, QMessageBox, QGroupBox,
    QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from database.orcamento import gerar_sugestoes_ajuste, obter_orcamento, criar_item_orcamento
from database.db import obter_categorias
from utils.logger import logger
from datetime import datetime


class TelaSugestoes(QWidget):
    """Tela para visualizar e aplicar sugestões de ajuste"""
    
    dados_atualizados = pyqtSignal()
    
    def __init__(self, orcamento_id: int):
        super().__init__()
        self.orcamento_id = orcamento_id
        self.sugestoes = []
        self.setWindowTitle("Sugestões de Ajuste - Orçamento")
        self.resize(1100, 600)
        
        # Estilo dark mode
        self.setStyleSheet("""
            QWidget { 
                background-color: #0b0b0b; 
                color: white; 
            }
            QLabel { 
                color: #a4b0be; 
                font-weight: bold; 
            }
            QSpinBox {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QSpinBox:focus {
                border: 1px solid #ff0055;
            }
            QTableWidget {
                background-color: #121212;
                border: 1px solid #1f1f1f;
                gridline-color: #252525;
                color: white;
                selection-background-color: #ff0055;
                selection-color: white;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #a4b0be;
                padding: 5px;
                border: 1px solid #1f1f1f;
                font-weight: bold;
            }
            QPushButton {
                background-color: #1f1f1f;
                color: white;
                border: 1px solid #333333;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                border: 1px solid #ff0055;
            }
            QPushButton.aplicar {
                background-color: #28a745;
                border: 1px solid #28a745;
            }
            QPushButton.aplicar:hover {
                background-color: #218838;
            }
            QGroupBox {
                border: 1px solid #333333;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                color: #a4b0be;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Título
        orcamento = obter_orcamento(orcamento_id)
        ano = orcamento['ano'] if orcamento else "N/A"
        titulo = QLabel(f"SUGESTÕES DE AJUSTE - ORÇAMENTO {ano}")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #ff0055; margin-bottom: 5px;")
        layout.addWidget(titulo)
        
        # Painel de controle
        self.criar_painel_controle(layout)
        
        # Tabela de sugestões
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels([
            "Categoria", "Tipo", "Valor Atual", "Valor Sugerido",
            "Diferença", "% Médio", "Motivo", "Ação"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabela)
        
        # Painel de resumo
        self.criar_painel_resumo(layout)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()
        
        btn_aplicar_todas = QPushButton("Aplicar Todas as Sugestões")
        btn_aplicar_todas.setProperty("class", "aplicar")
        btn_aplicar_todas.clicked.connect(self.aplicar_todas_sugestoes)
        botoes_layout.addWidget(btn_aplicar_todas)
        
        btn_atualizar = QPushButton("Atualizar Sugestões")
        btn_atualizar.clicked.connect(self.carregar_sugestoes)
        botoes_layout.addWidget(btn_atualizar)
        
        layout.addLayout(botoes_layout)
        
        # Carregar dados iniciais
        self.carregar_sugestoes()
    
    def criar_painel_controle(self, layout):
        """Cria o painel de controle"""
        controle_group = QGroupBox("Configurações")
        controle_layout = QHBoxLayout()
        controle_layout.setSpacing(15)
        
        # Seletor de mês atual
        controle_layout.addWidget(QLabel("Mês Atual:"))
        self.spin_mes_atual = QSpinBox()
        self.spin_mes_atual.setMinimum(1)
        self.spin_mes_atual.setMaximum(12)
        self.spin_mes_atual.setValue(datetime.now().month)
        self.spin_mes_atual.valueChanged.connect(self.carregar_sugestoes)
        controle_layout.addWidget(self.spin_mes_atual)
        
        # Nomes dos meses
        meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        mes_atual = self.spin_mes_atual.value()
        lbl_mes_nome = QLabel(f"({meses[mes_atual]})")
        lbl_mes_nome.setStyleSheet("color: #ff0055; font-style: italic;")
        controle_layout.addWidget(lbl_mes_nome)
        
        # Atualizar nome do mês quando mudar
        self.spin_mes_atual.valueChanged.connect(
            lambda v: lbl_mes_nome.setText(f"({meses[v]})")
        )
        
        controle_layout.addStretch()
        
        # Informação
        info_label = QLabel("💡 Sugestões baseadas em categorias >100% (despesas) ou <50% (receitas)")
        info_label.setStyleSheet("color: #a4b0be; font-style: italic; font-weight: normal;")
        controle_layout.addWidget(info_label)
        
        controle_group.setLayout(controle_layout)
        layout.addWidget(controle_group)
    
    def criar_painel_resumo(self, layout):
        """Cria o painel de resumo"""
        resumo_group = QGroupBox("Resumo")
        resumo_layout = QHBoxLayout()
        resumo_layout.setSpacing(30)
        
        self.lbl_total_sugestoes = QLabel("Total de Sugestões: 0")
        self.lbl_impacto_total = QLabel("Impacto Total: R$ 0,00")
        
        resumo_layout.addWidget(self.lbl_total_sugestoes)
        resumo_layout.addWidget(self.lbl_impacto_total)
        resumo_layout.addStretch()
        
        resumo_group.setLayout(resumo_layout)
        layout.addWidget(resumo_group)
    
    def carregar_sugestoes(self):
        """Carrega as sugestões de ajuste"""
        try:
            mes_atual = self.spin_mes_atual.value()
            
            # Gerar sugestões
            self.sugestoes = gerar_sugestoes_ajuste(self.orcamento_id, mes_atual)
            
            # Limpar tabela
            self.tabela.setRowCount(0)
            
            # Contadores para resumo
            impacto_total = 0
            
            # Preencher tabela
            for idx, sugestao in enumerate(self.sugestoes):
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                
                # Categoria
                item_cat = QTableWidgetItem(sugestao['categoria_nome'])
                self.tabela.setItem(row, 0, item_cat)
                
                # Tipo
                tipo = sugestao['tipo'].capitalize()
                item_tipo = QTableWidgetItem(tipo)
                if sugestao['tipo'] == 'receita':
                    item_tipo.setForeground(QColor(34, 139, 34))  # Verde
                else:
                    item_tipo.setForeground(QColor(220, 53, 69))  # Vermelho
                self.tabela.setItem(row, 1, item_tipo)
                
                # Valor Atual
                item_atual = QTableWidgetItem(f"R$ {float(sugestao['valor_atual']):,.2f}")
                item_atual.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 2, item_atual)
                
                # Valor Sugerido
                item_sugerido = QTableWidgetItem(f"R$ {float(sugestao['valor_sugerido']):,.2f}")
                item_sugerido.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                item_sugerido.setForeground(QColor(255, 193, 7))  # Amarelo
                self.tabela.setItem(row, 3, item_sugerido)
                
                # Diferença
                diferenca = sugestao['valor_sugerido'] - sugestao['valor_atual']
                item_dif = QTableWidgetItem(f"R$ {float(diferenca):+,.2f}")
                item_dif.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Colorir baseado na diferença
                if diferenca > 0:
                    item_dif.setForeground(QColor(220, 53, 69))  # Vermelho (aumento)
                elif diferenca < 0:
                    item_dif.setForeground(QColor(34, 139, 34))  # Verde (redução)
                
                self.tabela.setItem(row, 4, item_dif)
                
                # Percentual Médio
                item_pct = QTableWidgetItem(f"{float(sugestao['percentual_medio']):.1f}%")
                item_pct.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela.setItem(row, 5, item_pct)
                
                # Motivo
                item_motivo = QTableWidgetItem(sugestao['motivo'])
                self.tabela.setItem(row, 6, item_motivo)
                
                # Botão Aplicar
                btn_aplicar = QPushButton("Aplicar")
                btn_aplicar.setProperty("class", "aplicar")
                btn_aplicar.clicked.connect(lambda checked, i=idx: self.aplicar_sugestao(i))
                self.tabela.setCellWidget(row, 7, btn_aplicar)
                
                # Somar impacto
                impacto_total += sugestao['impacto']
            
            # Atualizar resumo
            self.lbl_total_sugestoes.setText(f"Total de Sugestões: {len(self.sugestoes)}")
            self.lbl_impacto_total.setText(f"Impacto Total: R$ {float(impacto_total):,.2f}")
            
            if not self.sugestoes:
                QMessageBox.information(
                    self,
                    "Sem Sugestões",
                    "Não há sugestões de ajuste no momento.\n\n"
                    "Sugestões são geradas para:\n"
                    "• Despesas consistentemente acima de 100%\n"
                    "• Receitas consistentemente abaixo de 50%\n"
                    "• Despesas consistentemente abaixo de 50%"
                )
            
            logger.info(f"Sugestões carregadas: {len(self.sugestoes)} sugestões")
            
        except Exception as e:
            logger.error(f"Erro ao carregar sugestões: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar sugestões: {str(e)}")
    
    def aplicar_sugestao(self, indice: int):
        """Aplica uma sugestão específica"""
        if indice < 0 or indice >= len(self.sugestoes):
            return
        
        sugestao = self.sugestoes[indice]
        
        # Confirmar com usuário
        msg = f"Aplicar sugestão para {sugestao['categoria_nome']}?\n\n"
        msg += f"Valor Atual: R$ {float(sugestao['valor_atual']):,.2f}\n"
        msg += f"Valor Sugerido: R$ {float(sugestao['valor_sugerido']):,.2f}\n"
        msg += f"Motivo: {sugestao['motivo']}\n\n"
        msg += "Esta ação aplicará o valor sugerido para todos os 12 meses."
        
        resposta = QMessageBox.question(
            self,
            "Confirmar Aplicação",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Aplicar valor sugerido para todos os 12 meses
            categoria_id = sugestao['categoria_id']
            valor_sugerido = sugestao['valor_sugerido']
            
            # Calcular valor mensal (dividir por 12)
            valor_mensal = valor_sugerido / 12
            
            for mes in range(1, 13):
                criar_item_orcamento(
                    self.orcamento_id,
                    categoria_id,
                    mes,
                    float(valor_mensal)
                )
            
            QMessageBox.information(
                self,
                "Sucesso",
                f"Sugestão aplicada com sucesso!\n\n"
                f"Valor mensal: R$ {float(valor_mensal):,.2f}"
            )
            
            # Recarregar sugestões
            self.carregar_sugestoes()
            
            # Emitir sinal de atualização
            self.dados_atualizados.emit()
            
        except Exception as e:
            logger.error(f"Erro ao aplicar sugestão: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao aplicar sugestão: {str(e)}")
    
    def aplicar_todas_sugestoes(self):
        """Aplica todas as sugestões de uma vez"""
        if not self.sugestoes:
            QMessageBox.warning(self, "Aviso", "Não há sugestões para aplicar.")
            return
        
        # Confirmar com usuário
        msg = f"Aplicar TODAS as {len(self.sugestoes)} sugestões?\n\n"
        msg += "Esta ação aplicará os valores sugeridos para todas as categorias listadas.\n"
        msg += "Os valores serão distribuídos igualmente pelos 12 meses.\n\n"
        msg += "Esta operação não pode ser desfeita automaticamente."
        
        resposta = QMessageBox.question(
            self,
            "Confirmar Aplicação em Lote",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta != QMessageBox.StandardButton.Yes:
            return
        
        try:
            sucesso = 0
            erros = 0
            
            for sugestao in self.sugestoes:
                try:
                    categoria_id = sugestao['categoria_id']
                    valor_sugerido = sugestao['valor_sugerido']
                    valor_mensal = valor_sugerido / 12
                    
                    for mes in range(1, 13):
                        criar_item_orcamento(
                            self.orcamento_id,
                            categoria_id,
                            mes,
                            float(valor_mensal)
                        )
                    
                    sucesso += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao aplicar sugestão para categoria {categoria_id}: {e}")
                    erros += 1
            
            # Mostrar resultado
            msg_resultado = f"Aplicação concluída!\n\n"
            msg_resultado += f"Sucesso: {sucesso} sugestões\n"
            if erros > 0:
                msg_resultado += f"Erros: {erros} sugestões"
            
            QMessageBox.information(self, "Resultado", msg_resultado)
            
            # Recarregar sugestões
            self.carregar_sugestoes()
            
            # Emitir sinal de atualização
            self.dados_atualizados.emit()
            
        except Exception as e:
            logger.error(f"Erro ao aplicar todas as sugestões: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao aplicar sugestões: {str(e)}")
