import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.db import conectar

class TelaAtualizacaoUsuario(QWidget):
    perfil_atualizado = pyqtSignal()

    def __init__(self, user_id, nome_atual, email_atual):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Completar Cadastro")
        self.setFixedSize(400, 450) # Aumentei a altura para caber os novos campos
        
        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QLineEdit { 
                background-color: #1a1a1a; border: 1px solid #333333; 
                border-radius: 6px; padding: 10px; color: white; 
            }
            QLineEdit:focus { border: 1px solid #00ffa3; }
            QPushButton { 
                background-color: #00ffa3; color: black; font-weight: bold; 
                padding: 12px; border-radius: 6px; 
            }
            QPushButton:hover { background-color: #00cc82; }
            QLabel { color: #a4b0be; font-size: 12px; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        titulo = QLabel("📋 DADOS COMPLEMENTARES")
        titulo.setStyleSheet("font-size: 18px; color: #00ffa3;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Nome e Sobrenome
        partes = nome_atual.strip().split(" ", 1)
        self.input_nome = QLineEdit(partes[0])
        self.input_sobrenome = QLineEdit(partes[1] if len(partes) > 1 else "")
        
        lay_h = QHBoxLayout()
        lay_h.addWidget(self.input_nome)
        lay_h.addWidget(self.input_sobrenome)
        layout.addLayout(lay_h)

        # Email
        self.input_email = QLineEdit(email_atual)
        layout.addWidget(QLabel("E-mail:"))
        layout.addWidget(self.input_email)

        # CPF com Máscara
        self.input_cpf = QLineEdit()
        self.input_cpf.setPlaceholderText("000.000.000-00")
        self.input_cpf.setInputMask("000.000.000-00;_") # Máscara fixa
        layout.addWidget(QLabel("CPF:"))
        layout.addWidget(self.input_cpf)

        # Telefone com Máscara (Formato celular com 9 dígitos)
        self.input_tel = QLineEdit()
        self.input_tel.setPlaceholderText("(00) 00000-0000")
        self.input_tel.setInputMask("(00) 00000-0000;_")
        layout.addWidget(QLabel("Telefone:"))
        layout.addWidget(self.input_tel)

        self.btn_salvar = QPushButton("Atualizar e Entrar")
        self.btn_salvar.clicked.connect(self.salvar_dados)
        layout.addWidget(self.btn_salvar)

    def salvar_dados(self):
        nome = self.input_nome.text().strip()
        sobrenome = self.input_sobrenome.text().strip()
        email = self.input_email.text().strip()
        cpf = self.input_cpf.text().strip()
        tel = self.input_tel.text().strip()

        # Validação simples de preenchimento (remover caracteres da máscara para checar)
        clean_cpf = re.sub(r'\D', '', cpf)
        clean_tel = re.sub(r'\D', '', tel)

        if not nome or not sobrenome or len(clean_cpf) < 11 or len(clean_tel) < 10:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha todos os campos corretamente.")
            return

        try:
            conn = conectar()
            cur = conn.cursor()
            
            # 1. Verificar se a tabela usuários tem as colunas, senão criar (Migração de BD)
            # Isso evita que o app trave em clientes antigos
            try:
                cur.execute("ALTER TABLE usuarios ADD COLUMN cpf TEXT")
                cur.execute("ALTER TABLE usuarios ADD COLUMN telefone TEXT")
            except:
                pass # Colunas já existem

            cur.execute("""
                UPDATE usuarios 
                SET nome = ?, email = ?, cpf = ?, telefone = ? 
                WHERE id = ?
            """, (f"{nome} {sobrenome}", email, cpf, tel, self.user_id))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Sucesso", "Cadastro completo!")
            self.perfil_atualizado.emit()
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro: {e}")