"""
Tela de Relatório Mensal de Orçamento.

Exibe detalhamento mensal com comparação entre planejado e realizado.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QFileDialog,
    QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.orcamento import (
    listar_orcamentos, calcular_valores_realizados,
    listar_itens_orcamento, calcular_totais_mensais
)
from database.db import obter_categorias
from utils.logger import logger
from datetime import datetime
import csv

# Importar reportlab para PDF
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("Reportlab não disponível - exportação PDF desabilitada")


class RelatorioMensalOrcamento(QWidget):
    """Relatório mensal detalhado de orçamento"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Relatório Mensal de Orçamento")
        self.resize(950, 600)
        
        self.orcamento_id_atual = None
        self.mes_atual = datetime.now().month
        
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
            QComboBox {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #121212;
                border: 1px solid #1f1f1f;
                gridline-color: #252525;
                color: white;
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Título
        titulo = QLabel("RELATÓRIO MENSAL DE ORÇAMENTO")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #ff0055;")
        layout.addWidget(titulo)
        
        # Controles
        controles = QHBoxLayout()
        
        controles.addWidget(QLabel("Orçamento:"))
        self.combo_orcamento = QComboBox()
        self.combo_orcamento.currentIndexChanged.connect(self.on_orcamento_selecionado)
        controles.addWidget(self.combo_orcamento)
        
        controles.addWidget(QLabel("Mês:"))
        self.combo_mes = QComboBox()
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        self.combo_mes.addItems(meses)
        self.combo_mes.setCurrentIndex(self.mes_atual - 1)
        self.combo_mes.currentIndexChanged.connect(self.carregar_relatorio)
        controles.addWidget(self.combo_mes)
        
        controles.addStretch()
        
        btn_exportar = QPushButton("📄 Exportar CSV")
        btn_exportar.clicked.connect(self.exportar_csv)
        controles.addWidget(btn_exportar)
        
        if REPORTLAB_AVAILABLE:
            btn_exportar_pdf = QPushButton("📑 Exportar PDF")
            btn_exportar_pdf.clicked.connect(self.exportar_pdf)
            controles.addWidget(btn_exportar_pdf)
        
        layout.addLayout(controles)
        
        # Tabela de receitas
        receitas_group = QGroupBox("Receitas")
        receitas_layout = QVBoxLayout()
        self.tabela_receitas = self.criar_tabela()
        receitas_layout.addWidget(self.tabela_receitas)
        receitas_group.setLayout(receitas_layout)
        layout.addWidget(receitas_group)
        
        # Tabela de despesas
        despesas_group = QGroupBox("Despesas")
        despesas_layout = QVBoxLayout()
        self.tabela_despesas = self.criar_tabela()
        despesas_layout.addWidget(self.tabela_despesas)
        despesas_group.setLayout(despesas_layout)
        layout.addWidget(despesas_group)
        
        # Resumo
        self.criar_painel_resumo(layout)
        
        # Carregar dados
        self.carregar_orcamentos()
    
    def criar_tabela(self):
        """Cria uma tabela para exibir dados"""
        tabela = QTableWidget()
        tabela.setColumnCount(5)
        tabela.setHorizontalHeaderLabels([
            "Categoria", "Planejado", "Realizado", "Diferença", "Percentual"
        ])
        tabela.horizontalHeader().setStretchLastSection(True)
        tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return tabela
    
    def criar_painel_resumo(self, layout):
        """Cria painel de resumo"""
        resumo_group = QGroupBox("Resumo do Mês")
        resumo_layout = QHBoxLayout()
        
        self.lbl_total_receitas_plan = QLabel("Receitas Planejadas: R$ 0,00")
        self.lbl_total_receitas_real = QLabel("Receitas Realizadas: R$ 0,00")
        self.lbl_total_despesas_plan = QLabel("Despesas Planejadas: R$ 0,00")
        self.lbl_total_despesas_real = QLabel("Despesas Realizadas: R$ 0,00")
        self.lbl_saldo_plan = QLabel("Saldo Planejado: R$ 0,00")
        self.lbl_saldo_real = QLabel("Saldo Realizado: R$ 0,00")
        
        resumo_layout.addWidget(self.lbl_total_receitas_plan)
        resumo_layout.addWidget(self.lbl_total_receitas_real)
        resumo_layout.addWidget(self.lbl_total_despesas_plan)
        resumo_layout.addWidget(self.lbl_total_despesas_real)
        resumo_layout.addWidget(self.lbl_saldo_plan)
        resumo_layout.addWidget(self.lbl_saldo_real)
        
        resumo_group.setLayout(resumo_layout)
        layout.addWidget(resumo_group)
    
    def carregar_orcamentos(self):
        """Carrega lista de orçamentos"""
        try:
            self.combo_orcamento.blockSignals(True)
            self.combo_orcamento.clear()
            
            orcamentos = listar_orcamentos(apenas_ativos=True)
            
            if not orcamentos:
                self.combo_orcamento.addItem("Nenhum orçamento", None)
                self.combo_orcamento.blockSignals(False)
                return
            
            for orc in orcamentos:
                self.combo_orcamento.addItem(f"Orçamento {orc['ano']}", orc['id'])
            
            self.combo_orcamento.blockSignals(False)
            
            if orcamentos:
                self.combo_orcamento.setCurrentIndex(0)
                self.on_orcamento_selecionado(0)
                
        except Exception as e:
            logger.error(f"Erro ao carregar orçamentos: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar orçamentos: {str(e)}")
    
    def on_orcamento_selecionado(self, index):
        """Handler quando orçamento é selecionado"""
        self.orcamento_id_atual = self.combo_orcamento.currentData()
        if self.orcamento_id_atual:
            self.carregar_relatorio()
    
    def carregar_relatorio(self):
        """Carrega dados do relatório"""
        if not self.orcamento_id_atual:
            return
        
        try:
            mes = self.combo_mes.currentIndex() + 1
            
            # Obter categorias
            categorias = obter_categorias()
            categorias_receitas = [c for c in categorias if c['tipo'] == 'receita']
            categorias_despesas = [c for c in categorias if c['tipo'] == 'despesa']
            
            # Obter itens do orçamento
            itens = listar_itens_orcamento(self.orcamento_id_atual)
            itens_dict = {}
            for item in itens:
                if item['mes'] == mes:
                    itens_dict[item['categoria_id']] = item['valor_planejado']
            
            # Obter valores realizados
            valores_realizados = calcular_valores_realizados(self.orcamento_id_atual)
            
            # Preencher tabela de receitas
            self.preencher_tabela(
                self.tabela_receitas,
                categorias_receitas,
                itens_dict,
                valores_realizados,
                mes
            )
            
            # Preencher tabela de despesas
            self.preencher_tabela(
                self.tabela_despesas,
                categorias_despesas,
                itens_dict,
                valores_realizados,
                mes
            )
            
            # Atualizar resumo
            self.atualizar_resumo(mes)
            
        except Exception as e:
            logger.error(f"Erro ao carregar relatório: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório: {str(e)}")
    
    def preencher_tabela(self, tabela, categorias, itens_dict, valores_realizados, mes):
        """Preenche uma tabela com dados"""
        tabela.setRowCount(0)
        
        total_planejado = 0
        total_realizado = 0
        
        for cat in categorias:
            cat_id = cat['id']
            planejado = itens_dict.get(cat_id, 0)
            realizado = valores_realizados.get(cat_id, {}).get(mes, 0)
            diferenca = realizado - planejado
            
            if planejado == 0:
                percentual = 0 if realizado == 0 else 100
            else:
                percentual = (realizado / planejado) * 100
            
            total_planejado += planejado
            total_realizado += realizado
            
            row = tabela.rowCount()
            tabela.insertRow(row)
            
            tabela.setItem(row, 0, QTableWidgetItem(cat['nome']))
            tabela.setItem(row, 1, QTableWidgetItem(f"R$ {planejado:,.2f}"))
            tabela.setItem(row, 2, QTableWidgetItem(f"R$ {realizado:,.2f}"))
            
            item_dif = QTableWidgetItem(f"R$ {diferenca:,.2f}")
            if diferenca < 0:
                item_dif.setForeground(QColor(220, 53, 69))
            elif diferenca > 0:
                item_dif.setForeground(QColor(34, 139, 34))
            tabela.setItem(row, 3, item_dif)
            
            item_perc = QTableWidgetItem(f"{percentual:.1f}%")
            if cat['tipo'] == 'despesa':
                if percentual > 100:
                    item_perc.setForeground(QColor(220, 53, 69))
                elif percentual > 80:
                    item_perc.setForeground(QColor(255, 193, 7))
            else:  # receita
                if percentual < 50:
                    item_perc.setForeground(QColor(220, 53, 69))
                elif percentual < 80:
                    item_perc.setForeground(QColor(255, 193, 7))
            tabela.setItem(row, 4, item_perc)
        
        # Adicionar linha de total
        if categorias:
            row = tabela.rowCount()
            tabela.insertRow(row)
            
            item_total = QTableWidgetItem("TOTAL")
            item_total.setForeground(QColor(255, 255, 255))
            tabela.setItem(row, 0, item_total)
            tabela.setItem(row, 1, QTableWidgetItem(f"R$ {total_planejado:,.2f}"))
            tabela.setItem(row, 2, QTableWidgetItem(f"R$ {total_realizado:,.2f}"))
            tabela.setItem(row, 3, QTableWidgetItem(f"R$ {total_realizado - total_planejado:,.2f}"))
            
            if total_planejado > 0:
                perc_total = (total_realizado / total_planejado) * 100
                tabela.setItem(row, 4, QTableWidgetItem(f"{perc_total:.1f}%"))
    
    def atualizar_resumo(self, mes):
        """Atualiza painel de resumo"""
        try:
            totais = calcular_totais_mensais(self.orcamento_id_atual)
            
            if mes in totais:
                dados = totais[mes]
                
                self.lbl_total_receitas_plan.setText(
                    f"Receitas Planejadas: R$ {dados['planejado_receitas']:,.2f}"
                )
                self.lbl_total_receitas_real.setText(
                    f"Receitas Realizadas: R$ {dados['realizado_receitas']:,.2f}"
                )
                self.lbl_total_despesas_plan.setText(
                    f"Despesas Planejadas: R$ {dados['planejado_despesas']:,.2f}"
                )
                self.lbl_total_despesas_real.setText(
                    f"Despesas Realizadas: R$ {dados['realizado_despesas']:,.2f}"
                )
                self.lbl_saldo_plan.setText(
                    f"Saldo Planejado: R$ {dados['saldo_planejado']:,.2f}"
                )
                self.lbl_saldo_real.setText(
                    f"Saldo Realizado: R$ {dados['saldo_realizado']:,.2f}"
                )
        except Exception as e:
            logger.error(f"Erro ao atualizar resumo: {e}")
    
    def exportar_csv(self):
        """Exporta relatório para CSV"""
        if not self.orcamento_id_atual:
            QMessageBox.warning(self, "Aviso", "Selecione um orçamento primeiro.")
            return
        
        try:
            # Solicitar local de salvamento
            ano = self.combo_orcamento.currentText().split()[-1]
            mes_nome = self.combo_mes.currentText()
            nome_arquivo = f"relatorio_mensal_{ano}_{mes_nome}.csv"
            
            caminho, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Relatório",
                nome_arquivo,
                "CSV Files (*.csv)"
            )
            
            if not caminho:
                return
            
            # Gerar CSV
            with open(caminho, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                
                # Cabeçalho
                writer.writerow([f"Relatório Mensal de Orçamento - {ano} - {mes_nome}"])
                writer.writerow([f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
                writer.writerow([])
                
                # Receitas
                writer.writerow(["RECEITAS"])
                writer.writerow(["Categoria", "Planejado", "Realizado", "Diferença", "Percentual"])
                
                for row in range(self.tabela_receitas.rowCount()):
                    linha = []
                    for col in range(5):
                        item = self.tabela_receitas.item(row, col)
                        linha.append(item.text() if item else "")
                    writer.writerow(linha)
                
                writer.writerow([])
                
                # Despesas
                writer.writerow(["DESPESAS"])
                writer.writerow(["Categoria", "Planejado", "Realizado", "Diferença", "Percentual"])
                
                for row in range(self.tabela_despesas.rowCount()):
                    linha = []
                    for col in range(5):
                        item = self.tabela_despesas.item(row, col)
                        linha.append(item.text() if item else "")
                    writer.writerow(linha)
                
                writer.writerow([])
                
                # Resumo
                writer.writerow(["RESUMO"])
                writer.writerow([self.lbl_total_receitas_plan.text()])
                writer.writerow([self.lbl_total_receitas_real.text()])
                writer.writerow([self.lbl_total_despesas_plan.text()])
                writer.writerow([self.lbl_total_despesas_real.text()])
                writer.writerow([self.lbl_saldo_plan.text()])
                writer.writerow([self.lbl_saldo_real.text()])
            
            QMessageBox.information(self, "Sucesso", f"Relatório exportado para:\n{caminho}")
            logger.info(f"Relatório mensal exportado: {caminho}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {str(e)}")
    
    def exportar_pdf(self):
        """Exporta relatório para PDF"""
        if not self.orcamento_id_atual:
            QMessageBox.warning(self, "Aviso", "Selecione um orçamento primeiro.")
            return
        
        if not REPORTLAB_AVAILABLE:
            QMessageBox.warning(self, "Aviso", 
                "Biblioteca reportlab não instalada.\n"
                "Instale com: pip install reportlab")
            return
        
        try:
            # Solicitar local de salvamento
            ano = self.combo_orcamento.currentText().split()[-1]
            mes_nome = self.combo_mes.currentText()
            nome_arquivo = f"relatorio_mensal_{ano}_{mes_nome}.pdf"
            
            caminho, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Relatório PDF",
                nome_arquivo,
                "PDF Files (*.pdf)"
            )
            
            if not caminho:
                return
            
            # Criar PDF
            doc = SimpleDocTemplate(
                caminho,
                pagesize=landscape(A4),
                rightMargin=1*cm,
                leftMargin=1*cm,
                topMargin=1*cm,
                bottomMargin=1*cm
            )
            
            # Elementos do PDF
            elementos = []
            styles = getSampleStyleSheet()
            
            # Estilo de título
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#ff0055'),
                spaceAfter=12,
                alignment=TA_CENTER
            )
            
            # Título
            titulo = Paragraph(
                f"Relatório Mensal de Orçamento - {ano} - {mes_nome}",
                titulo_style
            )
            elementos.append(titulo)
            
            # Data de geração
            data_style = ParagraphStyle(
                'DataStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            data_geracao = Paragraph(
                f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                data_style
            )
            elementos.append(data_geracao)
            elementos.append(Spacer(1, 0.5*cm))
            
            # Tabela de Receitas
            elementos.append(Paragraph("RECEITAS", styles['Heading2']))
            elementos.append(Spacer(1, 0.3*cm))
            
            dados_receitas = [["Categoria", "Planejado", "Realizado", "Diferença", "Percentual"]]
            for row in range(self.tabela_receitas.rowCount()):
                linha = []
                for col in range(5):
                    item = self.tabela_receitas.item(row, col)
                    linha.append(item.text() if item else "")
                dados_receitas.append(linha)
            
            tabela_receitas = Table(dados_receitas, colWidths=[6*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
            tabela_receitas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            elementos.append(tabela_receitas)
            elementos.append(Spacer(1, 0.5*cm))
            
            # Tabela de Despesas
            elementos.append(Paragraph("DESPESAS", styles['Heading2']))
            elementos.append(Spacer(1, 0.3*cm))
            
            dados_despesas = [["Categoria", "Planejado", "Realizado", "Diferença", "Percentual"]]
            for row in range(self.tabela_despesas.rowCount()):
                linha = []
                for col in range(5):
                    item = self.tabela_despesas.item(row, col)
                    linha.append(item.text() if item else "")
                dados_despesas.append(linha)
            
            tabela_despesas = Table(dados_despesas, colWidths=[6*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
            tabela_despesas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            elementos.append(tabela_despesas)
            elementos.append(Spacer(1, 0.5*cm))
            
            # Resumo
            elementos.append(Paragraph("RESUMO DO MÊS", styles['Heading2']))
            elementos.append(Spacer(1, 0.3*cm))
            
            resumo_style = ParagraphStyle(
                'ResumoStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            )
            
            elementos.append(Paragraph(self.lbl_total_receitas_plan.text(), resumo_style))
            elementos.append(Paragraph(self.lbl_total_receitas_real.text(), resumo_style))
            elementos.append(Paragraph(self.lbl_total_despesas_plan.text(), resumo_style))
            elementos.append(Paragraph(self.lbl_total_despesas_real.text(), resumo_style))
            elementos.append(Paragraph(self.lbl_saldo_plan.text(), resumo_style))
            elementos.append(Paragraph(self.lbl_saldo_real.text(), resumo_style))
            
            # Gerar PDF
            doc.build(elementos)
            
            QMessageBox.information(self, "Sucesso", f"Relatório PDF exportado para:\n{caminho}")
            logger.info(f"Relatório mensal PDF exportado: {caminho}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar PDF: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")
    
    def atualizar(self):
        """Método para atualizar dados"""
        self.carregar_orcamentos()
