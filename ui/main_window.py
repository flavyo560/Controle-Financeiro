import requests
import os
import subprocess
import sys
import urllib.request
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QFrame, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

# Importação das telas principais
from screens.dashboard_financeiro import DashboardFinanceiro
from screens.categorias import TelaCategorias
from screens.despesas import TelaDespesas
from screens.receitas import TelaReceitas
from screens.investimentos import TelaInvestimentos
from screens.combustivel import TelaCombustivel
from screens.manutencao import TelaManutencao
from screens.bancos import TelaBancos
from screens.transferencias import TelaTransferencias 
from screens.veiculos import TelaVeiculos 
from screens.analise_investimentos import AnaliseInvestimentos

# --- IMPORTAÇÃO DOS NOVOS RELATÓRIOS ---
from screens.relatorio_mensal import RelatorioMensal
from screens.relatorio_anual import RelatorioAnual
from screens.relatorio_veiculo import RelatorioVeiculo

# Importação das telas de investimento com tratamento de erro
try:
    from screens.dividendos import TelaDividendos
    from screens.rentabilidade import TelaRentabilidade
    from screens.atualizar_investimento import TelaAtualizarTesouro 
except ImportError:
    class TelaDividendos(QWidget): pass
    class TelaRentabilidade(QWidget): pass
    class TelaAtualizarTesouro(QWidget): pass

from utils.backup import realizar_backup, restaurar_backup
from database.db import resetar_banco, criar_tabelas

# --- CONFIGURAÇÕES DE ATUALIZAÇÃO ---
VERSION_URL = "https://raw.githubusercontent.com/flavyo560/Controle-Financeiro/main/version.txt"
INSTALLER_URL = "https://github.com/flavyo560/Controle-Financeiro/releases/download/V.2.3/Instalador_Controle_Financeiro_V2_3.exe"
VERSION_ATUAL = "2.3"

