from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QComboBox
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from database.db import conectar
from datetime import datetime

class AnaliseInvestimentos(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #0b0b0b;") 
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(25, 25, 25, 25)
        
        self.renderizar_ui()

    def renderizar_ui(self):
        # Limpar layout para re-renderizar se necessário
        while self.layout_principal.count():
            item = self.layout_principal.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

        # Título
        titulo = QLabel("ANÁLISE DE INVESTIMENTOS")
        titulo.setStyleSheet("color: #00ffa3; font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        self.layout_principal.addWidget(titulo)

        # Filtro de Ano
        filtro_layout = QHBoxLayout()
        self.combo_ano = QComboBox()
        self.combo_ano.setStyleSheet("background-color: #121212; color: white; border: 1px solid #2d2d2d; padding: 5px;")
        ano_atual = datetime.now().year
        for a in range(ano_atual - 5, ano_atual + 1):
            self.combo_ano.addItem(str(a))
        self.combo_ano.setCurrentText(str(ano_atual))
        self.combo_ano.currentTextChanged.connect(self.carregar_dados)
        
        filtro_layout.addWidget(QLabel("Ano de Evolução:"))
        filtro_layout.addWidget(self.combo_ano)
        filtro_layout.addStretch()
        self.layout_principal.addLayout(filtro_layout)

        # Container do Gráfico
        frame_graficos = QFrame()
        frame_graficos.setStyleSheet("background-color: #121212; border-radius: 20px; border: 1px solid #1f1f1f;")
        layout_v = QVBoxLayout(frame_graficos)

        # Configuração do Matplotlib para o tema Dark
        plt.rcParams.update({'text.color': 'white', 'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white'})
        
        # Criamos apenas um subplot grande para a linha de evolução
        self.fig, self.ax = plt.subplots(figsize=(12, 7))
        self.fig.patch.set_facecolor('#121212')
        self.ax.set_facecolor('#121212')
        
        for spine in self.ax.spines.values(): 
            spine.set_edgecolor('#2d2d2d')

        self.canvas = FigureCanvas(self.fig)
        layout_v.addWidget(self.canvas)
        self.layout_principal.addWidget(frame_graficos)
        
        self.carregar_dados()

    def carregar_dados(self):
        self.ax.clear()
        ano = self.combo_ano.currentText()
        meses_labels = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
        valores_patrimonio = []

        conn = conectar()
        cur = conn.cursor()

        # Lógica para calcular a evolução do patrimônio mês a mês
        for i in range(1, 13):
            # Data limite é o último dia do mês corrente no loop
            data_limite = f"{ano}-{i:02d}-31"
            
            # Buscamos a soma do valor_atual de todos os ativos comprados até essa data
            # Nota: Ajuste os nomes das colunas 'valor_atual' e 'data_compra' se forem diferentes no seu banco
            try:
                cur.execute("SELECT SUM(valor_atual) FROM investimentos WHERE data_compra <= ?", (data_limite,))
                total = cur.fetchone()[0] or 0
                valores_patrimonio.append(total)
            except:
                valores_patrimonio.append(0)

        conn.close()

        # Desenhar a linha Neon (Estilo o Anual/Mensal que fizemos)
        self.ax.plot(meses_labels, valores_patrimonio, color='#00ffa3', marker='o', markersize=8, linewidth=4, label='Patrimônio Acumulado')
        
        # Sombra neon abaixo da linha
        self.ax.fill_between(meses_labels, valores_patrimonio, color='#00ffa3', alpha=0.15)

        # Títulos e Grids
        self.ax.set_title(f"EVOLUÇÃO DO PATRIMÔNIO EM {ano}", fontsize=15, fontweight='bold', color='#00ffa3', pad=20)
        self.ax.grid(True, color='#2d2d2d', linestyle='--', alpha=0.5)
        
        # Ajuste de layout e refresh
        self.fig.tight_layout()
        self.canvas.draw()