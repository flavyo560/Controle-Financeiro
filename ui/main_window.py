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
from screens.bancos import TelaBancos
from screens.transferencias import TelaTransferencias
from screens.analise_investimentos import AnaliseInvestimentos
from screens.gestao_frota import TelaGestaoFrota
from screens.gestao_lancamentos import TelaGestaoLancamentos
from screens.cartoes import TelaCartoes
from screens.orcamento import TelaOrcamento

# --- IMPORTAÇÃO DOS NOVOS RELATÓRIOS ---
from screens.relatorio_mensal import RelatorioMensal
from screens.relatorio_anual import RelatorioAnual
from screens.relatorio_veiculo import RelatorioVeiculo

# Importação direta das telas de investimento
from screens.dividendos import TelaDividendos
from screens.rentabilidade import TelaRentabilidade
from screens.atualizar_investimento import TelaAtualizarTesouro 

from utils.backup import realizar_backup, restaurar_backup
from database import resetar_banco, criar_tabelas, conectar

# --- CONFIGURAÇÕES DE ATUALIZAÇÃO ---
VERSION_URL = "https://raw.githubusercontent.com/flavyo560/Controle-Financeiro/main/version.txt"
INSTALLER_URL = "https://github.com/flavyo560/Controle-Financeiro/releases/download/V.2.3/Instalador_Controle_Financeiro_V2_3.exe"
VERSION_ATUAL = "2.4"

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

        # --- INICIALIZAÇÃO DAS TELAS (LAZY LOADING) ---
        self.stack = QStackedWidget()
        
        # Dicionário para armazenar as telas (lazy loading)
        self._telas_cache = {}
        
        # Apenas o Dashboard é carregado imediatamente (tela inicial)
        self.dashboard = DashboardFinanceiro()
        self._telas_cache['dashboard'] = self.dashboard
        self.stack.addWidget(self.dashboard)
        
        # Todas as outras telas serão criadas sob demanda
        self.bancos = None
        self.transferencias = None
        self.categorias = None
        self.receitas = None
        self.despesas = None
        self.investimentos = None
        self.analise_inv = None
        self.dividendos = None
        self.rentabilidade = None
        self.atualizar_tesouro = None
        self.gestao_frota = None
        self.gestao_lancamentos = None
        self.cartoes = None
        self.orcamento = None
        self.rel_mensal = None
        self.rel_anual = None
        self.rel_veiculo = None

        # --- CONEXÃO DE SINAIS (será feita quando as telas forem criadas) ---
        # Os sinais serão conectados no método _conectar_sinais_tela()

        # --- BOTÕES DA NAVBAR ---
        self.botoes = []
        self.btn_dash = self.add_nav_btn("🏠 DASHBOARD", self.dashboard)  # Dashboard já está criado
        
        self.btn_bancos_menu = QPushButton("🏦 BANCOS  ▾")
        self.btn_bancos_menu.setMenu(self.criar_menu_bancos())
        self.layout_nav.addWidget(self.btn_bancos_menu)
        self.botoes.append(self.btn_bancos_menu)

        self.add_nav_btn("📂 CATEGORIAS", 'categorias')
        
        # Menu de Lançamentos (Receitas, Despesas, Cartões, Investimentos)
        self.btn_lancamentos_menu = QPushButton("📝 LANÇAMENTOS  ▾")
        self.btn_lancamentos_menu.setMenu(self.criar_menu_lancamentos())
        self.layout_nav.addWidget(self.btn_lancamentos_menu)
        self.botoes.append(self.btn_lancamentos_menu)
        
        self.add_nav_btn("📊 ORÇAMENTO", 'orcamento')

        self.btn_rel_menu = QPushButton("📊 RELATÓRIOS  ▾")
        self.btn_rel_menu.setMenu(self.criar_menu_relatorios())
        self.layout_nav.addWidget(self.btn_rel_menu)
        self.botoes.append(self.btn_rel_menu)

        self.btn_veic = self.add_nav_btn("🚗 FROTA", 'gestao_frota')

        self.layout_nav.addStretch()

        self.btn_tools = QPushButton("⚙️ FERRAMENTAS  ▾")
        self.btn_tools.setMenu(self.criar_menu_ferramentas())
        self.layout_nav.addWidget(self.btn_tools)

        self.btn_perfil = QPushButton("👤 PERFIL")
        self.btn_perfil.clicked.connect(self.abrir_perfil)
        self.layout_nav.addWidget(self.btn_perfil)

        self.layout_geral.addWidget(self.navbar)
        self.layout_geral.addWidget(self.stack)
        self.btn_dash.setChecked(True)

        # --- VERIFICAÇÃO DE ATUALIZAÇÃO AO INICIAR ---
        self.verificar_e_atualizar()
        
        # --- GERAÇÕES AUTOMÁTICAS NO STARTUP ---
        self.executar_geracoes_automaticas()

    def executar_geracoes_automaticas(self):
        """
        Executa todas as gerações automáticas no startup.
        Exibe indicador visual durante execução.
        Registra erros no log mas não interrompe inicialização.
        """
        from database.db import (
            gerar_parcelas_pendentes,
            gerar_lancamentos_recorrentes,
            gerar_despesas_faturas_vencidas
        )
        from utils.logger import logger
        
        try:
            # Exibir indicador de carregamento
            self.statusBar().showMessage("Gerando lançamentos automáticos...")
            
            # Executar gerações
            parcelas = gerar_parcelas_pendentes()
            recorrentes = gerar_lancamentos_recorrentes()
            faturas = gerar_despesas_faturas_vencidas()
            
            # Log de sucesso
            logger.info(f"Gerações automáticas: {parcelas} parcelas, "
                       f"{recorrentes} recorrentes, {faturas} faturas")
            
            # Limpar status bar
            self.statusBar().clearMessage()
            
            # Atualizar interface se houver novos lançamentos
            if parcelas + recorrentes + faturas > 0:
                self.dashboard.atualizar()
                self.despesas.atualizar()
                
        except Exception as e:
            logger.error(f"Erro nas gerações automáticas: {e}", exc_info=True)
            self.statusBar().showMessage("Erro ao gerar lançamentos automáticos", 5000)

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
        ac1.triggered.connect(lambda: self.trocar_tela('bancos', self.btn_bancos_menu))
        ac2 = QAction("🔄 Transferências", self)
        ac2.triggered.connect(lambda: self.trocar_tela('transferencias', self.btn_bancos_menu))
        menu.addActions([ac1, ac2])
        return menu

    def criar_menu_lancamentos(self):
        """Cria o menu dropdown para Lançamentos"""
        menu = QMenu(self)
        self._estilo_menu(menu)
        
        # Opção única para abrir a tela unificada com abas
        ac_unificado = QAction("📝 Gerenciar Lançamentos", self)
        ac_unificado.triggered.connect(lambda: self.trocar_tela('gestao_lancamentos', self.btn_lancamentos_menu))
        
        menu.addAction(ac_unificado)
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
        ac1.triggered.connect(lambda: self.trocar_tela('rel_mensal', self.btn_rel_menu))
        ac2 = QAction("🗓️ Relatório Anual", self)
        ac2.triggered.connect(lambda: self.trocar_tela('rel_anual', self.btn_rel_menu))
        ac3 = QAction("🚗 Custos por Veículo", self)
        ac3.triggered.connect(lambda: self.trocar_tela('rel_veiculo', self.btn_rel_menu))
        menu.addActions([ac1, ac2, ac3])
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

    def _criar_tela(self, nome_tela):
        """Cria uma tela sob demanda (lazy loading)"""
        if nome_tela in self._telas_cache:
            return self._telas_cache[nome_tela]
        
        # Mapeamento de nomes para classes
        mapa_telas = {
            'bancos': (TelaBancos, 'bancos'),
            'transferencias': (TelaTransferencias, 'transferencias'),
            'categorias': (TelaCategorias, 'categorias'),
            'receitas': (TelaReceitas, 'receitas'),
            'despesas': (TelaDespesas, 'despesas'),
            'investimentos': (TelaInvestimentos, 'investimentos'),
            'analise_inv': (AnaliseInvestimentos, 'analise_inv'),
            'dividendos': (TelaDividendos, 'dividendos'),
            'rentabilidade': (TelaRentabilidade, 'rentabilidade'),
            'atualizar_tesouro': (TelaAtualizarTesouro, 'atualizar_tesouro'),
            'gestao_frota': (TelaGestaoFrota, 'gestao_frota'),
            'gestao_lancamentos': (TelaGestaoLancamentos, 'gestao_lancamentos'),
            'cartoes': (TelaCartoes, 'cartoes'),
            'orcamento': (TelaOrcamento, 'orcamento'),
            'rel_mensal': (RelatorioMensal, 'rel_mensal'),
            'rel_anual': (RelatorioAnual, 'rel_anual'),
            'rel_veiculo': (RelatorioVeiculo, 'rel_veiculo'),
        }
        
        if nome_tela not in mapa_telas:
            return None
        
        classe, attr_name = mapa_telas[nome_tela]
        
        # Criar a tela
        tela = classe()
        setattr(self, attr_name, tela)
        
        # Adicionar ao stack
        self.stack.addWidget(tela)
        
        # Armazenar no cache
        self._telas_cache[nome_tela] = tela
        
        # Conectar sinais
        self._conectar_sinais_tela(nome_tela, tela)
        
        return tela
    
    def _conectar_sinais_tela(self, nome_tela, tela):
        """Conecta os sinais de uma tela específica"""
        try:
            # Conexões com bancos
            if nome_tela == 'bancos' and hasattr(tela, 'dados_atualizados'):
                if self.receitas: tela.dados_atualizados.connect(self.receitas.atualizar)
                if self.despesas: tela.dados_atualizados.connect(self.despesas.atualizar)
                if self.investimentos: tela.dados_atualizados.connect(self.investimentos.atualizar)
                if self.transferencias: tela.dados_atualizados.connect(self.transferencias.atualizar)
                if self.cartoes: tela.dados_atualizados.connect(self.cartoes.atualizar)
                tela.dados_atualizados.connect(self.dashboard.atualizar)
            
            # Conexões com receitas
            elif nome_tela == 'receitas' and hasattr(tela, 'dados_atualizados'):
                tela.dados_atualizados.connect(self.dashboard.atualizar)
                tela.dados_atualizados.connect(self.on_dados_financeiros_atualizados)
            
            # Conexões com despesas
            elif nome_tela == 'despesas' and hasattr(tela, 'dados_atualizados'):
                tela.dados_atualizados.connect(self.dashboard.atualizar)
                tela.dados_atualizados.connect(self.on_dados_financeiros_atualizados)
            
            # Conexões com transferências
            elif nome_tela == 'transferencias' and hasattr(tela, 'dados_atualizados'):
                tela.dados_atualizados.connect(self.dashboard.atualizar)
            
            # Conexões com cartões
            elif nome_tela == 'cartoes' and hasattr(tela, 'dados_atualizados'):
                if self.bancos: tela.dados_atualizados.connect(self.bancos.atualizar)
                tela.dados_atualizados.connect(self.dashboard.atualizar)
            
            # Conexões com categorias
            elif nome_tela == 'categorias' and hasattr(tela, 'dados_atualizados'):
                tela.dados_atualizados.connect(self.on_categorias_atualizadas)
            
            # Conexões com orçamento
            elif nome_tela == 'orcamento' and hasattr(tela, 'dados_atualizados'):
                tela.dados_atualizados.connect(self.dashboard.atualizar)
        except Exception as e:
            print(f"Erro ao conectar sinais da tela {nome_tela}: {e}")

    def trocar_tela(self, tela_ou_nome, botao):
        """Troca para uma tela, criando-a sob demanda se necessário"""
        # Se recebeu um nome de tela (string), criar/obter a tela
        if isinstance(tela_ou_nome, str):
            tela = self._criar_tela(tela_ou_nome)
            if tela is None:
                return
        else:
            # Se recebeu a tela diretamente, usar ela
            tela = tela_ou_nome
        
        # Trocar para a tela
        self.stack.setCurrentWidget(tela)
        for b in self.botoes: b.setChecked(False)
        if botao: botao.setChecked(True)
        if hasattr(tela, "atualizar"): tela.atualizar()
        elif hasattr(tela, "carregar_dados"): tela.carregar_dados()
        elif hasattr(tela, "atualizar_lista"): tela.atualizar_lista()

    def trocar_tela_old(self, tela, botao):
        self.stack.setCurrentWidget(tela)
        for b in self.botoes: b.setChecked(False)
        if botao: botao.setChecked(True)
        if hasattr(tela, "atualizar"): tela.atualizar()
        elif hasattr(tela, "carregar_dados"): tela.carregar_dados()
        elif hasattr(tela, "atualizar_lista"): tela.atualizar_lista()

    def on_dados_financeiros_atualizados(self):
        """
        Handler para atualização de dados financeiros (receitas/despesas).
        Recalcula valores realizados do orçamento automaticamente.
        """
        try:
            # Atualizar orçamento se estiver carregado
            if hasattr(self.orcamento, 'orcamento_id_atual') and self.orcamento.orcamento_id_atual:
                self.orcamento.atualizar_matriz()
                self.orcamento.atualizar_painel_informacoes()
                self.orcamento.atualizar_alertas()
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Erro ao atualizar orçamento após mudança financeira: {e}")
    
    def on_categorias_atualizadas(self):
        """
        Handler para atualização de categorias.
        Recarrega lista de categorias no orçamento.
        """
        try:
            # Atualizar orçamento se estiver carregado
            if hasattr(self.orcamento, 'orcamento_id_atual') and self.orcamento.orcamento_id_atual:
                # Recarregar categorias
                self.orcamento.carregar_categorias()
                # Reconfigurar tabela com novas categorias
                self.orcamento.configurar_tabela()
                # Atualizar matriz
                self.orcamento.atualizar_matriz()
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Erro ao atualizar orçamento após mudança de categorias: {e}")

    def abrir_perfil(self):
        try:
            from screens.tela_atualizacao import TelaAtualizacaoUsuario
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome, email FROM usuarios LIMIT 1")
            row = cur.fetchone()
            conn.close()
            if row:
                self.janela_perfil = TelaAtualizacaoUsuario(row[0], row[1], row[2])
                self.janela_perfil.perfil_atualizado.connect(lambda: None)
                self.janela_perfil.show()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir perfil: {e}")