class MainWindow(QMainWindow):
    def __init__(self):
        # 1. ATUALIZA O BANCO DE DADOS (MIGRAÇÕES)
        criar_tabelas()

        super().__init__()
        self.setWindowTitle("Controle Financeiro - Ultra Dark 2.0")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #0b0b0b;") 

        self.showMaximized()

        central = QWidget()
        self.setCentralWidget(central)
        self.layout_geral = QVBoxLayout(central)
        self.layout_geral.setContentsMargins(0, 0, 0, 0)
        self.layout_geral.setSpacing(0)

        # --- NAVBAR SUPERIOR ---
        self.navbar = QFrame()
        self.navbar.setFixedHeight(60)
        self.navbar.setStyleSheet("""
            QFrame { background-color: #0b0b0b; border-bottom: 2px solid #1f1f1f; }
            QPushButton {
                color: #a4b0be; background: transparent; border: none;
                padding: 10px 15px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { color: white; background-color: #1f1f1f; border-radius: 5px; }
            QPushButton:checked { color: #00ffa3; border-bottom: 2px solid #00ffa3; }
        """)
        
        self.layout_nav = QHBoxLayout(self.navbar)
        self.layout_nav.setContentsMargins(20, 0, 20, 0)

        # --- INICIALIZAÇÃO DAS TELAS ---
        self.stack = QStackedWidget()
        
        self.dashboard = DashboardFinanceiro()
        self.bancos = TelaBancos()
        self.transferencias = TelaTransferencias() 
        self.categorias = TelaCategorias()
        self.receitas = TelaReceitas()
        self.despesas = TelaDespesas()
        self.investimentos = TelaInvestimentos()
        self.analise_inv = AnaliseInvestimentos() 
        self.dividendos = TelaDividendos()
        self.rentabilidade = TelaRentabilidade()
        self.atualizar_tesouro = TelaAtualizarTesouro()
        self.veiculos_cadastro = TelaVeiculos()
        self.combustivel = TelaCombustivel()
        self.manutencao = TelaManutencao()
        
        self.rel_mensal = RelatorioMensal()
        self.rel_anual = RelatorioAnual()
        self.rel_veiculo = RelatorioVeiculo()

        # --- CONEXÃO DE SINAIS ---
        self.bancos.dados_atualizados.connect(self.receitas.atualizar)
        self.bancos.dados_atualizados.connect(self.despesas.atualizar)
        self.bancos.dados_atualizados.connect(self.investimentos.atualizar)
        self.bancos.dados_atualizados.connect(self.transferencias.atualizar) 
        self.bancos.dados_atualizados.connect(self.dashboard.atualizar)
        self.bancos.dados_atualizados.connect(self.combustivel.atualizar)
        self.bancos.dados_atualizados.connect(self.manutencao.atualizar)

        # Adicionando ao Stack
        telas = [
            self.dashboard, self.bancos, self.transferencias, self.categorias, 
            self.receitas, self.despesas, self.investimentos, self.analise_inv, 
            self.dividendos, self.rentabilidade, self.atualizar_tesouro, 
            self.veiculos_cadastro, self.combustivel, self.manutencao,
            self.rel_mensal, self.rel_anual, self.rel_veiculo
        ]
        for t in telas: self.stack.addWidget(t)

        # --- BOTÕES DA NAVBAR ---
        self.botoes = []
        self.btn_dash = self.add_nav_btn("🏠 DASHBOARD", self.dashboard)
        
        self.btn_bancos_menu = QPushButton("🏦 BANCOS  ▾")
        self.btn_bancos_menu.setMenu(self.criar_menu_bancos())
        self.layout_nav.addWidget(self.btn_bancos_menu)
        self.botoes.append(self.btn_bancos_menu)

        self.add_nav_btn("📂 CATEGORIAS", self.categorias)
        self.add_nav_btn("💰 RECEITAS", self.receitas)
        self.add_nav_btn("💸 DESPESAS", self.despesas)
        
        self.btn_inv = QPushButton("📈 INVESTIMENTOS  ▾")
        self.btn_inv.setMenu(self.criar_menu_investimentos())
        self.layout_nav.addWidget(self.btn_inv)
        self.botoes.append(self.btn_inv)

        self.btn_rel_menu = QPushButton("📊 RELATÓRIOS  ▾")
        self.btn_rel_menu.setMenu(self.criar_menu_relatorios())
        self.layout_nav.addWidget(self.btn_rel_menu)
        self.botoes.append(self.btn_rel_menu)

        self.btn_veic = QPushButton("🚗 VEÍCULOS  ▾")
        self.btn_veic.setMenu(self.criar_menu_veiculo())
        self.layout_nav.addWidget(self.btn_veic)
        self.botoes.append(self.btn_veic)

        self.layout_nav.addStretch()

        self.btn_tools = QPushButton("⚙️ FERRAMENTAS  ▾")
        self.btn_tools.setMenu(self.criar_menu_ferramentas())
        self.layout_nav.addWidget(self.btn_tools)

        self.layout_geral.addWidget(self.navbar)
        self.layout_geral.addWidget(self.stack)
        self.btn_dash.setChecked(True)

        # --- VERIFICAÇÃO DE ATUALIZAÇÃO AO INICIAR ---
        self.verificar_e_atualizar()

    def verificar_e_atualizar(self):
        """Verifica se há uma nova versão no GitHub"""
        try:
            response = requests.get(VERSION_URL, timeout=5)
            if response.status_code == 200:
                versao_remota = response.text.strip()
                if versao_remota > VERSION_ATUAL:
                    msg = QMessageBox.question(
                        self, "Atualização disponível!",
                        f"A versão {versao_remota} está disponível. Deseja atualizar agora?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if msg == QMessageBox.StandardButton.Yes:
                        temp_exe = os.path.join(os.getenv("TEMP"), "update_setup.exe")
                        urllib.request.urlretrieve(INSTALLER_URL, temp_exe)
                        subprocess.Popen([temp_exe, "/SILENT", "/CLOSEAPPLICATIONS"])
                        sys.exit()
        except Exception as e:
            print(f"Erro ao verificar atualização: {e}")

    def add_nav_btn(self, texto, tela):
        btn = QPushButton(texto)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.trocar_tela(tela, btn))
        self.layout_nav.addWidget(btn)
        self.botoes.append(btn)
        return btn

    def criar_menu_bancos(self):
        menu = QMenu(self)
        self._estilo_menu(menu)
        ac1 = QAction("🏦 Gerenciar Bancos", self)
        ac1.triggered.connect(lambda: self.trocar_tela(self.bancos, self.btn_bancos_menu))
        ac2 = QAction("🔄 Transferências", self)
        ac2.triggered.connect(lambda: self.trocar_tela(self.transferencias, self.btn_bancos_menu))
        menu.addActions([ac1, ac2])
        return menu

    def criar_menu_investimentos(self):
        menu = QMenu(self)
        self._estilo_menu(menu)
        ac1 = QAction("📝 Gerenciar Ativos", self)
        ac1.triggered.connect(lambda: self.trocar_tela(self.investimentos, self.btn_inv))
        ac_graficos = QAction("📊 Gráficos de Ativos", self)
        ac_graficos.triggered.connect(lambda: self.trocar_tela(self.analise_inv, self.btn_inv))
        ac2 = QAction("💸 Dividendos", self)
        ac2.triggered.connect(lambda: self.trocar_tela(self.dividendos, self.btn_inv))
        ac_extra = QAction("📈 Atualizar Saldo (Tesouro)", self)
        ac_extra.triggered.connect(lambda: self.trocar_tela(self.atualizar_tesouro, self.btn_inv))
        ac3 = QAction("📈 Rentabilidade", self)
        ac3.triggered.connect(lambda: self.trocar_tela(self.rentabilidade, self.btn_inv))
        menu.addActions([ac1, ac_graficos, ac2, ac_extra, ac3])
        return menu

    def criar_menu_relatorios(self):
        menu = QMenu(self)
        self._estilo_menu(menu)
        ac1 = QAction("📅 Relatório Mensal", self)
        ac1.triggered.connect(lambda: self.trocar_tela(self.rel_mensal, self.btn_rel_menu))
        ac2 = QAction("🗓️ Relatório Anual", self)
        ac2.triggered.connect(lambda: self.trocar_tela(self.rel_anual, self.btn_rel_menu))
        ac3 = QAction("🚗 Custos por Veículo", self)
        ac3.triggered.connect(lambda: self.trocar_tela(self.rel_veiculo, self.btn_rel_menu))
        menu.addActions([ac1, ac2, ac3])
        return menu

    def criar_menu_veiculo(self):
        menu = QMenu(self)
        self._estilo_menu(menu)
        ac0 = QAction("🚗 Gerenciar Frota (Cadastro)", self)
        ac0.triggered.connect(lambda: self.trocar_tela(self.veiculos_cadastro, self.btn_veic))
        ac1 = QAction("⛽ Abastecimento", self)
        ac1.triggered.connect(lambda: self.trocar_tela(self.combustivel, self.btn_veic))
        ac2 = QAction("🔧 Manutenção", self)
        ac2.triggered.connect(lambda: self.trocar_tela(self.manutencao, self.btn_veic))
        menu.addActions([ac0, ac1, ac2])
        return menu

    def criar_menu_ferramentas(self):
        menu = QMenu(self)
        self._estilo_menu(menu)
        ac1 = QAction("💾 Realizar Backup", self)
        ac1.triggered.connect(lambda: realizar_backup(self))
        ac2 = QAction("📂 Restaurar Backup", self)
        ac2.triggered.connect(lambda: restaurar_backup(self))
        ac3 = QAction("⚠️ Resetar Todo o Sistema", self)
        ac3.triggered.connect(self.reset_confirm)
        menu.addActions([ac1, ac2, ac3])
        return menu

    def _estilo_menu(self, menu):
        menu.setStyleSheet("""
            QMenu { background-color: #121212; color: white; border: 1px solid #1f1f1f; padding: 5px; } 
            QMenu::item { padding: 8px 25px; border-radius: 4px; }
            QMenu::item:selected { background-color: #00ffa3; color: black; }
        """)

    def reset_confirm(self):
        msg = QMessageBox.question(self, "Resetar Sistema", "Apagar TUDO?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if msg == QMessageBox.StandardButton.Yes:
            resetar_banco()
            self.dashboard.atualizar()

    def trocar_tela(self, tela, botao):
        self.stack.setCurrentWidget(tela)
        for b in self.botoes: b.setChecked(False)
        if botao: botao.setChecked(True)
        if hasattr(tela, "atualizar"): tela.atualizar()
        elif hasattr(tela, "carregar_dados"): tela.carregar_dados()
        elif hasattr(tela, "atualizar_lista"): tela.atualizar_lista()