from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLabel, QHeaderView
)
from PyQt6.QtCore import Qt
from database.db import conectar

class TelaVeiculos(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Meus Veículos")
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QLineEdit { background-color: #1a1a1a; border: 1px solid #333; padding: 8px; color: white; border-radius: 4px; }
            QPushButton { border-radius: 4px; padding: 8px; }
            QTableWidget { background-color: #1a1a1a; color: white; gridline-color: #333; }
            QHeaderView::section { background-color: #222; color: #00ffa3; }
        """)

        layout = QVBoxLayout(self)

        titulo = QLabel("🚗 GERENCIAR FROTA")
        titulo.setStyleSheet("font-size: 18px; color: #00ffa3; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Formulário
        form = QHBoxLayout()
        self.input_nome = QLineEdit(); self.input_nome.setPlaceholderText("Identificador (Ex: Celta)")
        self.input_placa = QLineEdit(); self.input_placa.setPlaceholderText("Placa")
        self.btn_adicionar = QPushButton("Adicionar")
        self.btn_adicionar.clicked.connect(self.adicionar_veiculo)
        self.btn_adicionar.setStyleSheet("background-color: #00ffa3; color: black; font-weight: bold;")

        form.addWidget(self.input_nome)
        form.addWidget(self.input_placa)
        form.addWidget(self.btn_adicionar)
        layout.addLayout(form)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(3)
        self.tabela.setHorizontalHeaderLabels(["ID", "Veículo", "Placa"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Seleciona a linha toda
        layout.addWidget(self.tabela)

        # Botão Remover (O toque extra para o cliente)
        self.btn_remover = QPushButton("Remover Veículo Selecionado")
        self.btn_remover.clicked.connect(self.remover_veiculo)
        self.btn_remover.setStyleSheet("background-color: #ff4757; color: white; font-weight: bold; margin-top: 5px;")
        layout.addWidget(self.btn_remover)

        self.atualizar_lista()

    def adicionar_veiculo(self):
        nome = self.input_nome.text().strip()
        placa = self.input_placa.text().strip()
        if not nome: 
            QMessageBox.warning(self, "Aviso", "O nome do veículo é obrigatório.")
            return

        try:
            conn = conectar(); cur = conn.cursor()
            cur.execute("INSERT INTO veiculos (nome_identificador, placa) VALUES (?, ?)", (nome, placa))
            conn.commit(); conn.close()
            
            self.input_nome.clear(); self.input_placa.clear()
            self.atualizar_lista()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

    def remover_veiculo(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um veículo na tabela para remover.")
            return
        
        id_veiculo = self.tabela.item(linha, 0).text()
        
        confirmar = QMessageBox.question(self, "Confirmar", "Deseja realmente remover este veículo?", 
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirmar == QMessageBox.StandardButton.Yes:
            try:
                conn = conectar(); cur = conn.cursor()
                # Usamos status = 0 para não deletar o histórico de abastecimentos
                cur.execute("UPDATE veiculos SET status = 0 WHERE id = ?", (id_veiculo,))
                conn.commit(); conn.close()
                self.atualizar_lista()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao remover: {e}")

    def atualizar_lista(self):
        try:
            self.tabela.setRowCount(0)
            conn = conectar(); cur = conn.cursor()
            cur.execute("SELECT id, nome_identificador, placa FROM veiculos WHERE status = 1")
            for row_data in cur.fetchall():
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                for col, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabela.setItem(row, col, item)
            conn.close()
        except:
            pass