from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QMessageBox, QLineEdit, QApplication, QLabel
)
from utils.backup import realizar_backup, restaurar_backup
from database.db import resetar_banco
from screens.cadastro_usuario import TelaCadastroUsuario

class TelaFerramentas(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Ferramentas de Sistema")
        
        # Estilo Global da Tela
        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QPushButton {
                background-color: #1f1f1f;
                color: white;
                border: 1px solid #333333;
                padding: 15px;
                border-radius: 8px;
                font-size: 14px;
                text-align: left;
                padding-left: 20px;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                border: 1px solid #3742fa;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        titulo = QLabel("FERRAMENTAS E MANUTENÇÃO")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #a4b0be; margin-bottom: 20px;")
        layout.addWidget(titulo)

        # --- Backup ---
        btn_backup = QPushButton("💾 Fazer Backup dos Dados")
        btn_backup.clicked.connect(lambda: realizar_backup(self))
        layout.addWidget(btn_backup)

        # --- Restaurar ---
        btn_restore = QPushButton("♻️ Restaurar Backup Existente")
        btn_restore.clicked.connect(lambda: restaurar_backup(self))
        layout.addWidget(btn_restore)

        # --- Novo Usuário ---
        #btn_user = QPushButton("👤 Cadastrar Novo Usuário")
        #btn_user.clicked.connect(self.cadastrar_usuario)
       # layout.addWidget(btn_user)

       # layout.addSpacing(30)

        # --- Reset (Com destaque visual) ---
        btn_reset = QPushButton("🧹 RESET GERAL DO SISTEMA (Perigoso)")
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #2f1010; 
                color: #ff4757; 
                border: 1px solid #ff4757;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff4757;
                color: white;
            }
        """)
        btn_reset.clicked.connect(self.reset_geral)
        layout.addWidget(btn_reset)

        layout.addStretch()

    def atualizar(self):
        pass

    #def cadastrar_usuario(self):
        #self.nova_tela = TelaCadastroUsuario()
       # self.nova_tela.show()

    def reset_geral(self):
        resp = QMessageBox.question(
            self, "Reset Geral",
            "⚠️ ATENÇÃO!\n\nIsso irá APAGAR TODOS OS DADOS.\nDeseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resp != QMessageBox.StandardButton.Yes:
            return

        confirm = QMessageBox(self)
        confirm.setWindowTitle("Confirmação Final")
        confirm.setText("Para confirmar, digite abaixo: RESETAR")
        
        # Ajuste para o QLineEdit no diálogo do reset
        input_text = QLineEdit()
        input_text.setStyleSheet("background-color: white; color: black; padding: 5px;")
        confirm.layout().addWidget(input_text)

        confirm.addButton("Confirmar", QMessageBox.ButtonRole.AcceptRole)
        confirm.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        
        if confirm.exec() == 0:
            if input_text.text().strip().upper() == "RESETAR":
                resetar_banco()
                QMessageBox.information(self, "Sucesso", "Dados resetados. O app será fechado.")
                QApplication.quit()
            else:
                QMessageBox.warning(self, "Erro", "Palavra incorreta.")