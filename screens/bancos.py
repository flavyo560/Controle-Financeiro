from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from database.db import conectar, calcular_saldo_banco
from datetime import datetime

class TelaBancos(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerenciar Bancos")
        self.resize(800, 500)
        
        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QLabel { color: #a4b0be; font-weight: bold; }
            QLineEdit { background-color: #1a1a1a; border: 1px solid #333333; border-radius: 6px; padding: 8px; color: white; }
            QTableWidget { background-color: #121212; color: white; gridline-color: #252525; selection-background-color: #00ffa3; selection-color: black; }
            QHeaderView::section { background-color: #1a1a1a; color: #a4b0be; font-weight: bold; padding: 5px; }
            QPushButton { background-color: #1f1f1f; color: white; border: 1px solid #333333; padding: 10px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { border: 1px solid #00ffa3; background-color: #252525; }
        """)

        layout = QVBoxLayout(self)
        titulo = QLabel("🏦 MEUS BANCOS E SALDOS REAIS")
        titulo.setStyleSheet("font-size:18px; color: #00ffa3;")
        layout.addWidget(titulo)

        # Formulário de Cadastro
        form = QHBoxLayout()
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome do Banco (Ex: Nubank)")
        self.input_saldo = QLineEdit()
        self.input_saldo.setPlaceholderText("Saldo Inicial R$")
        self.btn_salvar = QPushButton("Cadastrar Banco")
        self.btn_salvar.setStyleSheet("background-color: #00ffa3; color: black;")
        self.btn_salvar.clicked.connect(self.salvar_banco)
        
        form.addWidget(self.input_nome)
        form.addWidget(self.input_saldo)
        form.addWidget(self.btn_salvar)
        layout.addLayout(form)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["ID", "BANCO", "SALDO INICIAL", "SALDO ATUAL"])
        self.tabela.setColumnHidden(0, True)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabela)

        # Botão Ocultar/Desativar
        self.btn_desativar = QPushButton("🚫 Ocultar Banco Selecionado")
        self.btn_desativar.setStyleSheet("""
            QPushButton { background-color: #1a1a1a; color: #ff4757; border: 1px solid #ff4757; }
            QPushButton:hover { background-color: #ff4757; color: white; }
        """)
        self.btn_desativar.clicked.connect(self.desativar_banco)
        layout.addWidget(self.btn_desativar, alignment=Qt.AlignmentFlag.AlignRight)

        self.atualizar()

    def atualizar(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar()
            cur = conn.cursor()
            # BUSCA APENAS BANCOS COM STATUS = 1 (ATIVOS)
            cur.execute("SELECT id, nome, saldo_inicial FROM bancos WHERE status = 1 ORDER BY nome")
            bancos = cur.fetchall()
            
            for row_data in bancos:
                b_id = row_data[0]
                saldo_atual = calcular_saldo_banco(b_id)
                
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                
                # ID (Oculto)
                self.tabela.setItem(row, 0, QTableWidgetItem(str(b_id)))
                # Nome
                self.tabela.setItem(row, 1, QTableWidgetItem(str(row_data[1])))
                # Saldo Inicial
                self.tabela.setItem(row, 2, QTableWidgetItem(f"R$ {row_data[2]:.2f}"))
                
                # Saldo Atual Colorido
                item_atual = QTableWidgetItem(f"R$ {saldo_atual:.2f}")
                if saldo_atual < 0:
                    item_atual.setForeground(QColor("#ff4757"))
                else:
                    item_atual.setForeground(QColor("#00ffa3"))
                self.tabela.setItem(row, 3, item_atual)
                
            conn.close()
        except Exception as e:
            print(f"Erro ao atualizar tabela de bancos: {e}")

    def salvar_banco(self):
        nome = self.input_nome.text().strip()
        saldo_txt = self.input_saldo.text().replace(",", ".")
        if not nome or not saldo_txt:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos!")
            return
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("INSERT INTO bancos (nome, saldo_inicial, criado_em, status) VALUES (?, ?, ?, 1)",
                        (nome, float(saldo_txt), datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            
            self.input_nome.clear()
            self.input_saldo.clear()
            self.atualizar()
            self.dados_atualizados.emit()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

    def desativar_banco(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um banco na tabela para ocultar.")
            return

        id_banco = self.tabela.item(linha, 0).text()
        nome_banco = self.tabela.item(linha, 1).text()

        confirm = QMessageBox.question(self, "Ocultar Banco", 
            f"Deseja ocultar o banco '{nome_banco}'?\n\n"
            "Ele não aparecerá mais para novos lançamentos, mas seu histórico permanecerá salvo.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                conn = conectar()
                cur = conn.cursor()
                # MUDA O STATUS PARA 0 (DESATIVADO/OCULTO)
                cur.execute("UPDATE bancos SET status = 0 WHERE id = ?", (id_banco,))
                conn.commit()
                conn.close()
                
                self.atualizar()
                self.dados_atualizados.emit() # Avisa o Dashboard e outras telas para sumir com ele
                QMessageBox.information(self, "Sucesso", "Banco ocultado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao desativar: {e}")