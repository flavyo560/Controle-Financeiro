from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from database.db import conectar
from datetime import datetime


class RelatorioVeiculo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Relatório de Custo do Veículo")
        self.resize(900, 650)
        self.setStyleSheet("background-color: #0b0b0b; color: white;")

        layout = QVBoxLayout(self)

        # ---------- FILTRO ----------
        filtro = QHBoxLayout()
        
        # Novo Seletor de Veículo
        self.combo_veiculo = QComboBox()
        self.combo_veiculo.setStyleSheet("background-color: #1a1a1a; color: #00ffa3; padding: 5px;")
        
        self.combo_mes = QComboBox()
        self.combo_ano = QComboBox()

        for m in range(1, 13):
            self.combo_mes.addItem(f"{m:02d}")

        ano_atual = datetime.now().year
        for a in range(ano_atual - 5, ano_atual + 1):
            self.combo_ano.addItem(str(a))

        btn_gerar = QPushButton("📊 Gerar Relatório")
        btn_gerar.setStyleSheet("background-color: #00ffa3; color: black; font-weight: bold; padding: 5px 15px;")
        btn_gerar.clicked.connect(self.gerar_relatorio)

        filtro.addWidget(QLabel("Veículo:"))
        filtro.addWidget(self.combo_veiculo)
        filtro.addWidget(QLabel("Mês:"))
        filtro.addWidget(self.combo_mes)
        filtro.addWidget(QLabel("Ano:"))
        filtro.addWidget(self.combo_ano)
        filtro.addWidget(btn_gerar)

        layout.addLayout(filtro)

        # ---------- CARDS DE INFORMAÇÃO ----------
        cards_layout = QHBoxLayout()
        
        self.lbl_comb = QLabel("⛽ Combustível\nR$ 0,00")
        self.lbl_manut = QLabel("🔧 Manutenção\nR$ 0,00")
        self.lbl_total = QLabel("💸 Custo Total\nR$ 0,00")
        self.lbl_km = QLabel("📏 Km Rodados\n0 km")
        self.lbl_custo_km = QLabel("💰 Custo/Km\nR$ 0,00")

        for lbl in (self.lbl_comb, self.lbl_manut, self.lbl_total, self.lbl_km, self.lbl_custo_km):
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                background-color: #161616; 
                border: 1px solid #333; 
                border-radius: 8px; 
                padding: 15px; 
                font-size: 13px;
                font-weight: bold;
            """)
            cards_layout.addWidget(lbl)
        
        layout.addLayout(cards_layout)

        # ---------- GRÁFICO ----------
        self.fig = Figure(figsize=(5, 4), facecolor='#0b0b0b')
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.atualizar() # Carrega os veículos ao iniciar

    def atualizar(self):
        """Atualiza a lista de veículos disponível no ComboBox"""
        try:
            self.combo_veiculo.clear()
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome_identificador FROM veiculos WHERE status = 1")
            veiculos = cur.fetchall()
            for id_v, nome in veiculos:
                self.combo_veiculo.addItem(nome, id_v)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar veículos no relatório: {e}")

    def gerar_relatorio(self):
        # Pega o ID do veículo selecionado (armazenado no userData do combo)
        veiculo_id = self.combo_veiculo.currentData()
        
        if not veiculo_id:
            return

        mes = self.combo_mes.currentText()
        ano = self.combo_ano.currentText()
        ref = f"{ano}-{mes}"

        total_comb = self.total_combustivel(ref, veiculo_id)
        total_manut = self.total_manutencao(ref, veiculo_id)
        km_rodados = self.km_rodados_mes(ref, veiculo_id)

        custo_total = total_comb + total_manut
        custo_km = (custo_total / km_rodados) if km_rodados > 0 else 0

        self.lbl_comb.setText(f"⛽ Combustível\nR$ {total_comb:,.2f}")
        self.lbl_manut.setText(f"🔧 Manutenção\nR$ {total_manut:,.2f}")
        self.lbl_total.setText(f"💸 Custo Total\nR$ {custo_total:,.2f}")
        self.lbl_km.setText(f"📏 Km Rodados\n{km_rodados} km")
        self.lbl_custo_km.setText(f"💰 Custo/Km\nR$ {custo_km:,.2f}")

        self.atualizar_grafico(total_comb, total_manut)

    def total_combustivel(self, ref, veiculo_id):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM abastecimentos
            WHERE strftime('%Y-%m', data) = ? AND veiculo_id = ?
        """, (ref, veiculo_id))
        total = cur.fetchone()[0]
        conn.close()
        return total

    def total_manutencao(self, ref, veiculo_id):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM manutencoes
            WHERE strftime('%Y-%m', data) = ? AND veiculo_id = ?
        """, (ref, veiculo_id))
        total = cur.fetchone()[0]
        conn.close()
        return total

    def km_rodados_mes(self, ref, veiculo_id):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT MIN(km), MAX(km)
            FROM abastecimentos
            WHERE strftime('%Y-%m', data) = ? AND veiculo_id = ?
        """, (ref, veiculo_id))
        min_km, max_km = cur.fetchone()
        conn.close()

        if min_km is None or max_km is None:
            return 0
        return max_km - min_km

    def atualizar_grafico(self, combustivel, manutencao):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#161616')
        
        labels = ["Combustível", "Manutenção"]
        valores = [combustivel, manutencao]
        cores = ['#00ffa3', '#ff4757']
        
        bars = ax.bar(labels, valores, color=cores)
        ax.set_title("Divisão de Custos do Mês", color='white', fontweight='bold')
        ax.tick_params(colors='white')
        
        # Adicionar valores em cima das barras
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval, f'R${yval:,.2f}', 
                    va='bottom', ha='center', color='white', fontsize=9)

        self.canvas.draw()

# Importação do Qt para alinhamento
from PyQt6.QtCore import Qt