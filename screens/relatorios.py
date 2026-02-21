from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from database.db import conectar
from datetime import datetime

class TelaRelatorios(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Relatórios Mensais")
        
        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QLabel { color: #a4b0be; font-weight: bold; }
            QComboBox {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #121212;
                gridline-color: #252525;
                color: white;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #00ffa3;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        # Filtros
        topo = QHBoxLayout()
        self.combo_mes = QComboBox()
        self.combo_mes.addItems(["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
        self.combo_mes.setCurrentIndex(datetime.now().month - 1)
        self.combo_mes.currentIndexChanged.connect(self.atualizar)

        topo.addWidget(QLabel("Selecionar Mês:"))
        topo.addWidget(self.combo_mes)
        topo.addStretch()
        layout.addLayout(topo)

        # Resumo Financeiro
        self.label_resumo = QLabel("Resumo do Mês")
        self.label_resumo.setStyleSheet("font-size: 18px; color: #00ffa3; margin-top: 20px;")
        layout.addWidget(self.label_resumo)

        self.tabela_financas = QTableWidget(3, 2)
        self.tabela_financas.setHorizontalHeaderLabels(["Descrição", "Valor"])
        self.tabela_financas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_financas.setFixedHeight(130)
        layout.addWidget(self.tabela_financas)

        # Resumo Veicular
        self.label_veiculo = QLabel("Desempenho do Veículo")
        self.label_veiculo.setStyleSheet("font-size: 18px; color: #ffb100; margin-top: 20px;")
        layout.addWidget(self.label_veiculo)

        self.tabela_veiculo = QTableWidget(3, 2)
        self.tabela_veiculo.setHorizontalHeaderLabels(["Métrica", "Resultado"])
        self.tabela_veiculo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_veiculo.setFixedHeight(130)
        layout.addWidget(self.tabela_veiculo)

        layout.addStretch()
        self.atualizar()

    def atualizar(self):
        mes = self.combo_mes.currentIndex() + 1
        ano = datetime.now().year
        mes_str = f"{ano}-{mes:02d}"

        conn = conectar()
        cur = conn.cursor()

        # --- Finanças ---
        cur.execute("SELECT SUM(valor) FROM receitas WHERE data LIKE ?", (f"{mes_str}%",))
        rec = cur.fetchone()[0] or 0
        cur.execute("SELECT SUM(valor) FROM despesas WHERE data LIKE ?", (f"{mes_str}%",))
        desp = cur.fetchone()[0] or 0
        
        self.tabela_financas.setItem(0, 0, QTableWidgetItem("Total Receitas"))
        self.tabela_financas.setItem(0, 1, QTableWidgetItem(f"R$ {rec:.2f}"))
        self.tabela_financas.setItem(1, 0, QTableWidgetItem("Total Despesas"))
        self.tabela_financas.setItem(1, 1, QTableWidgetItem(f"R$ {desp:.2f}"))
        self.tabela_financas.setItem(2, 0, QTableWidgetItem("Saldo Líquido"))
        self.tabela_financas.setItem(2, 1, QTableWidgetItem(f"R$ {rec-desp:.2f}"))

        # --- Veículo (Cálculo de Consumo) ---
        cur.execute("SELECT km, litros FROM abastecimentos WHERE data LIKE ? ORDER BY km DESC", (f"{mes_str}%",))
        dados = cur.fetchall()
        
        if len(dados) >= 2:
            distancia = dados[0][0] - dados[-1][0]
            total_litros = sum(d[1] for d in dados[:-1]) # Litros usados para percorrer a distância
            consumo = distancia / total_litros if total_litros > 0 else 0
        else:
            distancia = 0
            consumo = 0

        self.tabela_veiculo.setItem(0, 0, QTableWidgetItem("KM Rodados no Mês"))
        self.tabela_veiculo.setItem(0, 1, QTableWidgetItem(f"{distancia:.1f} km"))
        self.tabela_veiculo.setItem(1, 0, QTableWidgetItem("Média de Consumo"))
        self.tabela_veiculo.setItem(1, 1, QTableWidgetItem(f"{consumo:.2f} km/L"))
        
        conn.close()