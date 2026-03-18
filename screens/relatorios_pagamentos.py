from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QFrame, QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from database import (
    listar_despesas_por_periodo_pagamento,
    agrupar_despesas_pagas_por_categoria,
    agrupar_despesas_pagas_por_banco
)
import csv
from datetime import datetime


class RelatoriosPagamentos(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("📊 RELATÓRIO DE PAGAMENTOS")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #00ffa3;")
        layout.addWidget(header)
        
        # Filtros
        filtros_frame = QFrame()
        filtros_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        filtros_layout = QHBoxLayout(filtros_frame)
        
        # Data início
        lbl_inicio = QLabel("Data Início:")
        lbl_inicio.setStyleSheet("color: white; font-weight: bold;")
        self.date_inicio = QDateEdit()
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.date_inicio.setStyleSheet("""
            QDateEdit {
                background-color: #0b0b0b;
                color: white;
                border: 1px solid #333;
                padding: 5px;
                border-radius: 4px;
            }
        """)
        
        # Data fim
        lbl_fim = QLabel("Data Fim:")
        lbl_fim.setStyleSheet("color: white; font-weight: bold;")
        self.date_fim = QDateEdit()
        self.date_fim.setCalendarPopup(True)
        self.date_fim.setDate(QDate.currentDate())
        self.date_fim.setStyleSheet("""
            QDateEdit {
                background-color: #0b0b0b;
                color: white;
                border: 1px solid #333;
                padding: 5px;
                border-radius: 4px;
            }
        """)
        
        # Botão gerar
        self.btn_gerar = QPushButton("Gerar Relatório")
        self.btn_gerar.clicked.connect(self.gerar_relatorio)
        self.btn_gerar.setStyleSheet("""
            QPushButton {
                background-color: #00ffa3;
                color: black;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #00cc82;
            }
        """)
        
        # Botão exportar
        self.btn_exportar = QPushButton("Exportar CSV")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        self.btn_exportar.setEnabled(False)
        self.btn_exportar.setStyleSheet("""
            QPushButton {
                background-color: #3742fa;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2c35c7;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        
        filtros_layout.addWidget(lbl_inicio)
        filtros_layout.addWidget(self.date_inicio)
        filtros_layout.addWidget(lbl_fim)
        filtros_layout.addWidget(self.date_fim)
        filtros_layout.addStretch()
        filtros_layout.addWidget(self.btn_gerar)
        filtros_layout.addWidget(self.btn_exportar)
        
        layout.addWidget(filtros_frame)
        
        # Tabs para diferentes visualizações
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333;
                background-color: #1a1a1a;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #0b0b0b;
                color: white;
                padding: 10px 20px;
                border: 1px solid #333;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                color: #00ffa3;
            }
        """)
        
        # Tab 1: Despesas Pagas
        self.tab_despesas = QWidget()
        tab_despesas_layout = QVBoxLayout(self.tab_despesas)
        
        self.tabela_despesas = QTableWidget()
        self.tabela_despesas.setColumnCount(6)
        self.tabela_despesas.setHorizontalHeaderLabels([
            "Data Pagamento", "Descrição", "Categoria", "Banco", "Valor", "Data Vencimento"
        ])
        self.tabela_despesas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_despesas.setStyleSheet("""
            QTableWidget {
                background-color: #0b0b0b;
                color: white;
                gridline-color: #333;
                border: none;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #00ffa3;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        
        self.lbl_total = QLabel("Total: R$ 0,00")
        self.lbl_total.setStyleSheet("""
            color: #00ffa3;
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
        """)
        
        tab_despesas_layout.addWidget(self.tabela_despesas)
        tab_despesas_layout.addWidget(self.lbl_total, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Tab 2: Agrupamento por Categoria
        self.tab_categoria = QWidget()
        tab_categoria_layout = QVBoxLayout(self.tab_categoria)
        
        self.tabela_categoria = QTableWidget()
        self.tabela_categoria.setColumnCount(3)
        self.tabela_categoria.setHorizontalHeaderLabels(["Categoria", "Quantidade", "Total"])
        self.tabela_categoria.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_categoria.setStyleSheet(self.tabela_despesas.styleSheet())
        
        tab_categoria_layout.addWidget(self.tabela_categoria)
        
        # Tab 3: Agrupamento por Banco
        self.tab_banco = QWidget()
        tab_banco_layout = QVBoxLayout(self.tab_banco)
        
        self.tabela_banco = QTableWidget()
        self.tabela_banco.setColumnCount(3)
        self.tabela_banco.setHorizontalHeaderLabels(["Banco", "Quantidade", "Total"])
        self.tabela_banco.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_banco.setStyleSheet(self.tabela_despesas.styleSheet())
        
        tab_banco_layout.addWidget(self.tabela_banco)
        
        # Adicionar tabs
        self.tabs.addTab(self.tab_despesas, "Despesas Pagas")
        self.tabs.addTab(self.tab_categoria, "Por Categoria")
        self.tabs.addTab(self.tab_banco, "Por Banco")
        
        layout.addWidget(self.tabs)
        
        self.despesas_data = []
    
    def gerar_relatorio(self):
        """Gera o relatório de pagamentos"""
        try:
            data_inicio = self.date_inicio.date().toString("yyyy-MM-dd")
            data_fim = self.date_fim.date().toString("yyyy-MM-dd")
            
            # Validar datas
            if data_inicio > data_fim:
                QMessageBox.warning(self, "Erro", "Data início não pode ser maior que data fim!")
                return
            
            # Buscar despesas pagas
            self.despesas_data = listar_despesas_por_periodo_pagamento(data_inicio, data_fim)
            
            # Preencher tabela de despesas
            self.tabela_despesas.setRowCount(len(self.despesas_data))
            total = 0.0
            
            for i, despesa in enumerate(self.despesas_data):
                # data_pagamento, descricao, categoria, banco, valor, data_vencimento
                self.tabela_despesas.setItem(i, 0, QTableWidgetItem(
                    datetime.strptime(despesa[0], "%Y-%m-%d").strftime("%d/%m/%Y")
                ))
                self.tabela_despesas.setItem(i, 1, QTableWidgetItem(despesa[1]))
                self.tabela_despesas.setItem(i, 2, QTableWidgetItem(despesa[2]))
                self.tabela_despesas.setItem(i, 3, QTableWidgetItem(despesa[3]))
                
                valor_item = QTableWidgetItem(f"R$ {despesa[4]:,.2f}")
                valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela_despesas.setItem(i, 4, valor_item)
                
                data_venc = despesa[5] if despesa[5] else ""
                if data_venc:
                    data_venc = datetime.strptime(data_venc, "%Y-%m-%d").strftime("%d/%m/%Y")
                self.tabela_despesas.setItem(i, 5, QTableWidgetItem(data_venc))
                
                total += despesa[4]
            
            self.lbl_total.setText(f"Total: R$ {total:,.2f}")
            
            # Gerar agrupamentos
            self.gerar_agrupamento_categoria(data_inicio, data_fim)
            self.gerar_agrupamento_banco(data_inicio, data_fim)
            
            self.btn_exportar.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {str(e)}")
    
    def gerar_agrupamento_categoria(self, data_inicio, data_fim):
        """Gera agrupamento por categoria"""
        try:
            dados = agrupar_despesas_pagas_por_categoria(data_inicio, data_fim)
            
            self.tabela_categoria.setRowCount(len(dados))
            
            for i, (nome, quantidade, total) in enumerate(dados):
                self.tabela_categoria.setItem(i, 0, QTableWidgetItem(nome))
                
                qtd_item = QTableWidgetItem(str(quantidade))
                qtd_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela_categoria.setItem(i, 1, qtd_item)
                
                valor_item = QTableWidgetItem(f"R$ {total:,.2f}")
                valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela_categoria.setItem(i, 2, valor_item)
                
        except Exception as e:
            print(f"Erro ao gerar agrupamento por categoria: {e}")
    
    def gerar_agrupamento_banco(self, data_inicio, data_fim):
        """Gera agrupamento por banco"""
        try:
            dados = agrupar_despesas_pagas_por_banco(data_inicio, data_fim)
            
            self.tabela_banco.setRowCount(len(dados))
            
            for i, (nome, quantidade, total) in enumerate(dados):
                self.tabela_banco.setItem(i, 0, QTableWidgetItem(nome))
                
                qtd_item = QTableWidgetItem(str(quantidade))
                qtd_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela_banco.setItem(i, 1, qtd_item)
                
                valor_item = QTableWidgetItem(f"R$ {total:,.2f}")
                valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela_banco.setItem(i, 2, valor_item)
                
        except Exception as e:
            print(f"Erro ao gerar agrupamento por banco: {e}")
    
    def exportar_csv(self):
        """Exporta o relatório para CSV"""
        try:
            if not self.despesas_data:
                QMessageBox.warning(self, "Aviso", "Gere um relatório antes de exportar!")
                return
            
            # Diálogo para salvar arquivo
            arquivo, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Relatório",
                f"relatorio_pagamentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not arquivo:
                return
            
            # Escrever CSV
            with open(arquivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Cabeçalho
                writer.writerow([
                    "Data Pagamento", "Descrição", "Categoria", "Banco", "Valor", "Data Vencimento"
                ])
                
                # Dados
                total = 0.0
                for despesa in self.despesas_data:
                    data_pag = datetime.strptime(despesa[0], "%Y-%m-%d").strftime("%d/%m/%Y")
                    data_venc = ""
                    if despesa[5]:
                        data_venc = datetime.strptime(despesa[5], "%Y-%m-%d").strftime("%d/%m/%Y")
                    
                    writer.writerow([
                        data_pag,
                        despesa[1],
                        despesa[2],
                        despesa[3],
                        f"R$ {despesa[4]:,.2f}",
                        data_venc
                    ])
                    total += despesa[4]
                
                # Total
                writer.writerow([])
                writer.writerow(["", "", "", "TOTAL", f"R$ {total:,.2f}", ""])
            
            QMessageBox.information(
                self,
                "Sucesso",
                f"Relatório exportado com sucesso!\n\n{arquivo}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {str(e)}")
