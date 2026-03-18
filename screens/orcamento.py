from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QLabel, QHeaderView, QGroupBox, QDialog,
    QLineEdit, QDialogButtonBox, QMenu, QListWidget, QListWidgetItem,
    QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QAction
from database.orcamento import (
    criar_orcamento, listar_orcamentos, obter_orcamento,
    listar_itens_orcamento, criar_item_orcamento,
    copiar_orcamento_ano_anterior, aplicar_valor_padrao_categoria,
    calcular_valores_realizados, calcular_totais_mensais,
    calcular_totais_categorias, obter_alertas_orcamento,
    atualizar_status_orcamento
)
from database.orcamento_calculator import OrcamentoCalculator
from database.db import obter_categorias
from models.validators import OrcamentoModel, ItemOrcamentoModel
from pydantic import ValidationError
from utils.logger import logger
from decimal import Decimal
from datetime import datetime


class TelaOrcamento(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orçamento e Planejamento Financeiro")
        self.resize(1100, 600)

        self.orcamento_id_atual = None
        self.categorias_receitas = []
        self.categorias_despesas = []
        self.orcamento_ativo = True  # Flag para controlar se orçamento está ativo

        # Estilo dark mode
        self.setStyleSheet("""
            QWidget { 
                background-color: #0b0b0b; 
                color: white; 
            }
            QLabel { 
                color: #a4b0be; 
                font-weight: bold; 
            }
            QLineEdit, QComboBox {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #ff0055;
            }
            QTableWidget {
                background-color: #121212;
                border: 1px solid #1f1f1f;
                gridline-color: #252525;
                color: white;
                selection-background-color: #ff0055;
                selection-color: white;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #a4b0be;
                padding: 5px;
                border: 1px solid #1f1f1f;
                font-weight: bold;
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
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Título
        titulo = QLabel("ORÇAMENTO E PLANEJAMENTO FINANCEIRO")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #ff0055; margin-bottom: 5px;")
        layout.addWidget(titulo)

        # Barra de controle superior
        controle_layout = QHBoxLayout()
        controle_layout.setSpacing(10)

        # ComboBox para seleção de orçamento
        self.combo_orcamento = QComboBox()
        self.combo_orcamento.setMinimumWidth(200)
        self.combo_orcamento.currentIndexChanged.connect(self.on_orcamento_selecionado)
        controle_layout.addWidget(QLabel("Orçamento:"))
        controle_layout.addWidget(self.combo_orcamento)
        
        # Checkbox para mostrar arquivados
        self.check_mostrar_arquivados = QCheckBox("Mostrar Arquivados")
        self.check_mostrar_arquivados.stateChanged.connect(self.carregar_lista_orcamentos)
        controle_layout.addWidget(self.check_mostrar_arquivados)

        controle_layout.addStretch()

        # Botões de ação
        btn_novo = QPushButton("Novo Orçamento")
        btn_novo.clicked.connect(self.criar_novo_orcamento)
        controle_layout.addWidget(btn_novo)

        btn_copiar = QPushButton("Copiar de Ano Anterior")
        btn_copiar.clicked.connect(self.copiar_de_ano_anterior)
        controle_layout.addWidget(btn_copiar)
        
        self.btn_desativar = QPushButton("Desativar Orçamento")
        self.btn_desativar.clicked.connect(self.desativar_orcamento)
        controle_layout.addWidget(self.btn_desativar)

        layout.addLayout(controle_layout)

        # Tabela de valores (matriz)
        self.tabela = QTableWidget()
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.tabela.cellChanged.connect(self.on_celula_editada)
        self.tabela.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabela.customContextMenuRequested.connect(self.mostrar_menu_contexto)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabela)

        # Painel de informações
        self.criar_painel_informacoes(layout)

        # Carregar dados iniciais
        self.carregar_lista_orcamentos()

    def criar_painel_informacoes(self, layout):
        """Cria o painel de informações com totais e resumos"""
        info_group = QGroupBox("Resumo")
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)

        # Labels para totais
        self.lbl_receitas_planejadas = QLabel("Receitas Planejadas: R$ 0,00")
        self.lbl_receitas_realizadas = QLabel("Receitas Realizadas: R$ 0,00")
        self.lbl_despesas_planejadas = QLabel("Despesas Planejadas: R$ 0,00")
        self.lbl_despesas_realizadas = QLabel("Despesas Realizadas: R$ 0,00")
        self.lbl_saldo_planejado = QLabel("Saldo Planejado: R$ 0,00")
        self.lbl_saldo_realizado = QLabel("Saldo Realizado: R$ 0,00")
        self.lbl_percentual_execucao = QLabel("Execução Geral: 0%")

        info_layout.addWidget(self.lbl_receitas_planejadas)
        info_layout.addWidget(self.lbl_receitas_realizadas)
        info_layout.addWidget(self.lbl_despesas_planejadas)
        info_layout.addWidget(self.lbl_despesas_realizadas)
        info_layout.addWidget(self.lbl_saldo_planejado)
        info_layout.addWidget(self.lbl_saldo_realizado)
        info_layout.addWidget(self.lbl_percentual_execucao)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Painel de alertas
        self.criar_painel_alertas(layout)

    def criar_painel_alertas(self, layout):
        """Cria o painel de alertas"""
        alertas_group = QGroupBox("Alertas de Orçamento")
        alertas_layout = QVBoxLayout()
        
        # Lista de alertas
        self.lista_alertas = QListWidget()
        self.lista_alertas.setMaximumHeight(150)
        self.lista_alertas.itemDoubleClicked.connect(self.on_alerta_clicado)
        alertas_layout.addWidget(self.lista_alertas)
        
        alertas_group.setLayout(alertas_layout)
        layout.addWidget(alertas_group)

    def carregar_lista_orcamentos(self):
        """Carrega a lista de orçamentos no ComboBox"""
        try:
            self.combo_orcamento.blockSignals(True)
            self.combo_orcamento.clear()

            # Verificar se deve mostrar arquivados
            apenas_ativos = not self.check_mostrar_arquivados.isChecked()
            orcamentos = listar_orcamentos(apenas_ativos=apenas_ativos)
            
            if not orcamentos:
                self.combo_orcamento.addItem("Nenhum orçamento criado", None)
                self.combo_orcamento.blockSignals(False)
                return

            for orc in orcamentos:
                ano = orc['ano']
                status = orc['status']
                orcamento_id = orc['id']
                
                # Adicionar indicador de status
                texto = f"Orçamento {ano}"
                if status == 'inativo':
                    texto += " (Arquivado)"
                
                self.combo_orcamento.addItem(texto, orcamento_id)

            self.combo_orcamento.blockSignals(False)
            
            # Selecionar o primeiro orçamento
            if orcamentos:
                self.combo_orcamento.setCurrentIndex(0)
                self.on_orcamento_selecionado(0)

        except Exception as e:
            logger.error(f"Erro ao carregar lista de orçamentos: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar orçamentos: {str(e)}")

    def on_orcamento_selecionado(self, index):
        """Callback quando um orçamento é selecionado no ComboBox"""
        orcamento_id = self.combo_orcamento.currentData()
        if orcamento_id:
            self.carregar_orcamento(orcamento_id)

    def carregar_orcamento(self, orcamento_id: int):
        """Carrega um orçamento específico e atualiza a interface"""
        try:
            self.orcamento_id_atual = orcamento_id
            
            # Obter dados do orçamento
            orcamento = obter_orcamento(orcamento_id)
            if orcamento:
                self.orcamento_ativo = (orcamento['status'] == 'ativo')
                
                # Atualizar botão de desativar/reativar
                if self.orcamento_ativo:
                    self.btn_desativar.setText("Desativar Orçamento")
                else:
                    self.btn_desativar.setText("Reativar Orçamento")
                
                # Bloquear edição se inativo
                self.tabela.setEnabled(self.orcamento_ativo)
            
            # Carregar categorias
            self.carregar_categorias()
            
            # Configurar tabela
            self.configurar_tabela()
            
            # Carregar dados
            self.atualizar_matriz()
            
            # Atualizar painel de informações
            self.atualizar_painel_informacoes()
            
            # Atualizar alertas
            self.atualizar_alertas()

        except Exception as e:
            logger.error(f"Erro ao carregar orçamento {orcamento_id}: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar orçamento: {str(e)}")

    def carregar_categorias(self):
        """Carrega as categorias de receitas e despesas"""
        try:
            categorias = obter_categorias()
            self.categorias_receitas = [c for c in categorias if c['tipo'] == 'receita']
            self.categorias_despesas = [c for c in categorias if c['tipo'] == 'despesa']
        except Exception as e:
            logger.error(f"Erro ao carregar categorias: {e}")
            self.categorias_receitas = []
            self.categorias_despesas = []

    def configurar_tabela(self):
        """Configura a estrutura da tabela (colunas e linhas)"""
        # Bloquear sinais durante configuração
        self.tabela.blockSignals(True)
        
        # 13 colunas: Categoria + 12 meses
        self.tabela.setColumnCount(13)
        
        # Cabeçalhos
        headers = ["Categoria", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                   "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        self.tabela.setHorizontalHeaderLabels(headers)
        
        # Número de linhas: receitas + despesas + 2 linhas de separação/totais
        num_linhas = len(self.categorias_receitas) + len(self.categorias_despesas) + 3
        self.tabela.setRowCount(num_linhas)
        
        # Desbloquear sinais
        self.tabela.blockSignals(False)

    def atualizar_matriz(self):
        """Atualiza a matriz com os valores planejados e realizados"""
        if not self.orcamento_id_atual:
            return

        try:
            self.tabela.blockSignals(True)
            
            # Carregar itens do orçamento
            itens = listar_itens_orcamento(self.orcamento_id_atual)
            itens_dict = {}
            for item in itens:
                key = (item['categoria_id'], item['mes'])
                itens_dict[key] = item['valor_planejado']
            
            # Carregar valores realizados
            valores_realizados = calcular_valores_realizados(self.orcamento_id_atual)
            
            # Preencher receitas
            linha = 0
            for cat in self.categorias_receitas:
                # Coluna 0: nome da categoria
                item_cat = QTableWidgetItem(cat['nome'])
                item_cat.setFlags(item_cat.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabela.setItem(linha, 0, item_cat)
                
                # Colunas 1-12: valores dos meses
                for mes in range(1, 13):
                    valor_planejado = itens_dict.get((cat['id'], mes), Decimal('0.00'))
                    valor_realizado = valores_realizados.get(cat['id'], {}).get(mes, Decimal('0.00'))
                    
                    # Exibir valor planejado (editável)
                    item = QTableWidgetItem(f"{float(valor_planejado):.2f}")
                    item.setData(Qt.ItemDataRole.UserRole, cat['id'])  # Armazenar categoria_id
                    item.setData(Qt.ItemDataRole.UserRole + 1, mes)  # Armazenar mês
                    self.tabela.setItem(linha, mes, item)
                
                linha += 1
            
            # Linha de separação
            for col in range(13):
                item = QTableWidgetItem("---")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabela.setItem(linha, col, item)
            linha += 1
            
            # Preencher despesas
            for cat in self.categorias_despesas:
                # Coluna 0: nome da categoria
                item_cat = QTableWidgetItem(cat['nome'])
                item_cat.setFlags(item_cat.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabela.setItem(linha, 0, item_cat)
                
                # Colunas 1-12: valores dos meses
                for mes in range(1, 13):
                    valor_planejado = itens_dict.get((cat['id'], mes), Decimal('0.00'))
                    valor_realizado = valores_realizados.get(cat['id'], {}).get(mes, Decimal('0.00'))
                    
                    # Exibir valor planejado (editável)
                    item = QTableWidgetItem(f"{float(valor_planejado):.2f}")
                    item.setData(Qt.ItemDataRole.UserRole, cat['id'])  # Armazenar categoria_id
                    item.setData(Qt.ItemDataRole.UserRole + 1, mes)  # Armazenar mês
                    self.tabela.setItem(linha, mes, item)
                
                linha += 1
            
            self.tabela.blockSignals(False)
            
            # Aplicar cores de status
            self.aplicar_cores_status()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar matriz: {e}")
            self.tabela.blockSignals(False)
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar matriz: {str(e)}")
    def aplicar_cores_status(self):
        """Aplica cores de status (verde/amarelo/vermelho) nas células"""
        if not self.orcamento_id_atual:
            return

        try:
            calculator = OrcamentoCalculator(self.orcamento_id_atual)

            # Aplicar cores nas receitas
            linha = 0
            for cat in self.categorias_receitas:
                for mes in range(1, 13):
                    status = calculator.calcular_status_item(cat['id'], mes, 'receita')
                    item = self.tabela.item(linha, mes)
                    if item:
                        self.aplicar_cor_por_status(item, status)
                linha += 1

            # Pular linha de separação
            linha += 1

            # Aplicar cores nas despesas
            for cat in self.categorias_despesas:
                for mes in range(1, 13):
                    status = calculator.calcular_status_item(cat['id'], mes, 'despesa')
                    item = self.tabela.item(linha, mes)
                    if item:
                        self.aplicar_cor_por_status(item, status)
                linha += 1

        except Exception as e:
            logger.error(f"Erro ao aplicar cores de status: {e}")

    def aplicar_cor_por_status(self, item: QTableWidgetItem, status: str):
        """Aplica cor de fundo baseada no status"""
        if status == 'verde':
            item.setBackground(QColor(34, 139, 34, 100))  # Verde com transparência
        elif status == 'amarelo':
            item.setBackground(QColor(255, 193, 7, 100))  # Amarelo com transparência
        elif status == 'vermelho':
            item.setBackground(QColor(220, 53, 69, 100))  # Vermelho com transparência
        else:
            item.setBackground(QColor(0, 0, 0, 0))  # Transparente


    def on_celula_editada(self, row: int, col: int):
        """Callback quando uma célula é editada"""
        if col == 0:  # Coluna de categoria não é editável
            return
        
        if not self.orcamento_id_atual:
            return
        
        # Bloquear edição se orçamento inativo
        if not self.orcamento_ativo:
            QMessageBox.warning(
                self,
                "Orçamento Inativo",
                "Este orçamento está arquivado e não pode ser editado.\n\n"
                "Para editar, reative o orçamento primeiro."
            )
            self.atualizar_matriz()  # Restaurar valor anterior
            return
        
        try:
            item = self.tabela.item(row, col)
            if not item:
                return
            
            # Obter categoria_id e mês armazenados no item
            categoria_id = item.data(Qt.ItemDataRole.UserRole)
            mes = item.data(Qt.ItemDataRole.UserRole + 1)
            
            if not categoria_id or not mes:
                return
            
            # Obter valor digitado
            valor_texto = item.text().strip()
            if not valor_texto:
                valor_texto = "0.00"
            
            # Validar usando Pydantic
            try:
                item_model = ItemOrcamentoModel(
                    orcamento_id=self.orcamento_id_atual,
                    categoria_id=categoria_id,
                    mes=mes,
                    valor_planejado=Decimal(valor_texto)
                )
            except ValidationError as ve:
                QMessageBox.warning(self, "Validação", f"Valor inválido: {ve}")
                self.atualizar_matriz()  # Restaurar valor anterior
                return
            
            # Salvar no banco (converter Decimal para float para SQLite)
            criar_item_orcamento(
                self.orcamento_id_atual,
                categoria_id,
                mes,
                float(item_model.valor_planejado)
            )
            
            # Atualizar painel de informações
            self.atualizar_painel_informacoes()
            
            # Aplicar cores de status
            self.aplicar_cores_status()
            
            # Atualizar alertas
            self.atualizar_alertas()
            
            # Emitir sinal de atualização
            self.dados_atualizados.emit()
            
        except Exception as e:
            logger.error(f"Erro ao salvar valor editado: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")
            self.atualizar_matriz()  # Restaurar valor anterior

    def atualizar_painel_informacoes(self):
        """Atualiza o painel de informações com totais"""
        if not self.orcamento_id_atual:
            return
        
        try:
            # Calcular totais
            totais_categorias = calcular_totais_categorias(self.orcamento_id_atual)
            
            # Separar receitas e despesas
            total_receitas_planejadas = Decimal('0.00')
            total_receitas_realizadas = Decimal('0.00')
            total_despesas_planejadas = Decimal('0.00')
            total_despesas_realizadas = Decimal('0.00')
            
            for cat_id, dados in totais_categorias.items():
                # Verificar se é receita ou despesa
                cat = next((c for c in self.categorias_receitas if c['id'] == cat_id), None)
                if cat:
                    total_receitas_planejadas += Decimal(str(dados['planejado']))
                    total_receitas_realizadas += Decimal(str(dados['realizado']))
                else:
                    total_despesas_planejadas += Decimal(str(dados['planejado']))
                    total_despesas_realizadas += Decimal(str(dados['realizado']))
            
            # Calcular saldos
            saldo_planejado = total_receitas_planejadas - total_despesas_planejadas
            saldo_realizado = total_receitas_realizadas - total_despesas_realizadas
            
            # Calcular percentual de execução geral
            calculator = OrcamentoCalculator(self.orcamento_id_atual)
            percentual_geral = calculator.calcular_percentual_execucao_geral()
            
            # Atualizar labels
            self.lbl_receitas_planejadas.setText(f"Receitas Planejadas: R$ {float(total_receitas_planejadas):,.2f}")
            self.lbl_receitas_realizadas.setText(f"Receitas Realizadas: R$ {float(total_receitas_realizadas):,.2f}")
            self.lbl_despesas_planejadas.setText(f"Despesas Planejadas: R$ {float(total_despesas_planejadas):,.2f}")
            self.lbl_despesas_realizadas.setText(f"Despesas Realizadas: R$ {float(total_despesas_realizadas):,.2f}")
            self.lbl_saldo_planejado.setText(f"Saldo Planejado: R$ {float(saldo_planejado):,.2f}")
            self.lbl_saldo_realizado.setText(f"Saldo Realizado: R$ {float(saldo_realizado):,.2f}")
            self.lbl_percentual_execucao.setText(f"Execução Geral: {percentual_geral:.1f}%")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar painel de informações: {e}")

    def atualizar_alertas(self):
        """Atualiza o painel de alertas"""
        if not self.orcamento_id_atual:
            self.lista_alertas.clear()
            return
        
        try:
            self.lista_alertas.clear()
            
            # Obter alertas (percentual de alerta padrão: 90%)
            alertas = obter_alertas_orcamento(self.orcamento_id_atual, 90.0)
            
            if not alertas:
                item = QListWidgetItem("✓ Nenhum alerta no momento")
                item.setForeground(QColor(34, 139, 34))  # Verde
                self.lista_alertas.addItem(item)
                return
            
            for alerta in alertas:
                categoria_nome = alerta['categoria_nome']
                mes = alerta['mes']
                percentual = alerta['percentual_execucao']
                valor_restante = alerta['valor_restante']
                status = alerta['status']
                
                # Nomes dos meses
                meses = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                mes_nome = meses[mes] if 1 <= mes <= 12 else str(mes)
                
                # Criar texto do alerta
                texto = f"⚠ {categoria_nome} ({mes_nome}): {percentual:.1f}% executado"
                if valor_restante < 0:
                    texto += f" - Excedido em R$ {abs(float(valor_restante)):,.2f}"
                else:
                    texto += f" - Restam R$ {float(valor_restante):,.2f}"
                
                item = QListWidgetItem(texto)
                
                # Aplicar cor baseada no status
                if status == 'vermelho':
                    item.setForeground(QColor(220, 53, 69))
                elif status == 'amarelo':
                    item.setForeground(QColor(255, 193, 7))
                else:
                    item.setForeground(QColor(34, 139, 34))
                
                # Armazenar dados do alerta no item
                item.setData(Qt.ItemDataRole.UserRole, alerta)
                
                self.lista_alertas.addItem(item)
                
        except Exception as e:
            logger.error(f"Erro ao atualizar alertas: {e}")

    def on_alerta_clicado(self, item: QListWidgetItem):
        """Handler quando um alerta é clicado"""
        alerta = item.data(Qt.ItemDataRole.UserRole)
        if not alerta:
            return
        
        categoria_id = alerta['categoria_id']
        mes = alerta['mes']
        categoria_nome = alerta['categoria_nome']
        valor_planejado = alerta['valor_planejado']
        valor_realizado = alerta['valor_realizado']
        
        # Perguntar se deseja ajustar o valor
        meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        mes_nome = meses[mes] if 1 <= mes <= 12 else str(mes)
        
        msg = f"Categoria: {categoria_nome}\n"
        msg += f"Mês: {mes_nome}\n"
        msg += f"Planejado: R$ {float(valor_planejado):,.2f}\n"
        msg += f"Realizado: R$ {float(valor_realizado):,.2f}\n\n"
        msg += "Deseja ajustar o valor planejado?"
        
        resposta = QMessageBox.question(
            self, 
            "Ajustar Valor", 
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            # Abrir dialog para ajustar valor
            dialog = DialogAjustarValor(self, categoria_nome, mes_nome, valor_planejado)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                novo_valor = dialog.get_valor()
                try:
                    # Validar
                    ItemOrcamentoModel(
                        orcamento_id=self.orcamento_id_atual,
                        categoria_id=categoria_id,
                        mes=mes,
                        valor_planejado=novo_valor
                    )
                    
                    # Salvar
                    criar_item_orcamento(
                        self.orcamento_id_atual,
                        categoria_id,
                        mes,
                        float(novo_valor)
                    )
                    
                    QMessageBox.information(self, "Sucesso", "Valor ajustado com sucesso!")
                    
                    # Atualizar interface
                    self.atualizar_matriz()
                    self.atualizar_painel_informacoes()
                    self.atualizar_alertas()
                    self.dados_atualizados.emit()
                    
                except ValidationError as ve:
                    QMessageBox.warning(self, "Validação", f"Valor inválido: {ve}")
                except Exception as e:
                    logger.error(f"Erro ao ajustar valor: {e}")
                    QMessageBox.critical(self, "Erro", f"Erro ao ajustar valor: {str(e)}")

    def criar_novo_orcamento(self):
        """Abre dialog para criar novo orçamento"""
        dialog = DialogNovoOrcamento(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            ano = dialog.get_ano()
            try:
                # Validar usando Pydantic
                OrcamentoModel(ano=ano, status='ativo')
                
                # Criar orçamento
                orcamento_id = criar_orcamento(ano)
                
                QMessageBox.information(self, "Sucesso", f"Orçamento {ano} criado com sucesso!")
                
                # Recarregar lista
                self.carregar_lista_orcamentos()
                
                # Selecionar o novo orçamento
                for i in range(self.combo_orcamento.count()):
                    if self.combo_orcamento.itemData(i) == orcamento_id:
                        self.combo_orcamento.setCurrentIndex(i)
                        break
                
                self.dados_atualizados.emit()
                
            except ValidationError as ve:
                QMessageBox.warning(self, "Validação", f"Ano inválido: {ve}")
            except Exception as e:
                logger.error(f"Erro ao criar orçamento: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao criar orçamento: {str(e)}")

    def copiar_de_ano_anterior(self):
        """Abre dialog para copiar orçamento de ano anterior"""
        dialog = DialogCopiarOrcamento(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            ano_origem, ano_destino = dialog.get_anos()
            try:
                # Validar anos
                OrcamentoModel(ano=ano_origem, status='ativo')
                OrcamentoModel(ano=ano_destino, status='ativo')
                
                # Copiar orçamento
                orcamento_id = copiar_orcamento_ano_anterior(ano_origem, ano_destino)
                
                QMessageBox.information(self, "Sucesso", 
                    f"Orçamento {ano_destino} criado com base em {ano_origem}!")
                
                # Recarregar lista
                self.carregar_lista_orcamentos()
                
                # Selecionar o novo orçamento
                for i in range(self.combo_orcamento.count()):
                    if self.combo_orcamento.itemData(i) == orcamento_id:
                        self.combo_orcamento.setCurrentIndex(i)
                        break
                
                self.dados_atualizados.emit()
                
            except ValidationError as ve:
                QMessageBox.warning(self, "Validação", f"Ano inválido: {ve}")
            except Exception as e:
                logger.error(f"Erro ao copiar orçamento: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao copiar orçamento: {str(e)}")

    def mostrar_menu_contexto(self, pos):
        """Mostra menu de contexto ao clicar com botão direito na tabela"""
        item = self.tabela.itemAt(pos)
        if not item or item.column() == 0:  # Não mostrar menu na coluna de categorias
            return
        
        # Obter categoria da linha
        row = item.row()
        categoria_item = self.tabela.item(row, 0)
        if not categoria_item or categoria_item.text() == "---":
            return
        
        # Encontrar categoria_id
        categoria_id = None
        for cat in self.categorias_receitas + self.categorias_despesas:
            if cat['nome'] == categoria_item.text():
                categoria_id = cat['id']
                break
        
        if not categoria_id:
            return
        
        # Criar menu
        menu = QMenu(self)
        action_aplicar_padrao = QAction("Aplicar valor padrão para todos os meses", self)
        action_aplicar_padrao.triggered.connect(lambda: self.aplicar_valor_padrao(categoria_id))
        menu.addAction(action_aplicar_padrao)
        
        # Mostrar menu
        menu.exec(self.tabela.viewport().mapToGlobal(pos))

    def aplicar_valor_padrao(self, categoria_id: int):
        """Abre dialog para aplicar valor padrão a todos os meses de uma categoria"""
        # Bloquear se orçamento inativo
        if not self.orcamento_ativo:
            QMessageBox.warning(
                self,
                "Orçamento Inativo",
                "Este orçamento está arquivado e não pode ser editado.\n\n"
                "Para editar, reative o orçamento primeiro."
            )
            return
        
        dialog = DialogValorPadrao(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            valor = dialog.get_valor()
            try:
                # Validar valor
                ItemOrcamentoModel(
                    orcamento_id=self.orcamento_id_atual,
                    categoria_id=categoria_id,
                    mes=1,
                    valor_planejado=valor
                )
                
                # Aplicar valor padrão
                aplicar_valor_padrao_categoria(self.orcamento_id_atual, categoria_id, float(valor))
                
                QMessageBox.information(self, "Sucesso", 
                    f"Valor R$ {float(valor):.2f} aplicado a todos os 12 meses!")
                
                # Atualizar interface
                self.atualizar_matriz()
                self.atualizar_painel_informacoes()
                self.dados_atualizados.emit()
                
            except ValidationError as ve:
                QMessageBox.warning(self, "Validação", f"Valor inválido: {ve}")
            except Exception as e:
                logger.error(f"Erro ao aplicar valor padrão: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao aplicar valor padrão: {str(e)}")
    
    def desativar_orcamento(self):
        """Desativa ou reativa o orçamento atual"""
        if not self.orcamento_id_atual:
            return
        
        try:
            orcamento = obter_orcamento(self.orcamento_id_atual)
            if not orcamento:
                return
            
            ano = orcamento['ano']
            status_atual = orcamento['status']
            
            if status_atual == 'ativo':
                # Desativar
                msg = f"Deseja arquivar o orçamento de {ano}?\n\n"
                msg += "O orçamento será marcado como inativo e não poderá ser editado.\n"
                msg += "Todos os dados serão preservados e você poderá reativá-lo depois."
                
                resposta = QMessageBox.question(
                    self,
                    "Confirmar Desativação",
                    msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if resposta == QMessageBox.StandardButton.Yes:
                    atualizar_status_orcamento(self.orcamento_id_atual, 'inativo')
                    QMessageBox.information(self, "Sucesso", f"Orçamento {ano} arquivado com sucesso!")
                    logger.info(f"Orçamento {self.orcamento_id_atual} desativado")
                    
                    # Recarregar lista e interface
                    self.carregar_lista_orcamentos()
            else:
                # Reativar
                msg = f"Deseja reativar o orçamento de {ano}?\n\n"
                msg += "O orçamento será marcado como ativo e poderá ser editado novamente."
                
                resposta = QMessageBox.question(
                    self,
                    "Confirmar Reativação",
                    msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if resposta == QMessageBox.StandardButton.Yes:
                    atualizar_status_orcamento(self.orcamento_id_atual, 'ativo')
                    QMessageBox.information(self, "Sucesso", f"Orçamento {ano} reativado com sucesso!")
                    logger.info(f"Orçamento {self.orcamento_id_atual} reativado")
                    
                    # Recarregar lista e interface
                    self.carregar_lista_orcamentos()
        
        except Exception as e:
            logger.error(f"Erro ao alterar status do orçamento: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao alterar status: {str(e)}")


class DialogNovoOrcamento(QDialog):
    """Dialog para criar novo orçamento"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Orçamento")
        self.setModal(True)
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        
        # Campo de ano
        layout.addWidget(QLabel("Ano do Orçamento:"))
        self.input_ano = QLineEdit()
        self.input_ano.setPlaceholderText(f"Ex: {datetime.now().year}")
        layout.addWidget(self.input_ano)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_ano(self) -> int:
        """Retorna o ano digitado"""
        return int(self.input_ano.text())


class DialogCopiarOrcamento(QDialog):
    """Dialog para copiar orçamento de ano anterior"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Copiar Orçamento")
        self.setModal(True)
        self.resize(300, 200)
        
        layout = QVBoxLayout(self)
        
        # Ano origem
        layout.addWidget(QLabel("Ano de Origem:"))
        self.input_ano_origem = QLineEdit()
        self.input_ano_origem.setPlaceholderText(f"Ex: {datetime.now().year - 1}")
        layout.addWidget(self.input_ano_origem)
        
        # Ano destino
        layout.addWidget(QLabel("Ano de Destino:"))
        self.input_ano_destino = QLineEdit()
        self.input_ano_destino.setPlaceholderText(f"Ex: {datetime.now().year}")
        layout.addWidget(self.input_ano_destino)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_anos(self) -> tuple[int, int]:
        """Retorna os anos digitados (origem, destino)"""
        return int(self.input_ano_origem.text()), int(self.input_ano_destino.text())


class DialogValorPadrao(QDialog):
    """Dialog para aplicar valor padrão a todos os meses"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aplicar Valor Padrão")
        self.setModal(True)
        self.resize(400, 250)
        
        layout = QVBoxLayout(self)
        
        # Campo de valor
        layout.addWidget(QLabel("Valor a ser aplicado em todos os 12 meses:"))
        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Ex: 1500.00")
        layout.addWidget(self.input_valor)
        
        # Prévia
        layout.addWidget(QLabel("\nPrévia:"))
        preview_text = "Este valor será aplicado em:\n"
        preview_text += "Janeiro, Fevereiro, Março, Abril, Maio, Junho,\n"
        preview_text += "Julho, Agosto, Setembro, Outubro, Novembro, Dezembro"
        lbl_preview = QLabel(preview_text)
        lbl_preview.setStyleSheet("color: #a4b0be; font-style: italic;")
        layout.addWidget(lbl_preview)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_valor(self) -> Decimal:
        """Retorna o valor digitado"""
        return Decimal(self.input_valor.text())


class DialogAjustarValor(QDialog):
    """Dialog para ajustar valor de um item específico"""
    
    def __init__(self, parent=None, categoria_nome="", mes_nome="", valor_atual=0):
        super().__init__(parent)
        self.setWindowTitle("Ajustar Valor")
        self.setModal(True)
        self.resize(350, 200)
        
        layout = QVBoxLayout(self)
        
        # Informações
        info_text = f"Categoria: {categoria_nome}\nMês: {mes_nome}"
        lbl_info = QLabel(info_text)
        lbl_info.setStyleSheet("color: #a4b0be; margin-bottom: 10px;")
        layout.addWidget(lbl_info)
        
        # Valor atual
        layout.addWidget(QLabel(f"Valor Atual: R$ {float(valor_atual):,.2f}"))
        
        # Novo valor
        layout.addWidget(QLabel("\nNovo Valor:"))
        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Ex: 2500.00")
        self.input_valor.setText(f"{float(valor_atual):.2f}")
        layout.addWidget(self.input_valor)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_valor(self) -> Decimal:
        """Retorna o valor digitado"""
        return Decimal(self.input_valor.text())
