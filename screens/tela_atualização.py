from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, 
    QLabel, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from database.db import conectar, hash_senha

class TelaAtualizacaoUsuario(QWidget):
    def __init__(self, usuario_id):
        super().__init__()
        self.usuario_id = usuario_id
        self.setWindowTitle("Atualizar Perfil")
        self.setFixedSize(400, 450)
        self.setStyleSheet("background-color: #0b0b0b; color: white;")

        layout = QVBoxLayout(self)
        
        titulo = QLabel("👤 MEU PERFIL")
        titulo.setStyleSheet("font-size: 18px; color: #00ffa3; font-weight: bold; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Campos
        self.input_nome = QLineEdit(); self.input_nome.setPlaceholderText("Nome Completo")
        self.input_email = QLineEdit(); self.input_email.setPlaceholderText("E-mail")
        self.input_cpf = QLineEdit(); self.input_cpf.setPlaceholderText("CPF")
        self.input_tel = QLineEdit(); self.input_tel.setPlaceholderText("Telefone")
        self.input_senha = QLineEdit(); self.input_senha.setPlaceholderText("Nova Senha (deixe em branco para manter)")
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)

        # Estilo dos inputs
        estilo_input = "background-color: #1a1a1a; border: 1px solid #333; padding: 10px; border-radius: 5px; color: white;"
        for w in [self.input_nome, self.input_email, self.input_cpf, self.input_tel, self.input_senha]:
            w.setStyleSheet(estilo_input)
            layout.addWidget(w)

        self.btn_salvar = QPushButton("Salvar Alterações")
        self.btn_salvar.setStyleSheet("""
            QPushButton { background-color: #00ffa3; color: black; font-weight: bold; padding: 12px; border-radius: 5px; margin-top: 10px; }
            QPushButton:hover { background-color: #00e591; }
        """)
        self.btn_salvar.clicked.connect(self.salvar_dados)
        layout.addWidget(self.btn_salvar)

        self.carregar_dados()

    def carregar_dados(self):
        try:
            conn = conectar(); cur = conn.cursor()
            cur.execute("SELECT nome, email, cpf, telefone FROM usuarios WHERE id = ?", (self.usuario_id,))
            user = cur.fetchone()
            conn.close()
            if user:
                self.input_nome.setText(user[0])
                self.input_email.setText(user[1])
                self.input_cpf.setText(user[2] or "")
                self.input_tel.setText(user[3] or "")
        except Exception as e:
            print(f"Erro ao carregar perfil: {e}")

    def salvar_dados(self):
        nome = self.input_nome.text().strip()
        email = self.input_email.text().strip()
        cpf = self.input_cpf.text().strip()
        tel = self.input_tel.text().strip()
        senha = self.input_senha.text().strip()

        if not nome or not email:
            QMessageBox.warning(self, "Erro", "Nome e E-mail são obrigatórios.")
            return

        try:
            conn = conectar(); cur = conn.cursor()
            if senha:
                cur.execute("""
                    UPDATE usuarios SET nome=?, email=?, cpf=?, telefone=?, senha_hash=? WHERE id=?
                """, (nome, email, cpf, tel, hash_senha(senha), self.usuario_id))
            else:
                cur.execute("""
                    UPDATE usuarios SET nome=?, email=?, cpf=?, telefone=? WHERE id=?
                """, (nome, email, cpf, tel, self.usuario_id))
            
            conn.commit(); conn.close()
            QMessageBox.information(self, "Sucesso", "Perfil atualizado com sucesso!")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar: {e}")