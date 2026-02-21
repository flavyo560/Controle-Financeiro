from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QDateEdit, QHeaderView
)
from PyQt6.QtCore import QDate, pyqtSignal, Qt
from database.db import conectar

class TelaReceitas(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Receitas")
        self.resize(900, 600)

        self.receita_id = None

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
                border: 1px solid #00d2ff;
            }
            QTableWidget {
                background-color: #121212;
                border: 1px solid #1f1f1f;
                gridline-color: #252525;
                color: white;
                selection-background-color: #00d2ff;
                selection-color: black;
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
                border: 1px solid #00d2ff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        titulo = QLabel("GERENCIAR RECEITAS")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #00d2ff; margin-bottom: 5px;")
        layout.addWidget(titulo)

        # ---------- FORMULÁRIO (ADICIONADO CAMPO BANCO) ----------
        form = QHBoxLayout()
        form.setSpacing(10)

        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Descrição (ex: Salário, Vendas)")

        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Valor (Ex: 1000.00)")
        self.input_valor.setFixedWidth(100)

        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)

        self.combo_categoria = QComboBox()
        self.combo_categoria.setMinimumWidth(130)

        # NOVO: Seletor de Banco para Depósito
        self.combo_banco = QComboBox()
        self.combo_banco.setPlaceholderText("Receber em...")
        self.combo_banco.setMinimumWidth(130)
        
        self.btn_add = QPushButton("Adicionar")
        self.btn_add.setStyleSheet("background-color: #00d2ff; color: black;")
        self.btn_add.clicked.connect(self.salvar_receita)

        form.addWidget(self.input_desc)
        form.addWidget(self.input_valor)
        form.addWidget(self.input_data)
        form.addWidget(self.combo_categoria)
        form.addWidget(self.combo_banco) # Adicionado ao layout
        form.addWidget(self.btn_add)

        layout.addLayout(form)

        # ---------- TABELA (COLUNA BANCO ADICIONADA) ----------
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6) # Aumentado para 6 colunas
        self.tabela.setHorizontalHeaderLabels(["ID", "DESCRIÇÃO", "VALOR", "DATA", "CATEGORIA", "BANCO"])
        self.tabela.setColumnHidden(0, True)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.tabela)

        # ---------- BOTÕES DE AÇÃO ----------
        btns = QHBoxLayout()
        btns.setSpacing(15)

        btn_editar = QPushButton("📝 Editar Selecionada")
        btn_excluir = QPushButton("🗑️ Excluir Selecionada")
        btn_excluir.setStyleSheet("""
            QPushButton { border: 1px solid #ff4757; color: #ff4757; }
            QPushButton:hover { background-color: #ff4757; color: white; }
        """)

        btn_editar.clicked.connect(self.editar_receita)
        btn_excluir.clicked.connect(self.excluir_receita)

        btns.addStretch()
        btns.addWidget(btn_editar)
        btns.addWidget(btn_excluir)

        layout.addLayout(btns)

        self.atualizar()

    def atualizar(self):
        self.carregar_categorias()
        self.carregar_bancos() # Novo
        self.carregar_receitas()

    def carregar_categorias(self):
        self.combo_categoria.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM categorias WHERE tipo='receita' ORDER BY nome")
            for cat_id, nome in cur.fetchall():
                self.combo_categoria.addItem(nome, cat_id)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")

    def carregar_bancos(self):
        """Busca os bancos cadastrados para preencher o combo."""
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

    def salvar_receita(self):
        desc = self.input_desc.text().strip()
        valor_txt = self.input_valor.text().replace(",", ".")
        data = self.input_data.date().toString("yyyy-MM-dd")
        cat_id = self.combo_categoria.currentData()
        banco_id = self.combo_banco.currentData()

        if not desc or not valor_txt or cat_id is None or banco_id is None:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos, incluindo o Banco de destino.")
            return

        try:
            valor = float(valor_txt)
        except:
            QMessageBox.warning(self, "Erro", "Valor numérico inválido.")
            return

        try:
            conn = conectar()
            cur = conn.cursor()

            if self.receita_id is None:
                # Agora incluímos o banco_id no cadastro
                cur.execute("""
                    INSERT INTO receitas (descricao, valor, data, categoria_id, banco_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (desc, valor, data, cat_id, banco_id))
            else:
                cur.execute("""
                    UPDATE receitas
                    SET descricao=?, valor=?, data=?, categoria_id=?, banco_id=?
                    WHERE id=?
                """, (desc, valor, data, cat_id, banco_id, self.receita_id))
                self.receita_id = None
                self.btn_add.setText("Adicionar")
                self.btn_add.setStyleSheet("background-color: #00d2ff; color: black;")

            conn.commit()
            conn.close()

            self.input_desc.clear()
            self.input_valor.clear()
            self.atualizar()
            self.dados_atualizados.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco", f"Erro ao salvar: {e}")

    def carregar_receitas(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar()
            cur = conn.cursor()
            # SQL atualizado com JOIN para buscar o nome do Banco
            cur.execute("""
                SELECT r.id, r.descricao, r.valor, r.data, c.nome, b.nome
                FROM receitas r
                JOIN categorias c ON r.categoria_id = c.id
                LEFT JOIN bancos b ON r.banco_id = b.id
                ORDER BY r.data DESC
            """)
            for row_data in cur.fetchall():
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                for col, item in enumerate(row_data):
                    val = f"R$ {item:.2f}" if col == 2 else str(item if item else "-")
                    tab_item = QTableWidgetItem(val)
                    if col == 2: tab_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.tabela.setItem(row, col, tab_item)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar receitas: {e}")

    def editar_receita(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione uma linha.")
            return

        self.receita_id = int(self.tabela.item(linha, 0).text())
        self.input_desc.setText(self.tabela.item(linha, 1).text())
        
        valor_limpo = self.tabela.item(linha, 2).text().replace("R$ ", "")
        self.input_valor.setText(valor_limpo)

        # Seta Categoria
        categoria_nome = self.tabela.item(linha, 4).text()
        index_cat = self.combo_categoria.findText(categoria_nome)
        if index_cat >= 0:
            self.combo_categoria.setCurrentIndex(index_cat)

        # Seta Banco
        banco_nome = self.tabela.item(linha, 5).text()
        index_banco = self.combo_banco.findText(banco_nome)
        if index_banco >= 0:
            self.combo_banco.setCurrentIndex(index_banco)

        self.btn_add.setText("Salvar Alteração")
        self.btn_add.setStyleSheet("background-color: #3742fa; color: white;")

    def excluir_receita(self):
        linha = self.tabela.currentRow()
        if linha < 0: return

        receita_id = int(self.tabela.item(linha, 0).text())
        resp = QMessageBox.question(self, "Confirmar", "Deseja excluir esta receita?")

        if resp == QMessageBox.StandardButton.Yes:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM receitas WHERE id=?", (receita_id,))
            conn.commit()
            conn.close()

            self.atualizar()
            self.dados_atualizados.emit()