from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QTableWidget, 
    QTableWidgetItem, QMessageBox, QDateEdit, QHeaderView,
    QSizePolicy  # <--- ADICIONADO AQUI
)
from PyQt6.QtCore import QDate, pyqtSignal, Qt
from database.db import conectar, calcular_saldo_banco
from datetime import datetime

class TelaTransferencias(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transferências entre Contas")
        self.resize(900, 600)

        # CSS Corrigido para remover a faixa branca e estilizar o cabeçalho
        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QLabel { color: #a4b0be; font-weight: bold; }
            QLineEdit, QComboBox, QDateEdit {
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
                selection-background-color: #ff4757;
                selection-color: white;
                border: 1px solid #252525;
            }
            /* ESTILO DO CABEÇALHO (FIM DA FAIXA BRANCA) */
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #00ffa3;
                padding: 8px;
                border: 1px solid #252525;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #1a1a1a;
                border: none;
            }
            QPushButton#btn_excluir {
                background-color: #2a1010;
                color: #ff4757;
                border: 1px solid #ff4757;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton#btn_excluir:hover { background-color: #ff4757; color: white; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        titulo = QLabel("🔄 TRANSFERÊNCIA ENTRE CONTAS")
        titulo.setStyleSheet("font-size:18px; color: #00ffa3;")
        layout.addWidget(titulo)

        # ---------- FORMULÁRIO ----------
        form = QHBoxLayout()
        self.combo_origem = QComboBox()
        self.combo_destino = QComboBox()
        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Valor R$")
        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)

        self.btn_transferir = QPushButton("Confirmar")
        self.btn_transferir.setStyleSheet("background-color: #00ffa3; color: black; font-weight: bold;")
        self.btn_transferir.clicked.connect(self.executar_transferencia)

        form.addWidget(self.combo_origem)
        form.addWidget(QLabel("➔"))
        form.addWidget(self.combo_destino)
        form.addWidget(self.input_valor)
        form.addWidget(self.input_data)
        form.addWidget(self.btn_transferir)
        layout.addLayout(form)

        # ---------- TABELA ----------
        layout.addWidget(QLabel("Histórico de Movimentações:"))
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["ID", "DATA", "ORIGEM", "DESTINO", "VALOR"])
        self.tabela.setColumnHidden(0, True) 
        
        # Ajustes de comportamento da tabela
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Agora o QSizePolicy funcionará corretamente
        self.tabela.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout.addWidget(self.tabela)

        # ---------- BOTÃO EXCLUIR ----------
        self.btn_excluir = QPushButton("Excluir Transferência Selecionada")
        self.btn_excluir.setObjectName("btn_excluir")
        self.btn_excluir.clicked.connect(self.excluir_transferencia)
        layout.addWidget(self.btn_excluir)

        self.atualizar()

    def atualizar(self):
        self.carregar_bancos()
        self.carregar_historico()

    def carregar_bancos(self):
        self.combo_origem.clear()
        self.combo_destino.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM bancos ORDER BY nome")
            for b_id, nome in cur.fetchall():
                saldo = calcular_saldo_banco(b_id)
                self.combo_origem.addItem(f"{nome} (R$ {saldo:.2f})", b_id)
                self.combo_destino.addItem(f"{nome} (R$ {saldo:.2f})", b_id)
            conn.close()
        except Exception as e: print(f"Erro: {e}")

    def carregar_historico(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT t.id, t.data, b1.nome, b2.nome, t.valor
                FROM transferencias t
                JOIN bancos b1 ON t.banco_origem_id = b1.id
                JOIN bancos b2 ON t.banco_destino_id = b2.id
                ORDER BY t.data DESC
            """)
            for row_data in cur.fetchall():
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                for col, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data) if col != 4 else f"R$ {data:.2f}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if col == 4: item.setForeground(Qt.GlobalColor.cyan)
                    self.tabela.setItem(row, col, item)
            conn.close()
        except Exception as e: print(f"Erro ao carregar histórico: {e}")

    def executar_transferencia(self):
        origem_id = self.combo_origem.currentData()
        destino_id = self.combo_destino.currentData()
        valor_txt = self.input_valor.text().replace(",", ".")
        data = self.input_data.date().toString("yyyy-MM-dd")
        if origem_id == destino_id:
            QMessageBox.warning(self, "Erro", "Selecione bancos diferentes.")
            return
        try:
            valor = float(valor_txt)
            conn = conectar(); cur = conn.cursor()
            cur.execute("INSERT INTO transferencias (banco_origem_id, banco_destino_id, valor, data) VALUES (?, ?, ?, ?)",
                        (origem_id, destino_id, valor, data))
            conn.commit(); conn.close()
            self.atualizar()
            self.dados_atualizados.emit()
            self.input_valor.clear()
        except Exception as e: QMessageBox.critical(self, "Erro", str(e))

    def excluir_transferencia(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma transferência para excluir.")
            return
        transf_id = self.tabela.item(linha, 0).text()
        confirmacao = QMessageBox.question(self, "Confirmar Exclusão", 
                                         "Deseja realmente excluir esta transferência?\nOs saldos dos bancos serão restaurados.",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmacao == QMessageBox.StandardButton.Yes:
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("DELETE FROM transferencias WHERE id = ?", (transf_id,))
                conn.commit(); conn.close()
                QMessageBox.information(self, "Sucesso", "Transferência removida!")
                self.atualizar()
                self.dados_atualizados.emit()
            except Exception as e: QMessageBox.critical(self, "Erro", f"Erro ao excluir: {e}")