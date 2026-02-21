from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.db import conectar

class TelaRentabilidade(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #0b0b0b; color: white;")
        layout = QVBoxLayout(self)

        self.label_titulo = QLabel("📊 PERFORMANCE TOTAL (VALORIZAÇÃO + DIVIDENDOS)")
        self.label_titulo.setStyleSheet("font-size:18px; color: #00ffa3; font-weight: bold;")
        layout.addWidget(self.label_titulo)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6) # Aumentamos para 6 colunas
        self.tabela.setHorizontalHeaderLabels([
            "ATIVO", "INVESTIDO", "VLR. ATUAL", "DIVIDENDOS", "LUCRO TOTAL", "RETORNO %"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setStyleSheet("""
            QTableWidget { background-color: #121212; color: white; gridline-color: #252525; border: none; }
            QHeaderView::section { background-color: #1a1a1a; color: #a4b0be; font-weight: bold; }
        """)
        layout.addWidget(self.tabela)

    def atualizar(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar()
            cur = conn.cursor()
            
            # Buscamos os ativos e o valor atual
            cur.execute("SELECT id, ativo, valor, COALESCE(valor_atual, 0) FROM investimentos")
            ativos = cur.fetchall()
            
            for id_inv, nome, investido, atual in ativos:
                # 1. Busca o total de dividendos recebidos deste ativo específico
                cur.execute("SELECT SUM(valor) FROM dividendos WHERE investimento_id = ?", (id_inv,))
                total_div = cur.fetchone()[0]
                total_div = total_div if total_div else 0.0
                
                # 2. Lógica de Preço
                vlr_mercado = atual if atual > 0 else investido
                lucro_valorizacao = vlr_mercado - investido
                
                # 3. Lucro Total = Valorização + Dividendos
                lucro_total = lucro_valorizacao + total_div
                
                # 4. Rentabilidade Real %
                porcentagem = (lucro_total / investido * 100) if investido > 0 else 0

                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                
                cor = "#00ffa3" if lucro_total >= 0 else "#ff4757"

                # Preenchimento
                self.tabela.setItem(row, 0, QTableWidgetItem(nome))
                self.tabela.setItem(row, 1, QTableWidgetItem(f"R$ {investido:.2f}"))
                self.tabela.setItem(row, 2, QTableWidgetItem(f"R$ {vlr_mercado:.2f}"))
                
                # Coluna de Dividendos (Nova)
                item_div = QTableWidgetItem(f"R$ {total_div:.2f}")
                item_div.setForeground(QColor("#00ffa3")) # Dividendos sempre em destaque
                self.tabela.setItem(row, 3, item_div)
                
                # Lucro Total (Valorização + Dividendos)
                item_lucro = QTableWidgetItem(f"R$ {lucro_total:.2f}")
                item_lucro.setForeground(QColor(cor))
                self.tabela.setItem(row, 4, item_lucro)
                
                # Porcentagem Total
                item_perc = QTableWidgetItem(f"{porcentagem:+.2f}%")
                item_perc.setForeground(QColor(cor))
                self.tabela.setItem(row, 5, item_perc)

            conn.close()
        except Exception as e:
            print(f"Erro na rentabilidade total: {e}")