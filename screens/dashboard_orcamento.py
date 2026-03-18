"""
Dashboard de Orçamento.

Exibe visualizações gráficas e métricas do orçamento:
- Gráfico de barras mensal (planejado vs realizado)
- Gráfico de linha de tendência de saldo
- Cards de métricas principais
- Lista de alertas
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.orcamento import (
    obter_orcamento, calcular_totais_mensais, obter_alertas_orcamento
)
from database.orcamento_calculator import OrcamentoCalculator
from utils.logger import logger
from datetime import datetime

# Importar matplotlib para gráficos
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib não disponível - gráficos desabilitados")


class DashboardOrcamento(QWidget):
    """Dashboard visual de acompanhamento do orçamento"""
    
    def __init__(self, orcamento_id: int):
        super().__init__()
        self.orcamento_id = orcamento_id
        self.setWindowTitle("Dashboard - Orçamento")
        self.resize(1100, 600)
        
        # Estilo dark mode
        self.setStyleSheet("""
            QWidget { 
                background-color: #0b0b0b; 
                color: white; 
            }
            QLabel { 
                color: #a4b0be; 
            }
            QPushButton {
                background-color: #1f1f1f;
                color: white;
                border: 1px solid #333333;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                border: 1px solid #ff0055;
            }
            QGroupBox {
                border: 1px solid #333333;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                color: #a4b0be;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QFrame.card {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        # Layout principal com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Título
        orcamento = obter_orcamento(orcamento_id)
        ano = orcamento['ano'] if orcamento else "N/A"
        titulo = QLabel(f"DASHBOARD - ORÇAMENTO {ano}")
        titulo.setStyleSheet("font-size:20px; font-weight:bold; color: #ff0055; margin-bottom: 10px;")
        layout.addWidget(titulo)
        
        # Cards de métricas
        self.criar_cards_metricas(layout)
        
        # Gráficos
        if MATPLOTLIB_AVAILABLE:
            self.criar_graficos(layout)
        else:
            aviso = QLabel("⚠️ Matplotlib não instalado - Gráficos não disponíveis")
            aviso.setStyleSheet("color: #ffc107; font-size: 14px; padding: 20px;")
            layout.addWidget(aviso)
        
        # Lista de alertas
        self.criar_painel_alertas(layout)
        
        # Botão atualizar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_atualizar = QPushButton("Atualizar Dashboard")
        btn_atualizar.clicked.connect(self.atualizar_dashboard)
        btn_layout.addWidget(btn_atualizar)
        layout.addLayout(btn_layout)
        
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Carregar dados
        self.atualizar_dashboard()
    
    def criar_cards_metricas(self, layout):
        """Cria os cards de métricas principais"""
        cards_group = QGroupBox("Métricas Principais")
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        # Card 1: Percentual de Execução Geral
        self.card_percentual = self.criar_card(
            "Execução Geral",
            "0%",
            "#ff0055"
        )
        cards_layout.addWidget(self.card_percentual)
        
        # Card 2: Número de Alertas
        self.card_alertas = self.criar_card(
            "Alertas Ativos",
            "0",
            "#ffc107"
        )
        cards_layout.addWidget(self.card_alertas)
        
        # Card 3: Melhor Mês
        self.card_melhor_mes = self.criar_card(
            "Melhor Mês",
            "-",
            "#28a745"
        )
        cards_layout.addWidget(self.card_melhor_mes)
        
        # Card 4: Pior Mês
        self.card_pior_mes = self.criar_card(
            "Pior Mês",
            "-",
            "#dc3545"
        )
        cards_layout.addWidget(self.card_pior_mes)
        
        cards_group.setLayout(cards_layout)
        layout.addWidget(cards_group)
    
    def criar_card(self, titulo: str, valor: str, cor: str) -> QFrame:
        """Cria um card de métrica"""
        card = QFrame()
        card.setProperty("class", "card")
        card.setMinimumHeight(120)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 12px; color: #a4b0be; font-weight: normal;")
        card_layout.addWidget(lbl_titulo)
        
        lbl_valor = QLabel(valor)
        lbl_valor.setStyleSheet(f"font-size: 32px; color: {cor}; font-weight: bold;")
        lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_valor)
        
        card_layout.addStretch()
        
        # Armazenar referência ao label de valor
        card.lbl_valor = lbl_valor
        
        return card
    
    def criar_graficos(self, layout):
        """Cria os gráficos do dashboard"""
        graficos_group = QGroupBox("Visualizações")
        graficos_layout = QVBoxLayout()
        
        # Gráfico de barras mensal
        self.fig_barras = Figure(figsize=(12, 4), facecolor='#0b0b0b')
        self.canvas_barras = FigureCanvas(self.fig_barras)
        graficos_layout.addWidget(self.canvas_barras)
        
        # Gráfico de linha de tendência
        self.fig_linha = Figure(figsize=(12, 4), facecolor='#0b0b0b')
        self.canvas_linha = FigureCanvas(self.fig_linha)
        graficos_layout.addWidget(self.canvas_linha)
        
        graficos_group.setLayout(graficos_layout)
        layout.addWidget(graficos_group)
    
    def criar_painel_alertas(self, layout):
        """Cria o painel de alertas"""
        alertas_group = QGroupBox("Alertas Críticos")
        alertas_layout = QVBoxLayout()
        
        self.lbl_alertas = QLabel("Carregando alertas...")
        self.lbl_alertas.setWordWrap(True)
        self.lbl_alertas.setStyleSheet("padding: 10px; font-size: 13px;")
        alertas_layout.addWidget(self.lbl_alertas)
        
        alertas_group.setLayout(alertas_layout)
        layout.addWidget(alertas_group)
    
    def atualizar_dashboard(self):
        """Atualiza todos os dados do dashboard"""
        try:
            # Atualizar cards de métricas
            self.atualizar_metricas()
            
            # Atualizar gráficos
            if MATPLOTLIB_AVAILABLE:
                self.atualizar_graficos()
            
            # Atualizar alertas
            self.atualizar_alertas()
            
            logger.info(f"Dashboard atualizado para orçamento {self.orcamento_id}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar dashboard: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar dashboard: {str(e)}")
    
    def atualizar_metricas(self):
        """Atualiza os cards de métricas"""
        try:
            calculator = OrcamentoCalculator(self.orcamento_id)
            
            # Percentual de execução geral
            percentual = calculator.calcular_percentual_execucao_geral()
            self.card_percentual.lbl_valor.setText(f"{percentual:.1f}%")
            
            # Número de alertas
            alertas = obter_alertas_orcamento(self.orcamento_id, 90.0)
            num_alertas = len(alertas)
            self.card_alertas.lbl_valor.setText(str(num_alertas))
            
            # Melhor e pior mês
            melhor_mes, pior_mes = calculator.identificar_melhor_pior_mes()
            
            meses = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            
            if melhor_mes and 1 <= melhor_mes <= 12:
                self.card_melhor_mes.lbl_valor.setText(meses[melhor_mes])
            else:
                self.card_melhor_mes.lbl_valor.setText("-")
            
            if pior_mes and 1 <= pior_mes <= 12:
                self.card_pior_mes.lbl_valor.setText(meses[pior_mes])
            else:
                self.card_pior_mes.lbl_valor.setText("-")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {e}")
    
    def atualizar_graficos(self):
        """Atualiza os gráficos"""
        try:
            # Obter dados
            totais_mensais = calcular_totais_mensais(self.orcamento_id)
            
            # Preparar dados para gráficos
            meses = list(range(1, 13))
            meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                          'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            
            receitas_planejadas = [totais_mensais[m]['planejado_receitas'] for m in meses]
            receitas_realizadas = [totais_mensais[m]['realizado_receitas'] for m in meses]
            despesas_planejadas = [totais_mensais[m]['planejado_despesas'] for m in meses]
            despesas_realizadas = [totais_mensais[m]['realizado_despesas'] for m in meses]
            saldo_planejado = [totais_mensais[m]['saldo_planejado'] for m in meses]
            saldo_realizado = [totais_mensais[m]['saldo_realizado'] for m in meses]
            
            # Gráfico de barras
            self.fig_barras.clear()
            ax1 = self.fig_barras.add_subplot(111)
            ax1.set_facecolor('#0b0b0b')
            
            x = range(len(meses_nomes))
            width = 0.2
            
            # Barras de receitas
            ax1.bar([i - width*1.5 for i in x], receitas_planejadas, width, 
                   label='Receitas Planejadas', color='#28a745', alpha=0.7)
            ax1.bar([i - width*0.5 for i in x], receitas_realizadas, width,
                   label='Receitas Realizadas', color='#20c997', alpha=0.9)
            
            # Barras de despesas
            ax1.bar([i + width*0.5 for i in x], despesas_planejadas, width,
                   label='Despesas Planejadas', color='#dc3545', alpha=0.7)
            ax1.bar([i + width*1.5 for i in x], despesas_realizadas, width,
                   label='Despesas Realizadas', color='#ff6b6b', alpha=0.9)
            
            ax1.set_xlabel('Mês', color='#a4b0be')
            ax1.set_ylabel('Valor (R$)', color='#a4b0be')
            ax1.set_title('Comparação Mensal: Planejado vs Realizado', 
                         color='#ff0055', fontweight='bold', pad=20)
            ax1.set_xticks(x)
            ax1.set_xticklabels(meses_nomes)
            ax1.legend(facecolor='#1a1a1a', edgecolor='#333333', labelcolor='#a4b0be')
            ax1.tick_params(colors='#a4b0be')
            ax1.spines['bottom'].set_color('#333333')
            ax1.spines['top'].set_color('#333333')
            ax1.spines['left'].set_color('#333333')
            ax1.spines['right'].set_color('#333333')
            ax1.grid(True, alpha=0.2, color='#333333')
            
            # Destacar mês atual
            mes_atual = datetime.now().month
            if 1 <= mes_atual <= 12:
                ax1.axvline(x=mes_atual-1, color='#ff0055', linestyle='--', 
                           alpha=0.5, linewidth=2, label='Mês Atual')
            
            self.fig_barras.tight_layout()
            self.canvas_barras.draw()
            
            # Gráfico de linha
            self.fig_linha.clear()
            ax2 = self.fig_linha.add_subplot(111)
            ax2.set_facecolor('#0b0b0b')
            
            ax2.plot(meses_nomes, saldo_planejado, marker='o', linewidth=2,
                    label='Saldo Planejado', color='#17a2b8', markersize=6)
            ax2.plot(meses_nomes, saldo_realizado, marker='s', linewidth=2,
                    label='Saldo Realizado', color='#ffc107', markersize=6)
            
            ax2.axhline(y=0, color='#666666', linestyle='-', alpha=0.5)
            ax2.set_xlabel('Mês', color='#a4b0be')
            ax2.set_ylabel('Saldo (R$)', color='#a4b0be')
            ax2.set_title('Tendência de Saldo ao Longo do Ano',
                         color='#ff0055', fontweight='bold', pad=20)
            ax2.legend(facecolor='#1a1a1a', edgecolor='#333333', labelcolor='#a4b0be')
            ax2.tick_params(colors='#a4b0be')
            ax2.spines['bottom'].set_color('#333333')
            ax2.spines['top'].set_color('#333333')
            ax2.spines['left'].set_color('#333333')
            ax2.spines['right'].set_color('#333333')
            ax2.grid(True, alpha=0.2, color='#333333')
            
            # Destacar mês atual
            if 1 <= mes_atual <= 12:
                ax2.axvline(x=mes_atual-1, color='#ff0055', linestyle='--',
                           alpha=0.5, linewidth=2)
            
            self.fig_linha.tight_layout()
            self.canvas_linha.draw()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar gráficos: {e}")
    
    def atualizar_alertas(self):
        """Atualiza o painel de alertas"""
        try:
            alertas = obter_alertas_orcamento(self.orcamento_id, 90.0)
            
            if not alertas:
                self.lbl_alertas.setText("✓ Nenhum alerta crítico no momento")
                self.lbl_alertas.setStyleSheet("padding: 10px; font-size: 13px; color: #28a745;")
                return
            
            # Mostrar apenas os 5 alertas mais críticos
            alertas_top = alertas[:5]
            
            texto = ""
            meses = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            
            for alerta in alertas_top:
                categoria = alerta['categoria_nome']
                mes = alerta['mes']
                mes_nome = meses[mes] if 1 <= mes <= 12 else str(mes)
                percentual = alerta['percentual_execucao']
                
                texto += f"⚠️ {categoria} ({mes_nome}): {percentual:.1f}% executado\n"
            
            if len(alertas) > 5:
                texto += f"\n... e mais {len(alertas) - 5} alertas"
            
            self.lbl_alertas.setText(texto)
            self.lbl_alertas.setStyleSheet("padding: 10px; font-size: 13px; color: #ffc107;")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar alertas: {e}")
            self.lbl_alertas.setText("Erro ao carregar alertas")
