from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QMessageBox, QHeaderView, QTableWidget, QTableWidgetItem, QDateEdit
)
from PyQt6.QtCore import pyqtSignal, QDate, Qt
from PyQt6.QtGui import QColor
from database.db import conectar

class TelaDividendos(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #0b0b0b; color: white;")
        layout = QVBoxLayout(self)

        titulo = QLabel("💰 GESTÃO DE DIVIDENDOS")
        titulo.setStyleSheet("font-size:18px; color: #00ffa3; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # --- ÁREA DE LANÇAMENTO ---
        form = QHBoxLayout()
        
        self.combo_ativos = QComboBox()
        self.combo_ativos.setStyleSheet("background-color: #1a1a1a; color: white; padding: 5px;")
        
        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Valor R$")
        self.input_valor.setStyleSheet("background-color: #1a1a1a; color: white; padding: 5px;")
        
        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        self.input_data.setStyleSheet("background-color: #1a1a1a; color: white; padding: 5px;")
        
        self.btn_salvar = QPushButton("Registrar")
        self.btn_salvar.setStyleSheet("background-color: #00ffa3; color: black; font-weight: bold; padding: 7px 15px;")
        self.btn_salvar.clicked.connect(self.registrar_dividendo)

        form.addWidget(self.combo_ativos)
        form.addWidget(self.input_valor)
        form.addWidget(self.input_data)
        form.addWidget(self.btn_salvar)
        layout.addLayout(form)

        # --- TABELA DE HISTÓRICO ---
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4) # Aumentado para 4 colunas (ID oculto)
        self.tabela.setHorizontalHeaderLabels(["ID", "DATA", "ATIVO", "VALOR"])
        self.tabela.hideColumn(0) # Esconde a coluna do ID do dividendo
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setStyleSheet("""
            QTableWidget { background-color: #121212; color: white; gridline-color: #252525; }
            QHeaderView::section { background-color: #1a1a1a; color: #a4b0be; }
        """)
        layout.addWidget(self.tabela)

        # --- BOTÃO EXCLUIR ---
        self.btn_excluir = QPushButton("🗑️ Excluir Lançamento Selecionado")
        self.btn_excluir.setStyleSheet("""
            QPushButton { background-color: #ff4757; color: white; font-weight: bold; padding: 8px; margin-top: 5px; border-radius: 5px; }
            QPushButton:hover { background-color: #ff6b81; }
        """)
        self.btn_excluir.clicked.connect(self.excluir_dividendo)
        layout.addWidget(self.btn_excluir)

        self.atualizar()

    def atualizar(self):
        self.carregar_ativos()
        self.carregar_historico()

    def carregar_ativos(self):
        self.combo_ativos.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, ativo FROM investimentos")
            for id_inv, nome in cur.fetchall():
                self.combo_ativos.addItem(nome, id_inv)
            conn.close()
        except: pass

    def carregar_historico(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT d.id, d.data, i.ativo, d.valor 
                FROM dividendos d
                INNER JOIN investimentos i ON d.investimento_id = i.id
                ORDER BY d.data DESC
            """)
            for id_div, data, ativo, valor in cur.fetchall():
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                self.tabela.setItem(row, 0, QTableWidgetItem(str(id_div)))
                self.tabela.setItem(row, 1, QTableWidgetItem(str(data)))
                self.tabela.setItem(row, 2, QTableWidgetItem(str(ativo)))
                item_v = QTableWidgetItem(f"R$ {valor:.2f}")
                item_v.setForeground(QColor("#00ffa3"))
                self.tabela.setItem(row, 3, item_v)
            conn.close()
        except: pass

    def registrar_dividendo(self):
        try:
            id_inv = self.combo_ativos.currentData()
            nome_ativo = self.combo_ativos.currentText()
            valor = float(self.input_valor.text().replace(",", "."))
            data = self.input_data.date().toString("yyyy-MM-dd")

            conn = conectar()
            cur = conn.cursor()
            cur.execute("INSERT INTO dividendos (investimento_id, valor, data) VALUES (?, ?, ?)", 
                       (id_inv, valor, data))

            # Registra como receita também
            try:
                cur.execute("SELECT id FROM categorias WHERE nome = 'Dividendo' LIMIT 1")
                cat = cur.fetchone()
                cat_id = cat[0] if cat else 1
                cur.execute("INSERT INTO receitas (descricao, valor, data, categoria_id) VALUES (?, ?, ?, ?)",
                           (f"Dividendo {nome_ativo}", valor, data, cat_id))
            except: pass

            conn.commit()
            conn.close()
            self.input_valor.clear()
            self.atualizar()
            self.dados_atualizados.emit()
            QMessageBox.information(self, "Sucesso", "Dividendo registrado!")
        except:
            QMessageBox.warning(self, "Erro", "Verifique o valor digitado.")

    def excluir_dividendo(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um lançamento para excluir.")
            return

        id_div = self.tabela.item(linha, 0).text()
        ativo = self.tabela.item(linha, 2).text()
        valor_texto = self.tabela.item(linha, 3).text().replace("R$ ", "")
        
        confirmar = QMessageBox.question(self, "Confirmar", f"Deseja excluir o dividendo de {ativo} no valor de R$ {valor_texto}?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirmar == QMessageBox.StandardButton.Yes:
            try:
                conn = conectar()
                cur = conn.cursor()
                
                # 1. Deleta da tabela de dividendos
                cur.execute("DELETE FROM dividendos WHERE id = ?", (id_div,))
                
                # 2. Deleta da tabela de receitas (baseado na descrição e valor aproximado)
                # Isso evita que o saldo do dashboard fique errado
                cur.execute("DELETE FROM receitas WHERE descricao LIKE ? AND valor = ?", 
                           (f"Dividendo {ativo}%", float(valor_texto)))
                
                conn.commit()
                conn.close()
                
                self.atualizar()
                self.dados_atualizados.emit()
                QMessageBox.information(self, "Sucesso", "Lançamento removido!")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao excluir: {e}")