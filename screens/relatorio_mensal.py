from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from database.db import conectar
from datetime import datetime
import calendar

# Imports para Exportação
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

class RelatorioMensal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Extrato Mensal Detalhado")
        self.resize(1000, 800)
        self.setStyleSheet("background-color: #0b0b0b; color: white;")
        self.dados_extrato = []

        layout = QVBoxLayout(self)

        # ---------- FILTROS ----------
        filtro = QHBoxLayout()
        self.combo_mes = QComboBox()
        self.combo_ano = QComboBox()
        estilo_combo = "background-color: #1a1a1a; color: white; border: 1px solid #333; padding: 5px;"
        self.combo_mes.setStyleSheet(estilo_combo)
        self.combo_ano.setStyleSheet(estilo_combo)

        for m in range(1, 13): self.combo_mes.addItem(f"{m:02d}")
        ano_at = datetime.now().year
        for a in range(ano_at - 5, ano_at + 1): self.combo_ano.addItem(str(a))

        btn_gerar = QPushButton("📊 Gerar Extrato")
        btn_gerar.setStyleSheet("background-color: #00ffa3; color: black; font-weight: bold; padding: 8px;")
        btn_gerar.clicked.connect(self.gerar_relatorio)

        self.btn_pdf = QPushButton("📕 PDF")
        self.btn_excel = QPushButton("📗 Excel")
        self.btn_pdf.setStyleSheet("background-color: #ff4757; color: white; font-weight: bold; padding: 8px;")
        self.btn_excel.setStyleSheet("background-color: #2ed573; color: white; font-weight: bold; padding: 8px;")
        
        self.btn_pdf.clicked.connect(self.exportar_pdf)
        self.btn_excel.clicked.connect(self.exportar_excel)

        filtro.addWidget(QLabel("Mês:"))
        filtro.addWidget(self.combo_mes)
        filtro.addWidget(QLabel("Ano:"))
        filtro.addWidget(self.combo_ano)
        filtro.addWidget(btn_gerar)
        filtro.addWidget(self.btn_pdf)
        filtro.addWidget(self.btn_excel)
        layout.addLayout(filtro)

        # ---------- GRÁFICO DE DUAS LINHAS (IGUAL ANUAL) ----------
        self.figura = Figure(figsize=(5, 4), facecolor='#0b0b0b')
        self.canvas = FigureCanvas(self.figura)
        layout.addWidget(self.canvas)

        # ---------- TABELA DE EXTRATO ----------
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Data", "Descrição", "Tipo", "Valor"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setStyleSheet("""
            QTableWidget { background-color: #121212; color: white; gridline-color: #333; border: none; }
            QHeaderView::section { background-color: #1a1a1a; color: #00ffa3; font-weight: bold; }
        """)
        layout.addWidget(self.tabela)

    def gerar_relatorio(self):
        mes_sel = self.combo_mes.currentText()
        ano_sel = self.combo_ano.currentText()
        ref = f"{ano_sel}-{mes_sel}"
        
        conn = conectar(); cur = conn.cursor()
        
        # 1. Dados da Tabela (Extrato)
        query = """
            SELECT data, descricao, 'Receita' as tipo, valor FROM receitas WHERE strftime('%Y-%m', data) = ?
            UNION ALL
            SELECT data, descricao, 'Despesa' as tipo, valor FROM despesas WHERE strftime('%Y-%m', data) = ?
            ORDER BY data ASC
        """
        cur.execute(query, (ref, ref))
        self.dados_extrato = cur.fetchall()

        # 2. Dados para o Gráfico (Evolução Diária)
        ultimo_dia = calendar.monthrange(int(ano_sel), int(mes_sel))[1]
        dias = list(range(1, ultimo_dia + 1))
        recs_diarias = []
        desps_diarias = []
        
        for dia in dias:
            data_loop = f"{ref}-{dia:02d}"
            cur.execute("SELECT COALESCE(SUM(valor),0) FROM receitas WHERE data = ?", (data_loop,))
            recs_diarias.append(cur.fetchone()[0] or 0)
            cur.execute("SELECT COALESCE(SUM(valor),0) FROM despesas WHERE data = ?", (data_loop,))
            desps_diarias.append(cur.fetchone()[0] or 0)
        
        conn.close()

        # --- Atualizar Tabela ---
        self.tabela.setRowCount(0)
        for row_idx, row_data in enumerate(self.dados_extrato):
            self.tabela.insertRow(row_idx)
            for col_idx, valor in enumerate(row_data):
                texto = f"R$ {valor:,.2f}" if col_idx == 3 else str(valor)
                item = QTableWidgetItem(texto)
                if col_idx == 3:
                    item.setForeground(QColor("#00ffa3") if row_data[2] == 'Receita' else QColor("#ff4757"))
                self.tabela.setItem(row_idx, col_idx, item)

        # --- Atualizar Gráfico (Duas Linhas: Verde e Vermelha) ---
        self.figura.clear()
        ax = self.figura.add_subplot(111); ax.set_facecolor('#0b0b0b')
        
        # Linha de Receitas (Verde) e Despesas (Vermelha)
        ax.plot(dias, recs_diarias, color='#00ffa3', marker='o', markersize=3, linewidth=2, label='Receitas')
        ax.plot(dias, desps_diarias, color='#ff4757', marker='o', markersize=3, linewidth=2, label='Despesas')
        
        ax.tick_params(colors='white')
        ax.set_title(f"FLUXO DIÁRIO - {mes_sel}/{ano_sel}", color="white", fontweight='bold')
        ax.set_xlabel("Dia", color="white")
        ax.legend(facecolor='#1a1a1a', labelcolor='white')
        ax.grid(True, color='#222', linestyle='--', alpha=0.5)
        
        for spine in ax.spines.values(): spine.set_color('#333')
        self.canvas.draw()

    def exportar_pdf(self):
        if not self.dados_extrato:
            QMessageBox.warning(self, "Aviso", "Gere o extrato antes de exportar!")
            return
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Extrato", f"Extrato_{self.combo_mes.currentText()}_{self.combo_ano.currentText()}.pdf", "PDF Files (*.pdf)")
        if not caminho: return

        doc = SimpleDocTemplate(caminho, pagesize=A4)
        elementos = []
        estilos = getSampleStyleSheet()
        titulo = Paragraph(f"Extrato Financeiro - {self.combo_mes.currentText()}/{self.combo_ano.currentText()}", estilos['Title'])
        elementos.append(titulo); elementos.append(Spacer(1, 12))

        dados_pdf = [["Data", "Descrição", "Tipo", "Valor"]]
        for d in self.dados_extrato:
            dados_pdf.append([d[0], d[1], d[2], f"R$ {d[3]:,.2f}"])

        t = Table(dados_pdf, colWidths=[80, 250, 80, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a1a1a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#00ffa3")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        for i, row in enumerate(self.dados_extrato):
            cor = colors.green if row[2] == 'Receita' else colors.red
            t.setStyle(TableStyle([('TEXTCOLOR', (3, i+1), (3, i+1), cor)]))

        elementos.append(t)
        doc.build(elementos)
        QMessageBox.information(self, "Sucesso", "PDF exportado!")

    def exportar_excel(self):
        if not self.dados_extrato:
            QMessageBox.warning(self, "Aviso", "Gere o extrato antes de exportar!")
            return
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Extrato", f"Extrato_{self.combo_mes.currentText()}_{self.combo_ano.currentText()}.xlsx", "Excel Files (*.xlsx)")
        if not caminho: return

        wb = Workbook(); ws = wb.active
        ws.title = "Extrato Mensal"
        ws.append(["Data", "Descrição", "Tipo", "Valor"])
        for d in self.dados_extrato: ws.append([d[0], d[1], d[2], d[3]])
        wb.save(caminho)
        QMessageBox.information(self, "Sucesso", "Excel exportado!")