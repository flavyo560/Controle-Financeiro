import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QMessageBox, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from database.db import criar_usuario, conectar

class TelaCadastroUsuario(QWidget):
    usuario_criado = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro Inicial")
        self.setFixedSize(400, 480) # Ajustado para os novos campos
        
        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QLineEdit { 
                background-color: #1a1a1a; border: 1px solid #333333; 
                border-radius: 6px; padding: 10px; color: white; 
            }
            QLineEdit:focus { border: 1px solid #00ffa3; }
            QPushButton { 
                background-color: #00ffa3; color: black; font-weight: bold; 
                padding: 12px; border-radius: 6px; font-size: 14px;
            }
            QPushButton:hover { background-color: #00cc82; }
            QLabel { color: #a4b0be; font-size: 11px; font-weight: bold; margin-top: 5px; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 20, 30, 20)

        titulo = QLabel("CRIAR NOVA CONTA")
        titulo.setStyleSheet("font-size: 18px; color: #00ffa3; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # --- NOME E SOBRENOME ---
        layout.addWidget(QLabel("NOME E SOBRENOME:"))
        layout_nome = QHBoxLayout()
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome")
        
        self.input_sobrenome = QLineEdit()
        self.input_sobrenome.setPlaceholderText("Sobrenome")
        
        layout_nome.addWidget(self.input_nome)
        layout_nome.addWidget(self.input_sobrenome)
        layout.addLayout(layout_nome)

        # --- CPF ---
        layout.addWidget(QLabel("CPF:"))
        self.input_cpf = QLineEdit()
        self.input_cpf.setPlaceholderText("000.000.000-00")
        self.input_cpf.setInputMask("000.000.000-00;_")
        layout.addWidget(self.input_cpf)

        # --- TELEFONE ---
        layout.addWidget(QLabel("TELEFONE:"))
        self.input_tel = QLineEdit()
        self.input_tel.setPlaceholderText("(00) 00000-0000")
        self.input_tel.setInputMask("(00) 00000-0000;_")
        layout.addWidget(self.input_tel)

        # --- EMAIL ---
        layout.addWidget(QLabel("E-MAIL:"))
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("exemplo@email.com")
        layout.addWidget(self.input_email)

        # --- SENHA ---
        layout.addWidget(QLabel("SENHA:"))
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Crie uma senha forte")
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input_senha)

        # --- BOTÃO ---
        self.btn = QPushButton("Finalizar Cadastro")
        self.btn.clicked.connect(self.tentar_criar)
        layout.addWidget(self.btn)

    def validar_email(self, email):
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email)

    def tentar_criar(self):
        nome = self.input_nome.text().strip()
        sobrenome = self.input_sobrenome.text().strip()
        email = self.input_email.text().strip()
        senha = self.input_senha.text().strip()
        cpf = self.input_cpf.text().strip()
        tel = self.input_tel.text().strip()

        # Limpeza para validação
        clean_cpf = re.sub(r'\D', '', cpf)
        clean_tel = re.sub(r'\D', '', tel)

        # 1. Validação de campos vazios ou incompletos
        if not nome or not sobrenome or not senha:
            QMessageBox.warning(self, "Campos Vazios", "Preencha Nome, Sobrenome e Senha.")
            return

        if len(clean_cpf) < 11:
            QMessageBox.warning(self, "CPF Inválido", "Por favor, digite o CPF completo.")
            return

        if len(clean_tel) < 10:
            QMessageBox.warning(self, "Telefone Inválido", "Por favor, digite o telefone completo.")
            return

        if not self.validar_email(email):
            QMessageBox.warning(self, "E-mail Inválido", "Use um formato válido: exemplo@email.com")
            return

        # 2. Executar criação no Banco de Dados
        try:
            # Garante que as colunas novas existam no banco antes de tentar inserir
            self.garantir_colunas()

            nome_completo = f"{nome} {sobrenome}"
            
            # Aqui vamos usar o banco diretamente para incluir os novos campos
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, cpf, telefone) 
                VALUES (?, ?, ?, ?, ?)
            """, (nome_completo, email, senha, cpf, tel))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Sucesso!", "Sua conta foi criada com sucesso!")
            self.usuario_criado.emit()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar usuário: {e}")

    def garantir_colunas(self):
        """Função auxiliar para garantir que o banco suporte CPF e Telefone"""
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("ALTER TABLE usuarios ADD COLUMN cpf TEXT")
            cur.execute("ALTER TABLE usuarios ADD COLUMN telefone TEXT")
            conn.commit()
            conn.close()
        except:
            pass # Colunas já existem