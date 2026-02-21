from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QMessageBox, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from database.db import validar_login
from screens.tela_atualizacao import TelaAtualizacaoUsuario

class TelaLogin(QWidget):
    login_sucesso = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login do Sistema")
        self.setFixedSize(360, 280) 

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ---------- TÍTULO ----------
        titulo = QLabel("🔐 Login")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #00ffa3;")
        layout.addWidget(titulo)

        # ---------- CAMPO IDENTIFICADOR ----------
        self.usuario_input = QLineEdit()
        self.usuario_input.setPlaceholderText("E-mail, Nome ou CPF")
        self.usuario_input.setStyleSheet("padding: 10px; border-radius: 5px;")
        
        # Conecta o evento de mudança de texto para aplicar a máscara
        self.usuario_input.textChanged.connect(self.aplicar_mascara_cpf)
        
        self.usuario_input.returnPressed.connect(self.logar)
        layout.addWidget(self.usuario_input)

        # ---------- CAMPO SENHA ----------
        self.senha = QLineEdit()
        self.senha.setPlaceholderText("Senha")
        self.senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.senha.setStyleSheet("padding: 10px; border-radius: 5px;")
        self.senha.returnPressed.connect(self.logar)
        layout.addWidget(self.senha)

        # ---------- BOTÃO ENTRAR ----------
        btn_entrar = QPushButton("ENTRAR NO SISTEMA")
        btn_entrar.setStyleSheet("""
            QPushButton {
                background-color: #00ffa3; color: black; font-weight: bold;
                padding: 12px; border-radius: 5px; margin-top: 10px;
            }
            QPushButton:hover { background-color: #00cc82; }
        """)
        btn_entrar.clicked.connect(self.logar)
        layout.addWidget(btn_entrar)

        self.setStyleSheet("background-color: #0b0b0b; color: white;")

    def aplicar_mascara_cpf(self, texto):
        """Aplica máscara de CPF apenas se o início do texto for numérico"""
        # Remove caracteres de formatação para processar
        texto_limpo = ''.join(filter(str.isdigit, texto))
        
        # Se o usuário digitou letras (ex: e-mail ou nome), não aplica máscara
        if len(texto) > 0 and not texto[0].isdigit():
            return

        # Limita a 11 dígitos numéricos
        texto_limpo = texto_limpo[:11]
        
        formatado = ""
        if len(texto_limpo) <= 3:
            formatado = texto_limpo
        elif len(texto_limpo) <= 6:
            formatado = f"{texto_limpo[:3]}.{texto_limpo[3:]}"
        elif len(texto_limpo) <= 9:
            formatado = f"{texto_limpo[:3]}.{texto_limpo[3:6]}.{texto_limpo[6:]}"
        else:
            formatado = f"{texto_limpo[:3]}.{texto_limpo[3:6]}.{texto_limpo[6:9]}-{texto_limpo[9:]}"

        # Bloqueia sinais para evitar loop infinito ao mudar o texto programaticamente
        self.usuario_input.blockSignals(True)
        self.usuario_input.setText(formatado)
        self.usuario_input.blockSignals(False)

    def logar(self):
        identificador = self.usuario_input.text().strip()
        senha = self.senha.text().strip()

        if not identificador or not senha:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return

        usuario = validar_login(identificador, senha)

        if usuario:
            usuario_id, usuario_nome, usuario_email, usuario_cpf, usuario_tel = usuario
            
            cadastro_incompleto = (
                not usuario_email or "@" not in str(usuario_email) or
                not usuario_cpf or 
                not usuario_tel
            )

            if cadastro_incompleto:
                self.janela_update = TelaAtualizacaoUsuario(usuario_id, usuario_nome, usuario_email)
                self.janela_update.perfil_atualizado.connect(
                    lambda: self.finalizar_login_apos_update(usuario_id)
                )
                self.janela_update.show()
                return 

            self.concluir_login(usuario_id, usuario_nome)
        else:
            QMessageBox.critical(self, "Erro", "Acesso Negado! Verifique os dados.")

    def finalizar_login_apos_update(self, usuario_id):
        from database.db import conectar
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT nome FROM usuarios WHERE id = ?", (usuario_id,))
            resultado = cur.fetchone()
            novo_nome = resultado[0] if resultado else "Usuário"
            conn.close()
            self.concluir_login(usuario_id, novo_nome)
        except Exception as e:
            self.concluir_login(usuario_id, "Usuário")

    def concluir_login(self, id_user, nome_user):
        self.login_sucesso.emit(id_user, nome_user)
        self.close()