import sys
import webbrowser
from PyQt6.QtWidgets import QApplication, QMessageBox
from database.db import criar_tabelas, existe_usuario
from screens.login import TelaLogin
from screens.cadastro_usuario import TelaCadastroUsuario
from ui.main_window import MainWindow
from screens.tela_ativacao import TelaAtivacao
from utils.licenca import verificar_status_licenca, ativar_sistema_online

class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        criar_tabelas()
        self.ativador = None
        self.login = None
        self.cadastro = None
        self.main_window = None

    def run(self):
        # Inicia pelo cadastro/login antes de pedir licença
        self.iniciar_fluxo_acesso()
        sys.exit(self.app.exec())

    def iniciar_fluxo_acesso(self):
        if not existe_usuario():
            self.abrir_cadastro()
        else:
            self.abrir_login()

    def abrir_cadastro(self):
        self.cadastro = TelaCadastroUsuario()
        self.cadastro.usuario_criado.connect(self.verificar_licenca_apos_acesso)
        self.cadastro.show()

    def abrir_login(self):
        if self.cadastro: self.cadastro.close()
        self.login = TelaLogin()
        self.login.login_sucesso.connect(self.verificar_licenca_apos_acesso)
        self.login.show()

    def verificar_licenca_apos_acesso(self, *args):
        """Chamado após login/cadastro para validar o PC"""
        status = verificar_status_licenca()
        if status == "VALIDA":
            self.abrir_dashboard()
        else:
            if self.login: self.login.hide()
            if self.cadastro: self.cadastro.hide()
            self.abrir_ativacao()

    def abrir_ativacao(self):
        self.ativador = TelaAtivacao()
        
        # CONECTA O BOTÃO: Aqui resolvemos o problema do clique
        self.ativador.btn_ativar.clicked.connect(self.processar_ativacao_no_banco)
        self.ativador.btn_whatsapp.clicked.connect(self.abrir_contato_whatsapp)
        
        # Sinal para quando a ativação for confirmada pelo Supabase
        self.ativador.ativado_com_sucesso.connect(self.abrir_dashboard)
        self.ativador.show()

    def processar_ativacao_no_banco(self):
        """Lógica que valida a chave no Supabase"""
        chave = self.ativador.input_chave.text().strip()
        if not chave:
            QMessageBox.warning(self.ativador, "Aviso", "Insira uma chave válida.")
            return

        sucesso, msg = ativar_sistema_online(chave)
        if sucesso:
            QMessageBox.information(self.ativador, "Sucesso", msg)
            self.ativador.ativado_com_sucesso.emit() # Fecha ativador e abre dashboard
        else:
            QMessageBox.critical(self.ativador, "Erro", msg)

    def abrir_dashboard(self):
        if self.login: self.login.close()
        if self.cadastro: self.cadastro.close()
        if self.ativador: self.ativador.close()
        self.main_window = MainWindow()
        self.main_window.show()

    def abrir_contato_whatsapp(self):
        numero = "5566992108734" 
        msg = "Olá! Realizei meu cadastro e gostaria da minha chave de ativação."
        webbrowser.open(f"https://wa.me/{numero}?text={msg.replace(' ', '%20')}")