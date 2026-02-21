from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from screens.veiculos import TelaVeiculos
from screens.tela_combustivel import TelaCombustivel
from screens.manutencao import TelaManutencao

class TelaGestaoFrota(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestão de Frota Completa")
        self.resize(1150, 750)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Criando o Widget de Abas
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333; background: #0b0b0b; }
            QTabBar::tab {
                background: #1a1a1a; color: #a4b0be;
                padding: 12px 30px; margin: 2px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #252525; color: #00ffa3;
                border-bottom: 2px solid #00ffa3;
            }
        """)

        # Instanciando as telas que já temos
        self.aba_cadastro = TelaVeiculos()
        self.aba_combustivel = TelaCombustivel()
        self.aba_manutencao = TelaManutencao()

        # Adicionando as abas
        self.tabs.addTab(self.aba_cadastro, "🚗 CADASTRO DE VEÍCULOS")
        self.tabs.addTab(self.aba_combustivel, "⛽ ABASTECIMENTOS")
        self.tabs.addTab(self.aba_manutencao, "🔧 MANUTENÇÕES")

        layout.addWidget(self.tabs)

        # Conectar atualizações entre abas
        # Se cadastrar um veículo na Aba 1, as listas das Abas 2 e 3 devem atualizar
        self.aba_cadastro.btn_adicionar.clicked.connect(self.sincronizar_telas)
        self.aba_cadastro.btn_remover.clicked.connect(self.sincronizar_telas)

    def sincronizar_telas(self):
        """Garante que as combos de veículos nas outras abas reflitam as mudanças"""
        self.aba_combustivel.atualizar()
        self.aba_manutencao.atualizar()