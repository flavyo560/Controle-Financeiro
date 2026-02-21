from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QMessageBox, QHeaderView, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from database.db import conectar

class TelaAtualizarTesouro(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Atualizar Valor de Ativos")
        self.resize(700, 500)

        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QLabel { color: #a4b0be; font-weight: bold; }
            QLineEdit, QComboBox {
                background-color: #1a1a1a; border: 1px solid #333333;
                border-radius: 6px; padding: 8px; color: white;
            }
            QPushButton {
                background-color: #1f1f1f; color: white; border: 1px solid #333333;
                padding: 10px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { border: 1px solid #00ffa3; background-color: #252525; }
            QTableWidget {
                background-color: #121212; color: white; gridline-color: #252525;
                border: none;
            }
            QHeaderView::section { background-color: #1a1a1a; color: #a4b0be; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)

        titulo = QLabel("📈 ATUALIZAR VALOR ATUAL (Marcação a Mercado)")
        titulo.setStyleSheet("font-size:18px; color: #00ffa3; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Form para atualizar
        form = QHBoxLayout()
        self.combo_ativos = QComboBox()
        self.input_novo_valor = QLineEdit()
        self.input_novo_valor.setPlaceholderText("Novo Valor Total R$")
        
        self.btn_atualizar = QPushButton("Atualizar Saldo")
        self.btn_atualizar.setStyleSheet("background-color: #00ffa3; color: black;")
        self.btn_atualizar.clicked.connect(self.atualizar_valor)

        form.addWidget(self.combo_ativos)
        form.addWidget(self.input_novo_valor)
        form.addWidget(self.btn_atualizar)
        layout.addLayout(form)

        # Tabela para mostrar ganhos/perdas
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["ATIVO", "INVESTIDO (CUSTO)", "VALOR ATUAL", "LUCRO/PERDA"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabela)

        self.carregar_dados()

    def carregar_dados(self):
        self.combo_ativos.clear()
        self.tabela.setRowCount(0)
        try:
            conn = conectar()
            cur = conn.cursor()
            
            # Buscamos o valor original e o valor_atual
            cur.execute("SELECT id, ativo, valor, COALESCE(valor_atual, 0) FROM investimentos")
            investimentos = cur.fetchall()
            
            for id_inv, nome, custo, atual in investimentos:
                # Adiciona ao combo para seleção
                self.combo_ativos.addItem(nome, (id_inv, custo))
                
                # Cálculo para a tabela
                vlr_mercado = atual if atual > 0 else custo
                lucro = vlr_mercado - custo
                cor = "#00ffa3" if lucro >= 0 else "#ff4757"
                
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                self.tabela.setItem(row, 0, QTableWidgetItem(nome))
                self.tabela.setItem(row, 1, QTableWidgetItem(f"R$ {custo:.2f}"))
                self.tabela.setItem(row, 2, QTableWidgetItem(f"R$ {vlr_mercado:.2f}"))
                
                item_lucro = QTableWidgetItem(f"R$ {lucro:.2f}")
                item_lucro.setForeground(QColor(cor))
                self.tabela.setItem(row, 3, item_lucro)
                
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")

    def atualizar_valor(self):
        try:
            dados = self.combo_ativos.currentData()
            if not dados: return
            
            id_inv = dados[0]
            vlr_custo = dados[1] # Mantemos o custo original
            novo_vlr = float(self.input_novo_valor.text().replace(",", "."))

            conn = conectar()
            cur = conn.cursor()
            
            # CORREÇÃO AQUI: Atualizamos a coluna valor_atual, preservando o valor (custo)
            cur.execute("UPDATE investimentos SET valor_atual = ? WHERE id = ?", (novo_vlr, id_inv))
            
            conn.commit()
            conn.close()

            variacao = novo_vlr - vlr_custo
            QMessageBox.information(self, "Sucesso", f"Saldo atualizado!\nLucro/Perda acumulado: R$ {variacao:.2f}")
            
            self.input_novo_valor.clear()
            self.carregar_dados()
            self.dados_atualizados.emit() # Notifica as outras telas (como Rentabilidade)
            
        except ValueError:
            QMessageBox.warning(self, "Erro", "Por favor, digite um valor numérico válido.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao atualizar banco: {e}")