"""
Tela de Histórico de Alterações do Orçamento.

Exibe todas as alterações feitas nos valores planejados do orçamento,
com filtros por categoria e período.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QComboBox, QDateEdit, QHeaderView,
    QMessageBox, QGroupBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from database.orcamento import obter_historico_orcamento, obter_orcamento
from database.db import obter_categorias
from utils.logger import logger
from datetime import datetime
import csv
import os


class TelaHistoricoOrcamento(QWidget):
    """Tela para visualizar histórico de alterações do orçamento"""
    
    def __init__(self, orcamento_id: int):
        super().__init__()
        self.orcamento_id = orcamento_id
        self.setWindowTitle("Histórico de Alterações - Orçamento")
        self.resize(950, 550)
        
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
            QComboBox, QDateEdit {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QComboBox:focus, QDateEdit:focus {
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
        titulo = QLabel(f"HISTÓRICO DE ALTERAÇÕES - ORÇAMENTO {ano}")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #ff0055; margin-bottom: 5px;")
        layout.addWidget(titulo)
        
        # Painel de filtros
        self.criar_painel_filtros(layout)
        
        # Tabela de histórico
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels([
            "Data/Hora", "Categoria", "Mês", "Valor Anterior", 
            "Valor Novo", "Variação", "Variação %", "Usuário"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabela)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()
        
        btn_exportar = QPushButton("Exportar CSV")
        btn_exportar.clicked.connect(self.exportar_csv)
        botoes_layout.addWidget(btn_exportar)
        
        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.clicked.connect(self.carregar_historico)
        botoes_layout.addWidget(btn_atualizar)
        
        layout.addLayout(botoes_layout)
        
        # Carregar dados iniciais
        self.carregar_historico()
    
    def criar_painel_filtros(self, layout):
        """Cria o painel de filtros"""
        filtros_group = QGroupBox("Filtros")
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(15)
        
        # Filtro por categoria
        filtros_layout.addWidget(QLabel("Categoria:"))
        self.combo_categoria = QComboBox()
        self.combo_categoria.addItem("Todas", None)
        
        # Carregar categorias
        try:
            categorias = obter_categorias()
            for cat in categorias:
                self.combo_categoria.addItem(cat['nome'], cat['id'])
        except Exception as e:
            logger.error(f"Erro ao carregar categorias: {e}")
        
        self.combo_categoria.currentIndexChanged.connect(self.carregar_historico)
        filtros_layout.addWidget(self.combo_categoria)
        
        filtros_layout.addSpacing(20)
        
        # Filtro por período
        filtros_layout.addWidget(QLabel("Período:"))
        
        filtros_layout.addWidget(QLabel("De:"))
        self.date_inicio = QDateEdit()
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.setDate(QDate.currentDate().addMonths(-3))
        self.date_inicio.dateChanged.connect(self.carregar_historico)
        filtros_layout.addWidget(self.date_inicio)
        
        filtros_layout.addWidget(QLabel("Até:"))
        self.date_fim = QDateEdit()
        self.date_fim.setCalendarPopup(True)
        self.date_fim.setDate(QDate.currentDate())
        self.date_fim.dateChanged.connect(self.carregar_historico)
        filtros_layout.addWidget(self.date_fim)
        
        filtros_layout.addStretch()
        
        # Botão limpar filtros
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.clicked.connect(self.limpar_filtros)
        filtros_layout.addWidget(btn_limpar)
        
        filtros_group.setLayout(filtros_layout)
        layout.addWidget(filtros_group)
    
    def limpar_filtros(self):
        """Limpa todos os filtros"""
        self.combo_categoria.setCurrentIndex(0)
        self.date_inicio.setDate(QDate.currentDate().addMonths(-3))
        self.date_fim.setDate(QDate.currentDate())
        self.carregar_historico()
    
    def carregar_historico(self):
        """Carrega o histórico de alterações com filtros aplicados"""
        try:
            # Obter filtros
            categoria_id = self.combo_categoria.currentData()
            data_inicio = self.date_inicio.date().toString("yyyy-MM-dd")
            data_fim = self.date_fim.date().toString("yyyy-MM-dd")
            
            # Buscar histórico
            historico = obter_historico_orcamento(
                self.orcamento_id,
                categoria_id=categoria_id,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            # Limpar tabela
            self.tabela.setRowCount(0)
            
            # Nomes dos meses
            meses = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            
            # Preencher tabela
            for registro in historico:
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                
                # Data/Hora
                data_hora = datetime.strptime(registro['data_alteracao'], "%Y-%m-%d %H:%M:%S")
                item_data = QTableWidgetItem(data_hora.strftime("%d/%m/%Y %H:%M"))
                self.tabela.setItem(row, 0, item_data)
                
                # Categoria
                item_cat = QTableWidgetItem(registro['categoria_nome'])
                self.tabela.setItem(row, 1, item_cat)
                
                # Mês
                mes = registro['mes']
                mes_nome = meses[mes] if 1 <= mes <= 12 else str(mes)
                item_mes = QTableWidgetItem(mes_nome)
                self.tabela.setItem(row, 2, item_mes)
                
                # Valor Anterior
                item_anterior = QTableWidgetItem(f"R$ {float(registro['valor_anterior']):,.2f}")
                item_anterior.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 3, item_anterior)
                
                # Valor Novo
                item_novo = QTableWidgetItem(f"R$ {float(registro['valor_novo']):,.2f}")
                item_novo.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 4, item_novo)
                
                # Variação (diferença)
                variacao = registro['valor_novo'] - registro['valor_anterior']
                item_var = QTableWidgetItem(f"R$ {float(variacao):+,.2f}")
                item_var.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Colorir baseado na variação
                if variacao > 0:
                    item_var.setForeground(QColor(34, 139, 34))  # Verde
                elif variacao < 0:
                    item_var.setForeground(QColor(220, 53, 69))  # Vermelho
                
                self.tabela.setItem(row, 5, item_var)
                
                # Variação %
                var_percentual = registro['variacao_percentual']
                item_var_pct = QTableWidgetItem(f"{float(var_percentual):+.2f}%")
                item_var_pct.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Colorir baseado na variação
                if var_percentual > 0:
                    item_var_pct.setForeground(QColor(34, 139, 34))  # Verde
                elif var_percentual < 0:
                    item_var_pct.setForeground(QColor(220, 53, 69))  # Vermelho
                
                self.tabela.setItem(row, 6, item_var_pct)
                
                # Usuário (não implementado ainda)
                item_usuario = QTableWidgetItem("-")
                self.tabela.setItem(row, 7, item_usuario)
            
            logger.info(f"Histórico carregado: {len(historico)} registros")
            
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar histórico: {str(e)}")
    
    def exportar_csv(self):
        """Exporta o histórico para CSV"""
        try:
            # Solicitar local de salvamento
            orcamento = obter_orcamento(self.orcamento_id)
            ano = orcamento['ano'] if orcamento else "N/A"
            nome_padrao = f"historico_orcamento_{ano}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            arquivo, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Histórico CSV",
                nome_padrao,
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not arquivo:
                return  # Usuário cancelou
            
            # Obter filtros atuais
            categoria_id = self.combo_categoria.currentData()
            data_inicio = self.date_inicio.date().toString("yyyy-MM-dd")
            data_fim = self.date_fim.date().toString("yyyy-MM-dd")
            
            # Buscar histórico
            historico = obter_historico_orcamento(
                self.orcamento_id,
                categoria_id=categoria_id,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            if not historico:
                QMessageBox.warning(self, "Aviso", "Não há dados para exportar.")
                return
            
            # Nomes dos meses
            meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            
            # Escrever CSV
            with open(arquivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Cabeçalho do arquivo
                writer.writerow([f"Histórico de Alterações - Orçamento {ano}"])
                writer.writerow([f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"])
                writer.writerow([f"Período: {self.date_inicio.date().toString('dd/MM/yyyy')} a {self.date_fim.date().toString('dd/MM/yyyy')}"])
                
                categoria_nome = self.combo_categoria.currentText()
                if categoria_id:
                    writer.writerow([f"Categoria: {categoria_nome}"])
                else:
                    writer.writerow(["Categoria: Todas"])
                
                writer.writerow([])  # Linha em branco
                
                # Cabeçalhos das colunas
                writer.writerow([
                    "Data",
                    "Hora",
                    "Categoria",
                    "Mês",
                    "Valor Anterior (R$)",
                    "Valor Novo (R$)",
                    "Variação (R$)",
                    "Variação (%)"
                ])
                
                # Dados
                for registro in historico:
                    data_hora = datetime.strptime(registro['data_alteracao'], "%Y-%m-%d %H:%M:%S")
                    mes = registro['mes']
                    mes_nome = meses[mes] if 1 <= mes <= 12 else str(mes)
                    variacao = registro['valor_novo'] - registro['valor_anterior']
                    
                    writer.writerow([
                        data_hora.strftime("%d/%m/%Y"),
                        data_hora.strftime("%H:%M:%S"),
                        registro['categoria_nome'],
                        mes_nome,
                        f"{float(registro['valor_anterior']):.2f}",
                        f"{float(registro['valor_novo']):.2f}",
                        f"{float(variacao):+.2f}",
                        f"{float(registro['variacao_percentual']):+.2f}"
                    ])
                
                # Linha de totais
                writer.writerow([])
                writer.writerow([f"Total de registros: {len(historico)}"])
            
            logger.info(f"Histórico exportado para: {arquivo}")
            QMessageBox.information(
                self,
                "Sucesso",
                f"Histórico exportado com sucesso!\n\nArquivo: {os.path.basename(arquivo)}\nRegistros: {len(historico)}"
            )
            
        except PermissionError:
            logger.error(f"Erro de permissão ao salvar arquivo: {arquivo}")
            QMessageBox.critical(
                self,
                "Erro de Permissão",
                "Não foi possível salvar o arquivo.\nVerifique se o arquivo não está aberto em outro programa."
            )
        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {str(e)}")
