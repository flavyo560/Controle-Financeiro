from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class TelaAtivacao(QWidget):
    # Sinal para avisar ao AppController que o banco validou a chave
    ativado_com_sucesso = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ativação FinanceApp")
        self.setFixedSize(450, 380)
        self.setStyleSheet("background-color: #f8f9fa;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        titulo = QLabel("Ativação do Sistema")
        titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.input_chave = QLineEdit()
        self.input_chave.setPlaceholderText("Cole sua chave aqui...")
        self.input_chave.setStyleSheet("padding: 12px; border: 1px solid #ccc; border-radius: 5px; margin-top: 20px;")

        # ADICIONADO SELF: Agora o AppController consegue enxergar este botão
        self.btn_ativar = QPushButton("Ativar Agora")
        self.btn_ativar.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")

        self.btn_whatsapp = QPushButton("💬 Solicitar Chave via WhatsApp")
        self.btn_whatsapp.setStyleSheet("""
            QPushButton { background-color: #25D366; color: white; font-weight: bold; padding: 12px; border-radius: 5px; margin-top: 10px; }
            QPushButton:hover { background-color: #128C7E; }
        """)

        layout.addWidget(titulo)
        layout.addWidget(self.input_chave)
        layout.addWidget(self.btn_ativar)
        layout.addWidget(self.btn_whatsapp)
        layout.addStretch()