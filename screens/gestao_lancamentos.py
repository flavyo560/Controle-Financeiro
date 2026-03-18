from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from screens.receitas import TelaReceitas
from screens.despesas import TelaDespesas
from screens.cartoes import TelaCartoes
from screens.investimentos import TelaInvestimentos
from screens.analise_investimentos import AnaliseInvestimentos
from screens.dividendos import TelaDividendos
from screens.atualizar_investimento import TelaAtualizarTesouro
from screens.rentabilidade import TelaRentabilidade


class TelaGestaoLancamentos(QWidget):
    """
    Tela unificada para gerenciar todos os lançamentos financeiros:
    - Receitas
    - Despesas
    - Cartões de Crédito
    - Investimentos (com todas as sub-telas)
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestão de Lançamentos")
        self.resize(1150, 750)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Criando o Widget de Abas
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #333; 
                background: #0b0b0b; 
            }
            QTabBar::tab {
                background: #1a1a1a; 
                color: #a4b0be;
                padding: 12px 25px; 
                margin: 2px;
                border-top-left-radius: 6px; 
                border-top-right-radius: 6px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: #252525; 
                color: #ff0055;
                border-bottom: 2px solid #ff0055;
            }
            QTabBar::tab:hover {
                background: #2d2d2d;
            }
        """)

        # Instanciar as telas
        self.aba_receitas = TelaReceitas()
        self.aba_despesas = TelaDespesas()
        self.aba_cartoes = TelaCartoes()
        self.aba_investimentos = TelaInvestimentos()
        self.aba_graficos_investimentos = AnaliseInvestimentos()
        self.aba_dividendos = TelaDividendos()
        self.aba_atualizar_tesouro = TelaAtualizarTesouro()
        self.aba_rentabilidade = TelaRentabilidade()

        # Adicionar as abas
        self.tabs.addTab(self.aba_receitas, "💰 RECEITAS")
        self.tabs.addTab(self.aba_despesas, "💸 DESPESAS")
        self.tabs.addTab(self.aba_cartoes, "💳 CARTÕES")
        self.tabs.addTab(self.aba_investimentos, "📝 ATIVOS")
        self.tabs.addTab(self.aba_graficos_investimentos, "📊 GRÁFICOS")
        self.tabs.addTab(self.aba_dividendos, "💸 DIVIDENDOS")
        self.tabs.addTab(self.aba_atualizar_tesouro, "📈 ATUALIZAR SALDO")
        self.tabs.addTab(self.aba_rentabilidade, "📈 RENTABILIDADE")

        layout.addWidget(self.tabs)

        # Conectar sinais de atualização entre abas
        abas_com_sinais = [
            self.aba_receitas,
            self.aba_despesas,
            self.aba_cartoes,
            self.aba_investimentos,
            self.aba_dividendos,
            self.aba_rentabilidade
        ]
        
        for aba in abas_com_sinais:
            if hasattr(aba, 'dados_atualizados'):
                aba.dados_atualizados.connect(self.sincronizar_telas)

    def sincronizar_telas(self):
        """
        Sincroniza os dados entre as abas quando houver alterações.
        Garante que todas as telas reflitam as mudanças mais recentes.
        """
        try:
            # Atualizar cada aba que tem método atualizar
            abas = [
                self.aba_receitas,
                self.aba_despesas,
                self.aba_cartoes,
                self.aba_investimentos,
                self.aba_graficos_investimentos,
                self.aba_dividendos,
                self.aba_atualizar_tesouro,
                self.aba_rentabilidade
            ]
            
            for aba in abas:
                if hasattr(aba, 'atualizar'):
                    aba.atualizar()
        except Exception as e:
            print(f"Erro ao sincronizar telas: {e}")
