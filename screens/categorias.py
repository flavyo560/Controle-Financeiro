from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout,
    QPushButton, QLineEdit,
    QListWidget, QMessageBox,
    QLabel, QComboBox
)
from PyQt6.QtCore import pyqtSignal
from database.db import conectar


class TelaCategorias(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Categorias")
        self.resize(420, 380)

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
            QLineEdit, QComboBox, QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 10px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #00ffa3;
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
                border: 1px solid #00ffa3;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #252525;
            }
            QListWidget::item:selected {
                background-color: #00ffa3;
                color: #000000;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        titulo = QLabel("GERENCIAR CATEGORIAS")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #00ffa3; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Nome
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome da categoria")
        layout.addWidget(self.input_nome)

        # Tipo
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["despesa", "receita", "investimento"])
        self.combo_tipo.currentTextChanged.connect(self.carregar_categorias)
        layout.addWidget(self.combo_tipo)

        # Botão adicionar (Verde Neon)
        btn_add = QPushButton("Adicionar categoria")
        btn_add.setStyleSheet("background-color: #00ffa3; color: black;")
        btn_add.clicked.connect(self.adicionar_categoria)
        layout.addWidget(btn_add)

        # Lista
        self.lista = QListWidget()
        layout.addWidget(self.lista)

        # Botão excluir (Vermelho Neon)
        btn_excluir = QPushButton("Excluir selecionada")
        btn_excluir.setStyleSheet("""
            QPushButton { background-color: transparent; border: 1px solid #ff4757; color: #ff4757; }
            QPushButton:hover { background-color: #ff4757; color: white; }
        """)
        btn_excluir.clicked.connect(self.excluir_categoria)
        layout.addWidget(btn_excluir)

        self.carregar_categorias()

    # =============================
    def carregar_categorias(self):
        self.lista.clear()
        tipo = self.combo_tipo.currentText()

        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, nome
                FROM categorias
                WHERE tipo = ?
                ORDER BY nome
            """, (tipo,))

            for cat_id, nome in cur.fetchall():
                self.lista.addItem(f"{cat_id} - {nome}")

            conn.close()
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")

    # =============================
    def adicionar_categoria(self):
        nome = self.input_nome.text().strip()
        tipo = self.combo_tipo.currentText()

        if not nome:
            QMessageBox.warning(self, "Erro", "Informe o nome da categoria.")
            return

        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO categorias (nome, tipo) VALUES (?, ?)",
                (nome, tipo)
            )
            conn.commit()
            conn.close()

            self.input_nome.clear()
            self.carregar_categorias()

            # 🔔 avisa o sistema inteiro
            self.dados_atualizados.emit()

        except:
            QMessageBox.warning(
                self,
                "Erro",
                "Essa categoria já existe para esse tipo."
            )

    # =============================
    def excluir_categoria(self):
        item = self.lista.currentItem()
        if not item:
            return

        texto = item.text()
        cat_id = texto.split(" - ")[0]

        resp = QMessageBox.question(
            self,
            "Confirmar",
            "Excluir esta categoria?"
        )

        if resp == QMessageBox.StandardButton.Yes:
            conn = conectar()
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM categorias WHERE id = ?",
                (cat_id,)
            )
            conn.commit()
            conn.close()

            self.carregar_categorias()
            self.dados_atualizados.emit()

    def atualizar(self):
        """Método chamado pela MainWindow para atualizar os dados"""
        self.carregar_categorias()