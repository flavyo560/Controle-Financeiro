from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QDateEdit, QLabel, QHeaderView
)
from PyQt6.QtCore import QDate, pyqtSignal, Qt
from database.db import conectar

class TelaDespesas(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Despesas")
        self.resize(900, 600)

        self.despesa_id = None

        # 1. ESTILO DA TELA (DARK MODE)
        self.setStyleSheet("""
            QWidget { 
                background-color: #0b0b0b; 
                color: white; 
            }
            QLabel { 
                color: #a4b0be; 
                font-weight: bold; 
            }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #ff0055;
            }
            QTableWidget {
                background-color: #121212;
                border: 1px solid #1f1f1f;
                gridline-color: #252525;
                color: white;
                selection-background-color: #ff0055;
                selection-color: white;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #a4b0be;
                padding: 5px;
                border: 1px solid #1f1f1f;
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
            QPushButton:hover {
                background-color: #2d2d2d;
                border: 1px solid #ff0055;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        titulo = QLabel("GERENCIAR DESPESAS")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #ff0055; margin-bottom: 5px;")
        layout.addWidget(titulo)

        # =============================
        # FORMULÁRIO (ADICIONADO CAMPO BANCO)
        # =============================
        form = QHBoxLayout()
        form.setSpacing(10)

        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Descrição da despesa...")

        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Valor (Ex: 50.00)")
        self.input_valor.setFixedWidth(100)

        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)

        self.combo_categoria = QComboBox()
        self.combo_categoria.setPlaceholderText("Categoria")
        self.combo_categoria.setMinimumWidth(130)

        # NOVO: ComboBox de Bancos
        self.combo_banco = QComboBox()
        self.combo_banco.setPlaceholderText("Pagar com...")
        self.combo_banco.setMinimumWidth(130)

        self.btn_add = QPushButton("Adicionar")
        self.btn_add.setStyleSheet("background-color: #ff0055; color: white;")
        self.btn_add.clicked.connect(self.salvar_despesa)

        form.addWidget(self.input_desc)
        form.addWidget(self.input_valor)
        form.addWidget(self.input_data)
        form.addWidget(self.combo_categoria)
        form.addWidget(self.combo_banco) # Adicionado no layout
        form.addWidget(self.btn_add)

        layout.addLayout(form)

        # =============================
        # TABELA (ADICIONADA COLUNA BANCO)
        # =============================
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6) # Aumentado de 5 para 6
        self.tabela.setHorizontalHeaderLabels(["ID", "DESCRIÇÃO", "VALOR", "DATA", "CATEGORIA", "BANCO"])
        self.tabela.setColumnHidden(0, True)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.tabela)

        # =============================
        # BOTÕES DE AÇÃO
        # =============================
        btns = QHBoxLayout()
        btns.setSpacing(15)

        btn_editar = QPushButton("📝 Editar Selecionada")
        btn_excluir = QPushButton("🗑️ Excluir Selecionada")
        btn_excluir.setStyleSheet("""
            QPushButton { border: 1px solid #ff4757; color: #ff4757; }
            QPushButton:hover { background-color: #ff4757; color: white; }
        """)

        btn_editar.clicked.connect(self.editar_despesa)
        btn_excluir.clicked.connect(self.excluir_despesa)

        btns.addStretch()
        btns.addWidget(btn_editar)
        btns.addWidget(btn_excluir)

        layout.addLayout(btns)

        self.atualizar()

    def atualizar(self):
        self.carregar_categorias()
        self.carregar_bancos() # Novo carregamento
        self.carregar_despesas()

    def carregar_categorias(self):
        self.combo_categoria.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM categorias WHERE tipo = 'despesa' ORDER BY nome")
            for cat_id, nome in cur.fetchall():
                self.combo_categoria.addItem(nome, cat_id)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")

    def carregar_bancos(self):
        """Carrega a lista de bancos cadastrados no sistema."""
        self.combo_banco.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM bancos ORDER BY nome")
            for b_id, nome in cur.fetchall():
                self.combo_banco.addItem(nome, b_id)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar bancos: {e}")

    def salvar_despesa(self):
        desc = self.input_desc.text().strip()
        valor_txt = self.input_valor.text().replace(",", ".")
        data = self.input_data.date().toString("yyyy-MM-dd")
        cat_id = self.combo_categoria.currentData()
        banco_id = self.combo_banco.currentData()

        if not desc or not valor_txt or cat_id is None or banco_id is None:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos, incluindo o Banco.")
            return

        try:
            valor = float(valor_txt)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valor numérico inválido.")
            return

        conn = conectar()
        cur = conn.cursor()

        if self.despesa_id is None:
            # Incluído banco_id no INSERT
            cur.execute("""
                INSERT INTO despesas (descricao, valor, data, categoria_id, banco_id) 
                VALUES (?, ?, ?, ?, ?)
            """, (desc, valor, data, cat_id, banco_id))
        else:
            # Incluído banco_id no UPDATE
            cur.execute("""
                UPDATE despesas SET descricao=?, valor=?, data=?, categoria_id=?, banco_id=? 
                WHERE id=?
            """, (desc, valor, data, cat_id, banco_id, self.despesa_id))
            self.despesa_id = None
            self.btn_add.setText("Adicionar")
            self.btn_add.setStyleSheet("background-color: #ff0055; color: white;")

        conn.commit()
        conn.close()

        self.input_desc.clear()
        self.input_valor.clear()
        self.atualizar()
        self.dados_atualizados.emit()

    def carregar_despesas(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar()
            cur = conn.cursor()
            # SQL atualizado para trazer o nome do Banco via JOIN
            cur.execute("""
                SELECT d.id, d.descricao, d.valor, d.data, c.nome, b.nome
                FROM despesas d
                JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN bancos b ON d.banco_id = b.id
                ORDER BY d.data DESC
            """)
            for row_data in cur.fetchall():
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                for col, item in enumerate(row_data):
                    val = f"R$ {item:.2f}" if col == 2 else str(item if item else "Não definido")
                    tab_item = QTableWidgetItem(val)
                    if col == 2: 
                        tab_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.tabela.setItem(row, col, tab_item)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar despesas: {e}")

    def editar_despesa(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione uma despesa para editar.")
            return

        self.despesa_id = int(self.tabela.item(linha, 0).text())
        self.input_desc.setText(self.tabela.item(linha, 1).text())
        
        valor_limpo = self.tabela.item(linha, 2).text().replace("R$ ", "")
        self.input_valor.setText(valor_limpo)

        # Recuperar Categoria
        categoria_nome = self.tabela.item(linha, 4).text()
        index_cat = self.combo_categoria.findText(categoria_nome)
        if index_cat >= 0:
            self.combo_categoria.setCurrentIndex(index_cat)

        # Recuperar Banco
        banco_nome = self.tabela.item(linha, 5).text()
        index_banco = self.combo_banco.findText(banco_nome)
        if index_banco >= 0:
            self.combo_banco.setCurrentIndex(index_banco)

        self.btn_add.setText("Salvar Alteração")
        self.btn_add.setStyleSheet("background-color: #3742fa; color: white;")

    def excluir_despesa(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            return

        despesa_id = int(self.tabela.item(linha, 0).text())
        resp = QMessageBox.question(self, "Confirmar", "Deseja realmente excluir esta despesa?")

        if resp == QMessageBox.StandardButton.Yes:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM despesas WHERE id=?", (despesa_id,))
            conn.commit()
            conn.close()

            self.atualizar()
            self.dados_atualizados.emit()