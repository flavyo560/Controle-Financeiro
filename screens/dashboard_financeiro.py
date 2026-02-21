from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QComboBox, QPushButton, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QDate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from database.db import conectar, calcular_saldo_banco

class DashboardFinanceiro(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(25, 20, 25, 20)
        self.layout_principal.setSpacing(15)

        # ---------- HEADER ----------
        header_layout = QHBoxLayout()
        self.label_titulo = QLabel("📊 DASHBOARD FINANCEIRO")
        self.label_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #00ffa3;")
        
        estilo_combo = "background-color: #1a1a1a; color: white; border: 1px solid #333; padding: 5px; border-radius: 4px;"
        self.combo_mes = QComboBox()
        self.combo_mes.addItems(["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
        self.combo_mes.setCurrentIndex(QDate.currentDate().month() - 1)
        self.combo_mes.setStyleSheet(estilo_combo)
        
        self.combo_ano = QComboBox()
        ano_at = QDate.currentDate().year()
        for a in range(ano_at - 5, ano_at + 2): self.combo_ano.addItem(str(a))
        self.combo_ano.setCurrentText(str(ano_at))
        self.combo_ano.setStyleSheet(estilo_combo)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.clicked.connect(self.atualizar)
        self.btn_filtrar.setStyleSheet("background-color: #00ffa3; color: black; font-weight: bold; padding: 6px 20px; border-radius: 4px;")

        header_layout.addWidget(self.label_titulo)
        header_layout.addStretch()
        header_layout.addWidget(self.combo_mes)
        header_layout.addWidget(self.combo_ano)
        header_layout.addWidget(self.btn_filtrar)
        self.layout_principal.addLayout(header_layout)

        # ---------- CARD PATRIMÔNIO (LARGURA TOTAL) ----------
        self.card_patrimonio = QFrame()
        self.card_patrimonio.setMinimumHeight(150)
        self.card_patrimonio.setStyleSheet("QFrame { background-color: #121212; border: 2px solid #333; border-radius: 15px; }")
        lay_patr = QVBoxLayout(self.card_patrimonio)
        
        lbl_p_tit = QLabel("PATRIMÔNIO TOTAL (ATIVO)")
        lbl_p_tit.setStyleSheet("color: #a4b0be; font-size: 14px; font-weight: bold; border: none;")
        self.lbl_patr_valor = QLabel("R$ 0,00")
        self.lbl_patr_valor.setStyleSheet("color: #00ffa3; font-size: 38px; font-weight: bold; border: none;")
        
        lay_patr.addWidget(lbl_p_tit, alignment=Qt.AlignmentFlag.AlignCenter)
        lay_patr.addWidget(self.lbl_patr_valor, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Área horizontal para os bancos
        self.area_bancos = QScrollArea()
        self.area_bancos.setWidgetResizable(True)
        self.area_bancos.setStyleSheet("border: none; background: transparent;")
        self.container_bancos = QWidget()
        self.layout_bancos_grid = QHBoxLayout(self.container_bancos)
        self.layout_bancos_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.area_bancos.setWidget(self.container_bancos)
        lay_patr.addWidget(self.area_bancos)
        
        self.layout_principal.addWidget(self.card_patrimonio)

        # ---------- GRID DE INDICADORES ----------
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        self.card_receitas = self.criar_card_mini("RECEITAS MÊS", "#2ecc71")
        self.card_despesas = self.criar_card_mini("DESPESAS MÊS", "#ff4757")
        self.card_investimentos = self.criar_card_mini("INVESTIMENTOS", "#1e90ff")
        self.card_dividendos = self.criar_card_mini("DIVIDENDOS", "#f1c40f")

        grid_layout.addWidget(self.card_receitas, 0, 0)
        grid_layout.addWidget(self.card_despesas, 0, 1)
        grid_layout.addWidget(self.card_investimentos, 0, 2)
        grid_layout.addWidget(self.card_dividendos, 0, 3)
        
        self.layout_principal.addLayout(grid_layout)

        # ---------- GRÁFICOS ----------
        container_graficos = QFrame()
        container_graficos.setStyleSheet("background-color: #0b0b0b; border-radius: 12px; border: 1px solid #252525;")
        self.layout_charts = QHBoxLayout(container_graficos) 

        plt.style.use('dark_background')
        self.fig_desp, self.ax_desp = plt.subplots(figsize=(5, 4))
        self.fig_desp.patch.set_facecolor('#0b0b0b')
        self.canvas_desp = FigureCanvas(self.fig_desp)
        
        self.fig_rec, self.ax_rec = plt.subplots(figsize=(5, 4))
        self.fig_rec.patch.set_facecolor('#0b0b0b')
        self.canvas_rec = FigureCanvas(self.fig_rec)

        self.layout_charts.addWidget(self.canvas_desp)
        self.layout_charts.addWidget(self.canvas_rec)
        self.layout_principal.addWidget(container_graficos)
        
        self.atualizar()

    def criar_card_mini(self, titulo, cor):
        card = QFrame()
        card.setFixedHeight(110)
        card.setStyleSheet("QFrame { background-color: #1a1a1a; border: 1px solid #333; border-radius: 10px; }")
        lay = QVBoxLayout(card)
        t = QLabel(titulo); t.setStyleSheet(f"color: {cor}; font-size: 11px; font-weight: bold; border: none;")
        v = QLabel("R$ 0,00"); v.setStyleSheet(f"color: white; font-size: 20px; font-weight: bold; border: none;")
        lay.addWidget(t, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(v, alignment=Qt.AlignmentFlag.AlignCenter)
        card.valor_label = v
        return card

    def atualizar(self):
        try:
            conn = conectar(); cur = conn.cursor()
            mes_idx = self.combo_mes.currentIndex() + 1
            ano = self.combo_ano.currentText()
            periodo = f"{ano}-{mes_idx:02d}"

            # 1. ATUALIZAR BANCOS NO PATRIMÔNIO (APENAS ATIVOS)
            for i in reversed(range(self.layout_bancos_grid.count())): 
                widget = self.layout_bancos_grid.itemAt(i).widget()
                if widget: widget.setParent(None)

            # FILTRO: status = 1
            cur.execute("SELECT id, nome FROM bancos WHERE status = 1 ORDER BY nome")
            bancos_ativos = cur.fetchall()
            total_geral = 0
            
            for b_id, nome in bancos_ativos:
                saldo = calcular_saldo_banco(b_id)
                total_geral += saldo
                lbl = QLabel(f"{nome}\nR$ {saldo:,.2f}")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("""
                    color: white; font-size: 10px; font-weight: bold; 
                    padding: 8px 15px; background: #1e1e1e; 
                    border: 1px solid #00ffa3; border-radius: 8px;
                """)
                self.layout_bancos_grid.addWidget(lbl)

            self.lbl_patr_valor.setText(f"R$ {total_geral:,.2f}")

            # 2. FUNÇÃO DE SOMA FILTRADA POR BANCOS ATIVOS
            def obter_soma(tabela):
                try:
                    # Inner Join com bancos para filtrar apenas os que têm status = 1
                    query = f"""
                        SELECT SUM(t.valor) 
                        FROM {tabela} t
                        INNER JOIN bancos b ON t.banco_id = b.id
                        WHERE strftime('%Y-%m', t.data) = ? AND b.status = 1
                    """
                    cur.execute(query, (periodo,))
                    res = cur.fetchone()[0]
                    return float(res) if res else 0.0
                except: return 0.0

            # Atualização dos Cards
            self.card_receitas.valor_label.setText(f"R$ {obter_soma('receitas'):,.2f}")
            self.card_despesas.valor_label.setText(f"R$ {obter_soma('despesas'):,.2f}")
            self.card_investimentos.valor_label.setText(f"R$ {obter_soma('investimentos'):,.2f}")
            
            # Dividendos (Soma geral, pois geralmente não depende de um banco_id específico na tabela)
            cur.execute("SELECT SUM(valor) FROM dividendos WHERE strftime('%Y-%m', data) = ?", (periodo,))
            res_div = cur.fetchone()[0]
            self.card_dividendos.valor_label.setText(f"R$ {(float(res_div) if res_div else 0.0):,.2f}")

            # 3. GRÁFICOS (RERENDER FILTRADO)
            self.ax_desp.clear()
            cur.execute("""
                SELECT c.nome, SUM(d.valor) 
                FROM despesas d 
                JOIN categorias c ON d.categoria_id = c.id 
                JOIN bancos b ON d.banco_id = b.id
                WHERE strftime('%Y-%m', d.data) = ? AND b.status = 1
                GROUP BY c.nome
            """, (periodo,))
            dados_d = cur.fetchall()
            if dados_d:
                self.ax_desp.pie([row[1] for row in dados_d], labels=[row[0] for row in dados_d], autopct='%1.1f%%', colors=['#ff4757', '#ffa502', '#3742fa', '#00ffa3'])
                self.ax_desp.set_title("DESPESAS (BANCOS ATIVOS)", color="#ff4757", fontsize=9, fontweight='bold')
            else: self.ax_desp.axis('off')

            self.ax_rec.clear()
            cur.execute("""
                SELECT c.nome, SUM(r.valor) 
                FROM receitas r 
                JOIN categorias c ON r.categoria_id = c.id 
                JOIN bancos b ON r.banco_id = b.id
                WHERE strftime('%Y-%m', r.data) = ? AND b.status = 1
                GROUP BY c.nome
            """, (periodo,))
            dados_r = cur.fetchall()
            if dados_r:
                self.ax_rec.pie([row[1] for row in dados_r], labels=[row[0] for row in dados_r], autopct='%1.1f%%', colors=['#2ecc71', '#00ffa3', '#1e90ff', '#a29bfe'])
                self.ax_rec.set_title("RECEITAS (BANCOS ATIVOS)", color="#2ecc71", fontsize=9, fontweight='bold')
            else: self.ax_rec.axis('off')

            self.canvas_desp.draw(); self.canvas_rec.draw()
            conn.close()
        except Exception as e: print(f"Erro no Dash: {e}")