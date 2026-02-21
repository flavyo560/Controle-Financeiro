from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QDateEdit, QHeaderView
)
from PyQt6.QtCore import QDate, pyqtSignal, Qt
from database.db import conectar


class TelaInvestimentos(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Investimentos")
        self.resize(1100, 650)

        self.investimento_id = None  # controla edição

        # ESTILO MODERNO DARK COM DETALHES CIANO NEON
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
            QLineEdit:focus { border: 1px solid #00ffa3; }
            QTableWidget {
                background-color: #121212;
                gridline-color: #252525;
                color: white;
                selection-background-color: #00ffa3;
                selection-color: black;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #a4b0be;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #1f1f1f;
                color: white;
                border: 1px solid #333333;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { border: 1px solid #00ffa3; background-color: #252525; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        titulo = QLabel("📈 CARTEIRA DE INVESTIMENTOS")
        titulo.setStyleSheet("font-size:18px; color: #00ffa3;")
        layout.addWidget(titulo)

        # ---------- FORMULÁRIO (ADICIONADO CAMPO BANCO) ----------
        form = QHBoxLayout()

        self.input_ativo = QLineEdit()
        self.input_ativo.setPlaceholderText("Ativo (ex: PETR4, BTC)")

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Ação", "FII", "Tesouro", "Cripto", "Renda Fixa", "Outro"])

        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Valor R$")
        self.input_valor.setFixedWidth(100)

        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)

        self.combo_categoria = QComboBox()
        self.combo_categoria.setPlaceholderText("Categoria")

        # NOVO: Seletor de Banco (Origem do dinheiro)
        self.combo_banco = QComboBox()
        self.combo_banco.setPlaceholderText("Origem...")
        self.combo_banco.setMinimumWidth(120)

        self.btn_add = QPushButton("Registrar")
        self.btn_add.setStyleSheet("background-color: #00ffa3; color: black;")
        self.btn_add.clicked.connect(self.salvar_investimento)

        form.addWidget(self.input_ativo)
        form.addWidget(self.combo_tipo)
        form.addWidget(self.input_valor)
        form.addWidget(self.input_data)
        form.addWidget(self.combo_categoria)
        form.addWidget(self.combo_banco) # Adicionado
        form.addWidget(self.btn_add)

        layout.addLayout(form)

        # ---------- TABELA (COLUNA BANCO ADICIONADA) ----------
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7) # Aumentado para 7
        self.tabela.setHorizontalHeaderLabels(
            ["ID", "Ativo", "Tipo", "Valor", "Data", "Categoria", "Origem/Banco"]
        )
        self.tabela.setColumnHidden(0, True)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.tabela)

        # ---------- BOTÕES DE AÇÃO ----------
        btns = QHBoxLayout()

        btn_editar = QPushButton("📝 Editar Selecionado")
        btn_excluir = QPushButton("🗑️ Excluir Registro")
        btn_excluir.setStyleSheet("color: #ff4757; border: 1px solid #ff4757;")

        btn_editar.clicked.connect(self.editar_investimento)
        btn_excluir.clicked.connect(self.excluir_investimento)

        btns.addStretch()
        btns.addWidget(btn_editar)
        btns.addWidget(btn_excluir)

        layout.addLayout(btns)

        self.atualizar()

    def atualizar(self):
        self.carregar_categorias()
        self.carregar_bancos() # Novo
        self.carregar_investimentos()

    def carregar_categorias(self):
        self.combo_categoria.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM categorias WHERE tipo='investimento' ORDER BY nome")
            for cat_id, nome in cur.fetchall():
                self.combo_categoria.addItem(nome, cat_id)
            conn.close()
        except Exception as e:
            print(f"Erro categorias: {e}")

    def carregar_bancos(self):
        self.combo_banco.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM bancos ORDER BY nome")
            for b_id, nome in cur.fetchall():
                self.combo_banco.addItem(nome, b_id)
            conn.close()
        except Exception as e:
            print(f"Erro bancos: {e}")

    def salvar_investimento(self):
        ativo = self.input_ativo.text().strip().upper()
        valor_txt = self.input_valor.text().replace(",", ".")
        data = self.input_data.date().toString("yyyy-MM-dd")
        tipo = self.combo_tipo.currentText()
        cat_id = self.combo_categoria.currentData()
        banco_id = self.combo_banco.currentData()

        if not ativo or not valor_txt or cat_id is None or banco_id is None:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos, incluindo o Banco de origem.")
            return

        try:
            valor = float(valor_txt)
            conn = conectar()
            cur = conn.cursor()

            if self.investimento_id is None:
                cur.execute("""
                    INSERT INTO investimentos (ativo, valor, tipo, data, categoria_id, banco_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ativo, valor, tipo, data, cat_id, banco_id))
            else:
                cur.execute("""
                    UPDATE investimentos
                    SET ativo=?, valor=?, tipo=?, data=?, categoria_id=?, banco_id=?
                    WHERE id=?
                """, (ativo, valor, tipo, data, cat_id, banco_id, self.investimento_id))
                self.investimento_id = None
                self.btn_add.setText("Registrar")
                self.btn_add.setStyleSheet("background-color: #00ffa3; color: black;")

            conn.commit()
            conn.close()

            self.input_ativo.clear()
            self.input_valor.clear()
            self.atualizar()
            self.dados_atualizados.emit()
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valor financeiro inválido.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro no banco: {e}")

    def carregar_investimentos(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT i.id, i.ativo, i.tipo, i.valor, i.data, c.nome, b.nome
                FROM investimentos i
                JOIN categorias c ON i.categoria_id = c.id
                LEFT JOIN bancos b ON i.banco_id = b.id
                ORDER BY i.data DESC
            """)
            for row_data in cur.fetchall():
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                for col, item in enumerate(row_data):
                    if col == 3:
                        val = f"R$ {item:.2f}"
                    else:
                        val = str(item if item else "-")
                    
                    self.tabela.setItem(row, col, QTableWidgetItem(val))
            conn.close()
        except Exception as e:
            print(f"Erro listagem: {e}")

    def editar_investimento(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione um investimento.")
            return

        self.investimento_id = int(self.tabela.item(linha, 0).text())
        self.input_ativo.setText(self.tabela.item(linha, 1).text())
        self.combo_tipo.setCurrentText(self.tabela.item(linha, 2).text())
        
        valor_limpo = self.tabela.item(linha, 3).text().replace("R$ ", "")
        self.input_valor.setText(valor_limpo)
        
        data_str = self.tabela.item(linha, 4).text()
        self.input_data.setDate(QDate.fromString(data_str, "yyyy-MM-dd"))

        # Selecionar Categoria
        index_cat = self.combo_categoria.findText(self.tabela.item(linha, 5).text())
        if index_cat >= 0: self.combo_categoria.setCurrentIndex(index_cat)

        # Selecionar Banco
        index_banco = self.combo_banco.findText(self.tabela.item(linha, 6).text())
        if index_banco >= 0: self.combo_banco.setCurrentIndex(index_banco)

        self.btn_add.setText("Salvar Alterações")
        self.btn_add.setStyleSheet("background-color: #ffb100; color: black;")

    def excluir_investimento(self):
        linha = self.tabela.currentRow()
        if linha < 0: return

        id_reg = int(self.tabela.item(linha, 0).text())
        if QMessageBox.question(self, "Confirmar", "Excluir este investimento?") == QMessageBox.StandardButton.Yes:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM investimentos WHERE id=?", (id_reg,))
            conn.commit()
            conn.close()
            self.atualizar()
            self.dados_atualizados.emit()