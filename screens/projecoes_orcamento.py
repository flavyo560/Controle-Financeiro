"""
Tela de Projeções do Orçamento.

Exibe projeções de gastos para meses futuros baseadas em média histórica,
identifica categorias com risco de estouro e sugere ajustes necessários.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QHeaderView, QMessageBox, QGroupBox,
    QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.orcamento import gerar_projecoes, obter_orcamento
from database.db import obter_categorias
from utils.logger import logger
from datetime import datetime


class TelaProjecoes(QWidget):
    """Tela para visualizar projeções de orçamento"""
    
    def __init__(self, orcamento_id: int):
        super().__init__()
        self.orcamento_id = orcamento_id
        self.setWindowTitle("Projeções de Orçamento")
        self.resize(1000, 600)
        
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
        titulo = QLabel(f"PROJEÇÕES DE ORÇAMENTO - {ano}")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #ff0055; margin-bottom: 5px;")
        layout.addWidget(titulo)
        
        # Painel de controle
        self.criar_painel_controle(layout)
        
        # Tabela de projeções
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7)
        self.tabela.setHorizontalHeaderLabels([
            "Categoria", "Média Mensal", "Projeção Total Ano",
            "Planejado Total Ano", "Diferença", "Risco Estouro", "Mês Est. Estouro"
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
        
        btn_atualizar = QPushButton("Atualizar Projeções")
        btn_atualizar.clicked.connect(self.carregar_projecoes)
        botoes_layout.addWidget(btn_atualizar)
        
        layout.addLayout(botoes_layout)
        
        # Carregar dados iniciais
        self.carregar_projecoes()
    
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
        self.spin_mes_atual.valueChanged.connect(self.carregar_projecoes)
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
        info_label = QLabel("💡 As projeções são baseadas na média dos meses decorridos")
        info_label.setStyleSheet("color: #a4b0be; font-style: italic; font-weight: normal;")
        controle_layout.addWidget(info_label)
        
        controle_group.setLayout(controle_layout)
        layout.addWidget(controle_group)
    
    def criar_painel_resumo(self, layout):
        """Cria o painel de resumo"""
        resumo_group = QGroupBox("Resumo")
        resumo_layout = QHBoxLayout()
        resumo_layout.setSpacing(30)
        
        self.lbl_total_categorias = QLabel("Total de Categorias: 0")
        self.lbl_categorias_risco = QLabel("Categorias em Risco: 0")
        self.lbl_categorias_risco.setStyleSheet("color: #dc3545;")
        self.lbl_ajuste_necessario = QLabel("Ajuste Total Necessário: R$ 0,00")
        
        resumo_layout.addWidget(self.lbl_total_categorias)
        resumo_layout.addWidget(self.lbl_categorias_risco)
        resumo_layout.addWidget(self.lbl_ajuste_necessario)
        resumo_layout.addStretch()
        
        resumo_group.setLayout(resumo_layout)
        layout.addWidget(resumo_group)
    
    def carregar_projecoes(self):
        """Carrega as projeções de orçamento"""
        try:
            mes_atual = self.spin_mes_atual.value()
            
            # Gerar projeções
            projecoes = gerar_projecoes(self.orcamento_id, mes_atual)
            
            # Limpar tabela
            self.tabela.setRowCount(0)
            
            # Carregar categorias para obter nomes
            categorias_dict = {}
            try:
                categorias = obter_categorias()
                for cat in categorias:
                    categorias_dict[cat['id']] = cat['nome']
            except Exception as e:
                logger.error(f"Erro ao carregar categorias: {e}")
            
            # Contadores para resumo
            total_categorias = len(projecoes)
            categorias_em_risco = 0
            ajuste_total = 0
            
            # Preencher tabela
            for categoria_id, dados in projecoes.items():
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                
                # Categoria
                categoria_nome = categorias_dict.get(categoria_id, f"ID {categoria_id}")
                item_cat = QTableWidgetItem(categoria_nome)
                self.tabela.setItem(row, 0, item_cat)
                
                # Média Mensal
                item_media = QTableWidgetItem(f"R$ {float(dados['media_mensal']):,.2f}")
                item_media.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 1, item_media)
                
                # Projeção Total Ano
                item_projecao = QTableWidgetItem(f"R$ {float(dados['projecao_total_ano']):,.2f}")
                item_projecao.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 2, item_projecao)
                
                # Planejado Total Ano
                item_planejado = QTableWidgetItem(f"R$ {float(dados['planejado_total_ano']):,.2f}")
                item_planejado.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 3, item_planejado)
                
                # Diferença
                diferenca = dados['projecao_total_ano'] - dados['planejado_total_ano']
                item_dif = QTableWidgetItem(f"R$ {float(diferenca):+,.2f}")
                item_dif.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Colorir baseado na diferença
                if diferenca > 0:
                    item_dif.setForeground(QColor(220, 53, 69))  # Vermelho (estouro)
                elif diferenca < 0:
                    item_dif.setForeground(QColor(34, 139, 34))  # Verde (economia)
                
                self.tabela.setItem(row, 4, item_dif)
                
                # Risco de Estouro
                risco = "SIM" if dados['risco_estouro'] else "NÃO"
                item_risco = QTableWidgetItem(risco)
                item_risco.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if dados['risco_estouro']:
                    item_risco.setForeground(QColor(220, 53, 69))  # Vermelho
                    item_risco.setBackground(QColor(220, 53, 69, 50))  # Fundo vermelho transparente
                    categorias_em_risco += 1
                    ajuste_total += dados['ajuste_necessario']
                else:
                    item_risco.setForeground(QColor(34, 139, 34))  # Verde
                
                self.tabela.setItem(row, 5, item_risco)
                
                # Mês Estimado de Estouro
                mes_estouro = dados['mes_estimado_estouro']
                if mes_estouro:
                    meses = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                            'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    mes_nome = meses[mes_estouro] if 1 <= mes_estouro <= 12 else str(mes_estouro)
                    item_mes = QTableWidgetItem(mes_nome)
                    item_mes.setForeground(QColor(255, 193, 7))  # Amarelo
                else:
                    item_mes = QTableWidgetItem("-")
                
                item_mes.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela.setItem(row, 6, item_mes)
            
            # Atualizar resumo
            self.lbl_total_categorias.setText(f"Total de Categorias: {total_categorias}")
            self.lbl_categorias_risco.setText(f"Categorias em Risco: {categorias_em_risco}")
            self.lbl_ajuste_necessario.setText(f"Ajuste Total Necessário: R$ {float(ajuste_total):,.2f}")
            
            logger.info(f"Projeções carregadas: {total_categorias} categorias, {categorias_em_risco} em risco")
            
        except Exception as e:
            logger.error(f"Erro ao carregar projeções: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar projeções: {str(e)}")
