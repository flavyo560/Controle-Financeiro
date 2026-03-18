"""
Tela de Relatório Anual de Orçamento.

Exibe consolidação anual com comparação entre planejado e realizado,
identificação de melhor/pior mês e comparação com ano anterior.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QFileDialog,
    QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.orcamento import (
    listar_orcamentos, calcular_totais_categorias, obter_orcamento
)
from database.orcamento_calculator import OrcamentoCalculator
from database.db import obter_categorias
from utils.logger import logger
from datetime import datetime
import csv

# Importar reportlab para PDF
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("Reportlab não disponível - exportação PDF desabilitada")


class RelatorioAnualOrcamento(QWidget):
    """Relatório anual consolidado de orçamento"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Relatório Anual de Orçamento")
        self.resize(1100, 600)
        
        self.orcamento_id_atual = None
        
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
            QComboBox, QCheckBox {
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
        titulo = QLabel("RELATÓRIO ANUAL DE ORÇAMENTO")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #ff0055;")
        layout.addWidget(titulo)
        
        # Controles
        controles = QHBoxLayout()
        
        controles.addWidget(QLabel("Orçamento:"))
        self.combo_orcamento = QComboBox()
        self.combo_orcamento.currentIndexChanged.connect(self.on_orcamento_selecionado)
        controles.addWidget(self.combo_orcamento)
        
        self.chk_comparar_ano_anterior = QCheckBox("Comparar com ano anterior")
        self.chk_comparar_ano_anterior.stateChanged.connect(self.carregar_relatorio)
        controles.addWidget(self.chk_comparar_ano_anterior)
        
        controles.addStretch()
        
        btn_exportar = QPushButton("📄 Exportar CSV")
        btn_exportar.clicked.connect(self.exportar_csv)
        controles.addWidget(btn_exportar)
        
        if REPORTLAB_AVAILABLE:
            btn_exportar_pdf = QPushButton("📑 Exportar PDF")
            btn_exportar_pdf.clicked.connect(self.exportar_pdf)
            controles.addWidget(btn_exportar_pdf)
        
        layout.addLayout(controles)
        
        # Painel de métricas
        self.criar_painel_metricas(layout)
        
        # Tabela de consolidação
        consolidacao_group = QGroupBox("Consolidação Anual por Categoria")
        consolidacao_layout = QVBoxLayout()
        self.tabela_consolidacao = self.criar_tabela_consolidacao()
        consolidacao_layout.addWidget(self.tabela_consolidacao)
        consolidacao_group.setLayout(consolidacao_layout)
        layout.addWidget(consolidacao_group)
        
        # Tabela de comparação com ano anterior (inicialmente oculta)
        self.comparacao_group = QGroupBox("Comparação com Ano Anterior")
        comparacao_layout = QVBoxLayout()
        self.tabela_comparacao = self.criar_tabela_comparacao()
        comparacao_layout.addWidget(self.tabela_comparacao)
        self.comparacao_group.setLayout(comparacao_layout)
        self.comparacao_group.setVisible(False)
        layout.addWidget(self.comparacao_group)
        
        # Carregar dados
        self.carregar_orcamentos()
    
    def criar_tabela_consolidacao(self):
        """Cria tabela de consolidação anual"""
        tabela = QTableWidget()
        tabela.setColumnCount(5)
        tabela.setHorizontalHeaderLabels([
            "Categoria", "Total Planejado", "Total Realizado", 
            "Diferença", "% Execução"
        ])
        tabela.horizontalHeader().setStretchLastSection(True)
        tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return tabela
    
    def criar_tabela_comparacao(self):
        """Cria tabela de comparação com ano anterior"""
        tabela = QTableWidget()
        tabela.setColumnCount(5)
        tabela.setHorizontalHeaderLabels([
            "Categoria", "Ano Anterior", "Ano Atual", 
            "Variação (R$)", "Variação (%)"
        ])
        tabela.horizontalHeader().setStretchLastSection(True)
        tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return tabela
    
    def criar_painel_metricas(self, layout):
        """Cria painel de métricas principais"""
        metricas_group = QGroupBox("Métricas do Ano")
        metricas_layout = QHBoxLayout()
        
        self.lbl_total_receitas_plan = QLabel("Receitas Planejadas: R$ 0,00")
        self.lbl_total_receitas_real = QLabel("Receitas Realizadas: R$ 0,00")
        self.lbl_total_despesas_plan = QLabel("Despesas Planejadas: R$ 0,00")
        self.lbl_total_despesas_real = QLabel("Despesas Realizadas: R$ 0,00")
        self.lbl_saldo_plan = QLabel("Saldo Planejado: R$ 0,00")
        self.lbl_saldo_real = QLabel("Saldo Realizado: R$ 0,00")
        
        metricas_layout.addWidget(self.lbl_total_receitas_plan)
        metricas_layout.addWidget(self.lbl_total_receitas_real)
        metricas_layout.addWidget(self.lbl_total_despesas_plan)
        metricas_layout.addWidget(self.lbl_total_despesas_real)
        metricas_layout.addWidget(self.lbl_saldo_plan)
        metricas_layout.addWidget(self.lbl_saldo_real)
        
        metricas_group.setLayout(metricas_layout)
        layout.addWidget(metricas_group)
        
        # Painel de melhor/pior mês
        desempenho_group = QGroupBox("Desempenho Mensal")
        desempenho_layout = QHBoxLayout()
        
        self.lbl_melhor_mes = QLabel("Melhor Mês: -")
        self.lbl_pior_mes = QLabel("Pior Mês: -")
        self.lbl_percentual_geral = QLabel("Execução Geral: 0%")
        
        desempenho_layout.addWidget(self.lbl_melhor_mes)
        desempenho_layout.addWidget(self.lbl_pior_mes)
        desempenho_layout.addWidget(self.lbl_percentual_geral)
        desempenho_layout.addStretch()
        
        desempenho_group.setLayout(desempenho_layout)
        layout.addWidget(desempenho_group)
    
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
            # Obter categorias
            categorias = obter_categorias()
            categorias_receitas = [c for c in categorias if c['tipo'] == 'receita']
            categorias_despesas = [c for c in categorias if c['tipo'] == 'despesa']
            
            # Obter totais por categoria
            totais = calcular_totais_categorias(self.orcamento_id_atual)
            
            # Preencher tabela de consolidação
            self.preencher_tabela_consolidacao(
                categorias_receitas, categorias_despesas, totais
            )
            
            # Atualizar métricas
            self.atualizar_metricas(totais, categorias)
            
            # Atualizar desempenho mensal
            self.atualizar_desempenho()
            
            # Comparação com ano anterior (se habilitado)
            if self.chk_comparar_ano_anterior.isChecked():
                self.carregar_comparacao_ano_anterior()
                self.comparacao_group.setVisible(True)
            else:
                self.comparacao_group.setVisible(False)
            
        except Exception as e:
            logger.error(f"Erro ao carregar relatório: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório: {str(e)}")
    
    def preencher_tabela_consolidacao(self, categorias_receitas, 
                                     categorias_despesas, totais):
        """Preenche tabela de consolidação"""
        self.tabela_consolidacao.setRowCount(0)
        
        # Receitas
        for cat in categorias_receitas:
            self.adicionar_linha_consolidacao(cat, totais)
        
        # Linha separadora
        if categorias_receitas and categorias_despesas:
            row = self.tabela_consolidacao.rowCount()
            self.tabela_consolidacao.insertRow(row)
            item = QTableWidgetItem("─" * 50)
            item.setForeground(QColor(100, 100, 100))
            self.tabela_consolidacao.setItem(row, 0, item)
        
        # Despesas
        for cat in categorias_despesas:
            self.adicionar_linha_consolidacao(cat, totais)
    
    def adicionar_linha_consolidacao(self, categoria, totais):
        """Adiciona uma linha na tabela de consolidação"""
        cat_id = categoria['id']
        
        if cat_id not in totais:
            return
        
        dados = totais[cat_id]
        planejado = dados['planejado']
        realizado = dados['realizado']
        diferenca = dados['diferenca']
        percentual = dados['percentual']
        
        row = self.tabela_consolidacao.rowCount()
        self.tabela_consolidacao.insertRow(row)
        
        self.tabela_consolidacao.setItem(row, 0, QTableWidgetItem(categoria['nome']))
        self.tabela_consolidacao.setItem(row, 1, QTableWidgetItem(f"R$ {planejado:,.2f}"))
        self.tabela_consolidacao.setItem(row, 2, QTableWidgetItem(f"R$ {realizado:,.2f}"))
        
        item_dif = QTableWidgetItem(f"R$ {diferenca:,.2f}")
        if diferenca < 0:
            item_dif.setForeground(QColor(220, 53, 69))
        elif diferenca > 0:
            item_dif.setForeground(QColor(34, 139, 34))
        self.tabela_consolidacao.setItem(row, 3, item_dif)
        
        item_perc = QTableWidgetItem(f"{percentual:.1f}%")
        if categoria['tipo'] == 'despesa':
            if percentual > 100:
                item_perc.setForeground(QColor(220, 53, 69))
            elif percentual > 80:
                item_perc.setForeground(QColor(255, 193, 7))
        else:  # receita
            if percentual < 50:
                item_perc.setForeground(QColor(220, 53, 69))
            elif percentual < 80:
                item_perc.setForeground(QColor(255, 193, 7))
        self.tabela_consolidacao.setItem(row, 4, item_perc)
    
    def atualizar_metricas(self, totais, categorias):
        """Atualiza painel de métricas"""
        total_receitas_plan = 0
        total_receitas_real = 0
        total_despesas_plan = 0
        total_despesas_real = 0
        
        for cat in categorias:
            cat_id = cat['id']
            if cat_id in totais:
                if cat['tipo'] == 'receita':
                    total_receitas_plan += totais[cat_id]['planejado']
                    total_receitas_real += totais[cat_id]['realizado']
                else:
                    total_despesas_plan += totais[cat_id]['planejado']
                    total_despesas_real += totais[cat_id]['realizado']
        
        saldo_plan = total_receitas_plan - total_despesas_plan
        saldo_real = total_receitas_real - total_despesas_real
        
        self.lbl_total_receitas_plan.setText(f"Receitas Planejadas: R$ {total_receitas_plan:,.2f}")
        self.lbl_total_receitas_real.setText(f"Receitas Realizadas: R$ {total_receitas_real:,.2f}")
        self.lbl_total_despesas_plan.setText(f"Despesas Planejadas: R$ {total_despesas_plan:,.2f}")
        self.lbl_total_despesas_real.setText(f"Despesas Realizadas: R$ {total_despesas_real:,.2f}")
        self.lbl_saldo_plan.setText(f"Saldo Planejado: R$ {saldo_plan:,.2f}")
        self.lbl_saldo_real.setText(f"Saldo Realizado: R$ {saldo_real:,.2f}")
    
    def atualizar_desempenho(self):
        """Atualiza informações de desempenho mensal"""
        try:
            calculator = OrcamentoCalculator(self.orcamento_id_atual)
            
            # Percentual de execução geral
            percentual = calculator.calcular_percentual_execucao_geral()
            self.lbl_percentual_geral.setText(f"Execução Geral: {percentual:.1f}%")
            
            # Melhor e pior mês
            melhor_mes, pior_mes = calculator.identificar_melhor_pior_mes()
            
            meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            
            if melhor_mes and 1 <= melhor_mes <= 12:
                self.lbl_melhor_mes.setText(f"Melhor Mês: {meses[melhor_mes]}")
                self.lbl_melhor_mes.setStyleSheet("color: #28a745; font-weight: bold;")
            else:
                self.lbl_melhor_mes.setText("Melhor Mês: -")
            
            if pior_mes and 1 <= pior_mes <= 12:
                self.lbl_pior_mes.setText(f"Pior Mês: {meses[pior_mes]}")
                self.lbl_pior_mes.setStyleSheet("color: #dc3545; font-weight: bold;")
            else:
                self.lbl_pior_mes.setText("Pior Mês: -")
                
        except Exception as e:
            logger.error(f"Erro ao atualizar desempenho: {e}")
    
    def carregar_comparacao_ano_anterior(self):
        """Carrega comparação com ano anterior"""
        try:
            # Obter ano do orçamento atual
            orcamento = obter_orcamento(self.orcamento_id_atual)
            if not orcamento:
                return
            
            ano_atual = orcamento['ano']
            ano_anterior = ano_atual - 1
            
            # Calcular variações
            calculator = OrcamentoCalculator(self.orcamento_id_atual)
            variacoes = calculator.calcular_variacao_ano_anterior(ano_anterior)
            
            if not variacoes:
                self.tabela_comparacao.setRowCount(1)
                self.tabela_comparacao.setItem(0, 0, 
                    QTableWidgetItem(f"Orçamento do ano {ano_anterior} não encontrado"))
                return
            
            # Obter categorias e totais
            categorias = obter_categorias()
            totais_atual = calcular_totais_categorias(self.orcamento_id_atual)
            
            # Preencher tabela
            self.tabela_comparacao.setRowCount(0)
            
            for cat in categorias:
                cat_id = cat['id']
                
                if cat_id not in variacoes or cat_id not in totais_atual:
                    continue
                
                variacao_planejado = variacoes[cat_id]['variacao_planejado']
                valor_atual = totais_atual[cat_id]['planejado']
                
                # Calcular valor do ano anterior
                if variacao_planejado == 0:
                    valor_anterior = valor_atual
                else:
                    valor_anterior = valor_atual / (1 + variacao_planejado / 100)
                
                variacao_valor = valor_atual - valor_anterior
                
                row = self.tabela_comparacao.rowCount()
                self.tabela_comparacao.insertRow(row)
                
                self.tabela_comparacao.setItem(row, 0, QTableWidgetItem(cat['nome']))
                self.tabela_comparacao.setItem(row, 1, QTableWidgetItem(f"R$ {valor_anterior:,.2f}"))
                self.tabela_comparacao.setItem(row, 2, QTableWidgetItem(f"R$ {valor_atual:,.2f}"))
                
                item_var_valor = QTableWidgetItem(f"R$ {variacao_valor:,.2f}")
                if variacao_valor < 0:
                    item_var_valor.setForeground(QColor(220, 53, 69))
                elif variacao_valor > 0:
                    item_var_valor.setForeground(QColor(34, 139, 34))
                self.tabela_comparacao.setItem(row, 3, item_var_valor)
                
                item_var_perc = QTableWidgetItem(f"{variacao_planejado:+.1f}%")
                if variacao_planejado < 0:
                    item_var_perc.setForeground(QColor(220, 53, 69))
                elif variacao_planejado > 0:
                    item_var_perc.setForeground(QColor(34, 139, 34))
                self.tabela_comparacao.setItem(row, 4, item_var_perc)
                
        except Exception as e:
            logger.error(f"Erro ao carregar comparação: {e}")
    
    def exportar_csv(self):
        """Exporta relatório para CSV"""
        if not self.orcamento_id_atual:
            QMessageBox.warning(self, "Aviso", "Selecione um orçamento primeiro.")
            return
        
        try:
            # Solicitar local de salvamento
            ano = self.combo_orcamento.currentText().split()[-1]
            nome_arquivo = f"relatorio_anual_{ano}.csv"
            
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
                writer.writerow([f"Relatório Anual de Orçamento - {ano}"])
                writer.writerow([f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
                writer.writerow([])
                
                # Métricas
                writer.writerow(["MÉTRICAS DO ANO"])
                writer.writerow([self.lbl_total_receitas_plan.text()])
                writer.writerow([self.lbl_total_receitas_real.text()])
                writer.writerow([self.lbl_total_despesas_plan.text()])
                writer.writerow([self.lbl_total_despesas_real.text()])
                writer.writerow([self.lbl_saldo_plan.text()])
                writer.writerow([self.lbl_saldo_real.text()])
                writer.writerow([])
                
                # Desempenho
                writer.writerow(["DESEMPENHO MENSAL"])
                writer.writerow([self.lbl_melhor_mes.text()])
                writer.writerow([self.lbl_pior_mes.text()])
                writer.writerow([self.lbl_percentual_geral.text()])
                writer.writerow([])
                
                # Consolidação
                writer.writerow(["CONSOLIDAÇÃO ANUAL POR CATEGORIA"])
                writer.writerow(["Categoria", "Total Planejado", "Total Realizado", 
                               "Diferença", "% Execução"])
                
                for row in range(self.tabela_consolidacao.rowCount()):
                    linha = []
                    for col in range(5):
                        item = self.tabela_consolidacao.item(row, col)
                        linha.append(item.text() if item else "")
                    writer.writerow(linha)
                
                # Comparação (se habilitada)
                if self.chk_comparar_ano_anterior.isChecked():
                    writer.writerow([])
                    writer.writerow(["COMPARAÇÃO COM ANO ANTERIOR"])
                    writer.writerow(["Categoria", "Ano Anterior", "Ano Atual", 
                                   "Variação (R$)", "Variação (%)"])
                    
                    for row in range(self.tabela_comparacao.rowCount()):
                        linha = []
                        for col in range(5):
                            item = self.tabela_comparacao.item(row, col)
                            linha.append(item.text() if item else "")
                        writer.writerow(linha)
            
            QMessageBox.information(self, "Sucesso", f"Relatório exportado para:\n{caminho}")
            logger.info(f"Relatório anual exportado: {caminho}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {str(e)}")
    
    def exportar_pdf(self):
        """Exporta relatório anual para PDF"""
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
            nome_arquivo = f"relatorio_anual_{ano}.pdf"
            
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
                f"Relatório Anual de Orçamento - {ano}",
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
            
            # Métricas do Ano
            elementos.append(Paragraph("MÉTRICAS DO ANO", styles['Heading2']))
            elementos.append(Spacer(1, 0.3*cm))
            
            metricas_style = ParagraphStyle(
                'MetricasStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=4
            )
            
            elementos.append(Paragraph(self.lbl_total_receitas_plan.text(), metricas_style))
            elementos.append(Paragraph(self.lbl_total_receitas_real.text(), metricas_style))
            elementos.append(Paragraph(self.lbl_total_despesas_plan.text(), metricas_style))
            elementos.append(Paragraph(self.lbl_total_despesas_real.text(), metricas_style))
            elementos.append(Paragraph(self.lbl_saldo_plan.text(), metricas_style))
            elementos.append(Paragraph(self.lbl_saldo_real.text(), metricas_style))
            elementos.append(Spacer(1, 0.5*cm))
            
            # Desempenho Mensal
            elementos.append(Paragraph("DESEMPENHO MENSAL", styles['Heading2']))
            elementos.append(Spacer(1, 0.3*cm))
            
            elementos.append(Paragraph(self.lbl_melhor_mes.text(), metricas_style))
            elementos.append(Paragraph(self.lbl_pior_mes.text(), metricas_style))
            elementos.append(Paragraph(self.lbl_percentual_geral.text(), metricas_style))
            elementos.append(Spacer(1, 0.5*cm))
            
            # Tabela de Consolidação
            elementos.append(Paragraph("CONSOLIDAÇÃO ANUAL POR CATEGORIA", styles['Heading2']))
            elementos.append(Spacer(1, 0.3*cm))
            
            dados_consolidacao = [["Categoria", "Total Planejado", "Total Realizado", "Diferença", "% Execução"]]
            for row in range(self.tabela_consolidacao.rowCount()):
                linha = []
                for col in range(5):
                    item = self.tabela_consolidacao.item(row, col)
                    texto = item.text() if item else ""
                    # Pular linhas separadoras
                    if texto.startswith("─"):
                        continue
                    linha.append(texto)
                if len(linha) == 5:  # Apenas adicionar linhas completas
                    dados_consolidacao.append(linha)
            
            tabela_consolidacao = Table(dados_consolidacao, colWidths=[6*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
            tabela_consolidacao.setStyle(TableStyle([
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
            elementos.append(tabela_consolidacao)
            
            # Comparação com ano anterior (se habilitada)
            if self.chk_comparar_ano_anterior.isChecked() and self.tabela_comparacao.rowCount() > 0:
                elementos.append(PageBreak())
                elementos.append(Paragraph("COMPARAÇÃO COM ANO ANTERIOR", styles['Heading2']))
                elementos.append(Spacer(1, 0.3*cm))
                
                dados_comparacao = [["Categoria", "Ano Anterior", "Ano Atual", "Variação (R$)", "Variação (%)"]]
                for row in range(self.tabela_comparacao.rowCount()):
                    linha = []
                    for col in range(5):
                        item = self.tabela_comparacao.item(row, col)
                        linha.append(item.text() if item else "")
                    dados_comparacao.append(linha)
                
                tabela_comparacao = Table(dados_comparacao, colWidths=[6*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
                tabela_comparacao.setStyle(TableStyle([
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
                elementos.append(tabela_comparacao)
            
            # Gerar PDF
            doc.build(elementos)
            
            QMessageBox.information(self, "Sucesso", f"Relatório PDF exportado para:\n{caminho}")
            logger.info(f"Relatório anual PDF exportado: {caminho}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar PDF: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")
    
    def atualizar(self):
        """Método para atualizar dados"""
        self.carregar_orcamentos()
