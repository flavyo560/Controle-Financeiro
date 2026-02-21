from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from database.db import conectar
from datetime import datetime

class RelatorioAnual(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Análise Anual de Evolução")
        self.resize(1000, 600)
        self.setStyleSheet("background-color: #0b0b0b; color: white;")

        layout = QVBoxLayout(self)
        
        topo = QHBoxLayout()
        self.combo_ano = QComboBox()
        self.combo_ano.setStyleSheet("background-color: #1a1a1a; color: white; padding: 5px;")
        ano_at = datetime.now().year
        for a in range(ano_at - 5, ano_at + 1): self.combo_ano.addItem(str(a))
        
        btn = QPushButton("📈 Ver Gráfico de Evolução")
        btn.setStyleSheet("background-color: #00ffa3; color: black; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self.gerar_relatorio)
        
        topo.addWidget(QLabel("Ano:"))
        topo.addWidget(self.combo_ano)
        topo.addWidget(btn)
        topo.addStretch()
        layout.addLayout(topo)

        self.figura = Figure(figsize=(10, 6), facecolor='#0b0b0b')
        self.canvas = FigureCanvas(self.figura)
        layout.addWidget(self.canvas)

    def gerar_relatorio(self):
        ano = self.combo_ano.currentText()
        meses_labels = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
        recs, desps = [], []

        conn = conectar(); cur = conn.cursor()
        for i in range(1, 13):
            ref = f"{ano}-{i:02d}"
            cur.execute("SELECT SUM(valor) FROM receitas WHERE strftime('%Y-%m', data) = ?", (ref,))
            recs.append(cur.fetchone()[0] or 0)
            cur.execute("SELECT SUM(valor) FROM despesas WHERE strftime('%Y-%m', data) = ?", (ref,))
            desps.append(cur.fetchone()[0] or 0)
        conn.close()

        self.figura.clear()
        ax = self.figura.add_subplot(111); ax.set_facecolor('#0b0b0b')
        
        # Duas linhas: Receitas (Verde) e Despesas (Vermelho)
        ax.plot(meses_labels, recs, marker='o', color='#00ffa3', linewidth=3, label='Receitas')
        ax.plot(meses_labels, desps, marker='o', color='#ff4757', linewidth=3, label='Despesas')
        
        ax.tick_params(colors='white')
        ax.set_title(f"FLUXO DE CAIXA ANUAL - {ano}", color="#00ffa3", fontsize=14, fontweight='bold')
        ax.legend(facecolor='#1a1a1a', labelcolor='white')
        ax.grid(True, color='#222', linestyle='--', alpha=0.5)
        
        for spine in ax.spines.values():
            spine.set_color('#333')
        
        self.canvas.draw()