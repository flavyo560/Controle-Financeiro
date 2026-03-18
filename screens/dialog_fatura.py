from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QComboBox, QLabel, QMessageBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from database import conectar, obter_fatura
from datetime import datetime


class DialogFatura(QDialog):
    """Dialog para visualização e gestão de faturas do cartão."""
    
    dados_atualizados = pyqtSignal()

    def __init__(self, parent=None, cartao_id=None, mes_fatura=None):
        super().__init__(parent)
        self.cartao_id_inicial = cartao_id
        self.mes_fatura_inicial = mes_fatura
        
        self.setWindowTitle("Visualizar Fatura")
        self.setModal(True)
        self.resize(900, 700)
        
        # Aplicar estilo dark mode consistente com o projeto
        self.setStyleSheet("""
            QDialog { 
                background-color: #0b0b0b; 
                color: white; 
            }
            QLabel { 
                color: #a4b0be; 
                font-weight: bold; 
            }
            QComboBox {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QComboBox:focus {
                border: 1px solid #ff0055;
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
            QPushButton:disabled {
                background-color: #0f0f0f;
                color: #555555;
                border: 1px solid #222222;
            }
            QPushButton#btn_pagar {
                background-color: #ff0055;
                color: white;
            }
            QPushButton#btn_pagar:hover {
                background-color: #e6004d;
            }
            QPushButton#btn_pagar:disabled {
                background-color: #4d0019;
                color: #999999;
            }
            QTableWidget {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                color: #ffffff;
                gridline-color: #333333;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #ff0055;
                color: white;
            }
            QHeaderView::section {
                background-color: #0f0f0f;
                color: #a4b0be;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #ff0055;
                font-weight: bold;
            }
        """)
        
        self._setup_ui()
        self._carregar_dados()
        
        # Selecionar cartão e mês inicial antes de conectar sinais
        if self.cartao_id_inicial and self.mes_fatura_inicial:
            self._selecionar_cartao_inicial()
            self._selecionar_mes_inicial()
        
        # Conectar sinais após selecionar valores iniciais
        self._conectar_sinais()
        
        # Carregar fatura inicial se fornecida (passar parâmetros diretamente)
        if self.cartao_id_inicial and self.mes_fatura_inicial:
            self.carregar_fatura(self.cartao_id_inicial, self.mes_fatura_inicial)

    def _setup_ui(self):
        """Configura a interface do dialog."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        titulo = QLabel("VISUALIZAR FATURA")
        titulo.setStyleSheet("font-size:16px; font-weight:bold; color: #ff0055; margin-bottom: 10px;")
        layout.addWidget(titulo)
        
        # Seção Superior - Seletores
        selecao_layout = QHBoxLayout()
        selecao_layout.setSpacing(15)
        
        # Seletor de Cartão
        label_cartao = QLabel("Cartão:")
        self.combo_cartao = QComboBox()
        self.combo_cartao.setMinimumWidth(250)
        
        # Seletor de Mês/Ano
        label_mes = QLabel("Mês/Ano:")
        self.combo_mes = QComboBox()
        self.combo_mes.setMinimumWidth(150)
        
        # Botão Atualizar
        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.setMaximumWidth(120)
        
        selecao_layout.addWidget(label_cartao)
        selecao_layout.addWidget(self.combo_cartao)
        selecao_layout.addWidget(label_mes)
        selecao_layout.addWidget(self.combo_mes)
        selecao_layout.addWidget(self.btn_atualizar)
        selecao_layout.addStretch()
        
        layout.addLayout(selecao_layout)
        
        # Seção Central - Tabela de Compras
        label_compras = QLabel("Compras da Fatura:")
        label_compras.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff; margin-top: 10px;")
        layout.addWidget(label_compras)
        
        self.tabela_compras = QTableWidget()
        self.tabela_compras.setColumnCount(5)
        self.tabela_compras.setHorizontalHeaderLabels([
            "Data", "Descrição", "Categoria", "Valor", "Parcela"
        ])
        
        # Configurar largura das colunas
        header = self.tabela_compras.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tabela_compras.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_compras.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_compras.setAlternatingRowColors(True)
        
        layout.addWidget(self.tabela_compras)
        
        # Seção de Resumo
        resumo_container = QWidget()
        resumo_container.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        resumo_layout = QVBoxLayout(resumo_container)
        resumo_layout.setSpacing(8)
        
        # Labels de resumo
        self.label_valor_total = QLabel("Valor Total: R$ 0,00")
        self.label_valor_total.setStyleSheet("font-size: 14px; color: #ffffff;")
        
        self.label_valor_pago = QLabel("Valor Pago: R$ 0,00")
        self.label_valor_pago.setStyleSheet("font-size: 14px; color: #00d4ff;")
        
        self.label_saldo_devedor = QLabel("Saldo Devedor: R$ 0,00")
        self.label_saldo_devedor.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff0055;")
        
        self.label_data_vencimento = QLabel("Data Vencimento: -")
        self.label_data_vencimento.setStyleSheet("font-size: 14px; color: #ffffff;")
        
        self.label_status = QLabel("Status: -")
        self.label_status.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        resumo_layout.addWidget(self.label_valor_total)
        resumo_layout.addWidget(self.label_valor_pago)
        resumo_layout.addWidget(self.label_saldo_devedor)
        resumo_layout.addWidget(self.label_data_vencimento)
        resumo_layout.addWidget(self.label_status)
        
        layout.addWidget(resumo_container)
        
        # Seção Inferior - Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        
        self.btn_pagar = QPushButton("Registrar Pagamento")
        self.btn_pagar.setObjectName("btn_pagar")
        self.btn_pagar.setEnabled(False)
        
        self.btn_historico = QPushButton("Ver Histórico de Pagamentos")
        
        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.clicked.connect(self.close)
        
        botoes_layout.addWidget(self.btn_pagar)
        botoes_layout.addWidget(self.btn_historico)
        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_fechar)
        
        layout.addLayout(botoes_layout)

    def _carregar_dados(self):
        """Carrega cartões e meses disponíveis."""
        self._carregar_cartoes()
        self._carregar_meses()

    def _carregar_cartoes(self):
        """Carrega cartões ativos."""
        self.combo_cartao.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, nome, bandeira 
                FROM cartoes 
                WHERE status = 1 
                ORDER BY nome
            """)
            for cartao_id, nome, bandeira in cur.fetchall():
                texto = f"{nome} ({bandeira})" if bandeira else nome
                self.combo_cartao.addItem(texto, cartao_id)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar cartões: {e}")

    def _carregar_meses(self):
        """Carrega lista de meses (últimos 12 meses + próximos 3 meses)."""
        self.combo_mes.clear()
        
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        # Gerar lista de meses (12 meses atrás até 3 meses à frente)
        hoje = date.today()
        
        for i in range(-12, 4):
            mes_data = hoje + relativedelta(months=i)
            mes_str = mes_data.strftime('%Y-%m')
            mes_formatado = mes_data.strftime('%m/%Y')
            self.combo_mes.addItem(mes_formatado, mes_str)
        
        # Selecionar mês atual por padrão
        mes_atual = hoje.strftime('%Y-%m')
        index = self.combo_mes.findData(mes_atual)
        if index >= 0:
            self.combo_mes.setCurrentIndex(index)

    def _conectar_sinais(self):
        """Conecta sinais para atualização."""
        self.btn_atualizar.clicked.connect(self.carregar_fatura)
        self.combo_cartao.currentIndexChanged.connect(self.carregar_fatura)
        self.combo_mes.currentIndexChanged.connect(self.carregar_fatura)
        self.btn_pagar.clicked.connect(self._abrir_dialog_pagamento)
        self.btn_historico.clicked.connect(self._abrir_historico_pagamentos)

    def _selecionar_cartao_inicial(self):
        """Seleciona o cartão inicial se fornecido."""
        if self.cartao_id_inicial:
            index = self.combo_cartao.findData(self.cartao_id_inicial)
            if index >= 0:
                # Desconectar temporariamente o sinal para evitar chamadas duplicadas
                self.combo_cartao.blockSignals(True)
                self.combo_cartao.setCurrentIndex(index)
                self.combo_cartao.blockSignals(False)
            else:
                # Cartão não encontrado no combo, pode ter sido desativado
                print(f"Aviso: Cartão ID {self.cartao_id_inicial} não encontrado no combo")

    def _selecionar_mes_inicial(self):
        """Seleciona o mês inicial se fornecido."""
        if self.mes_fatura_inicial:
            index = self.combo_mes.findData(self.mes_fatura_inicial)
            if index >= 0:
                # Desconectar temporariamente o sinal para evitar chamadas duplicadas
                self.combo_mes.blockSignals(True)
                self.combo_mes.setCurrentIndex(index)
                self.combo_mes.blockSignals(False)

    def carregar_fatura(self, cartao_id=None, mes_fatura=None):
        """Carrega e exibe os dados da fatura selecionada."""
        # Usar parâmetros fornecidos ou valores dos combos
        if cartao_id is None:
            cartao_id = self.combo_cartao.currentData()
        if mes_fatura is None:
            mes_fatura = self.combo_mes.currentData()
        
        if not cartao_id or not mes_fatura:
            self._limpar_fatura()
            return
        
        try:
            # Obter dados da fatura
            fatura = obter_fatura(cartao_id, mes_fatura)
            
            # Preencher tabela de compras
            self._preencher_tabela_compras(fatura['compras'])
            
            # Atualizar labels de resumo
            self._atualizar_resumo(fatura)
            
            # Habilitar/desabilitar botão de pagamento
            self.btn_pagar.setEnabled(fatura['saldo_devedor'] > 0)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar fatura: {str(e)}")
            self._limpar_fatura()

    def _preencher_tabela_compras(self, compras):
        """Preenche a tabela com as compras da fatura."""
        self.tabela_compras.setRowCount(0)
        
        for compra in compras:
            row = self.tabela_compras.rowCount()
            self.tabela_compras.insertRow(row)
            
            # Data
            data_formatada = datetime.strptime(compra['data_compra'], '%Y-%m-%d').strftime('%d/%m/%Y')
            item_data = QTableWidgetItem(data_formatada)
            item_data.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_compras.setItem(row, 0, item_data)
            
            # Descrição
            item_descricao = QTableWidgetItem(compra['descricao'])
            self.tabela_compras.setItem(row, 1, item_descricao)
            
            # Categoria
            categoria = compra.get('categoria_nome', '-')
            item_categoria = QTableWidgetItem(categoria if categoria else '-')
            item_categoria.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_compras.setItem(row, 2, item_categoria)
            
            # Valor
            item_valor = QTableWidgetItem(f"R$ {compra['valor']:.2f}")
            item_valor.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabela_compras.setItem(row, 3, item_valor)
            
            # Parcela
            parcela_info = compra.get('parcela_info', '-')
            item_parcela = QTableWidgetItem(parcela_info if parcela_info else '-')
            item_parcela.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_compras.setItem(row, 4, item_parcela)

    def _atualizar_resumo(self, fatura):
        """Atualiza os labels de resumo da fatura."""
        # Valor Total
        self.label_valor_total.setText(f"Valor Total: R$ {fatura['valor_total']:.2f}")
        
        # Valor Pago
        self.label_valor_pago.setText(f"Valor Pago: R$ {fatura['valor_pago']:.2f}")
        
        # Saldo Devedor
        self.label_saldo_devedor.setText(f"Saldo Devedor: R$ {fatura['saldo_devedor']:.2f}")
        
        # Data Vencimento
        data_venc_formatada = datetime.strptime(fatura['data_vencimento'], '%Y-%m-%d').strftime('%d/%m/%Y')
        self.label_data_vencimento.setText(f"Data Vencimento: {data_venc_formatada}")
        
        # Status com badge colorido
        status = fatura['status']
        status_texto, status_cor = self._obter_status_formatado(status)
        self.label_status.setText(f"Status: {status_texto}")
        self.label_status.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: bold; 
            color: {status_cor};
            background-color: {status_cor}22;
            padding: 8px;
            border-radius: 6px;
            border: 1px solid {status_cor};
        """)

    def _obter_status_formatado(self, status):
        """Retorna o texto e cor do status."""
        status_map = {
            'pendente': ('Pendente', '#ffcc00'),
            'paga_parcial': ('Paga Parcialmente', '#ff9900'),
            'paga_total': ('Paga Totalmente', '#00ff88'),
            'vencida': ('Vencida', '#ff0055')
        }
        return status_map.get(status, ('Desconhecido', '#ffffff'))

    def _limpar_fatura(self):
        """Limpa os dados da fatura."""
        self.tabela_compras.setRowCount(0)
        self.label_valor_total.setText("Valor Total: R$ 0,00")
        self.label_valor_pago.setText("Valor Pago: R$ 0,00")
        self.label_saldo_devedor.setText("Saldo Devedor: R$ 0,00")
        self.label_data_vencimento.setText("Data Vencimento: -")
        self.label_status.setText("Status: -")
        self.label_status.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.btn_pagar.setEnabled(False)

    def _abrir_dialog_pagamento(self):
        """Abre o diálogo de pagamento de fatura."""
        cartao_id = self.combo_cartao.currentData()
        mes_fatura = self.combo_mes.currentData()
        
        if not cartao_id or not mes_fatura:
            QMessageBox.warning(self, "Aviso", "Selecione um cartão e mês para registrar pagamento.")
            return
        
        from screens.dialog_pagamento_fatura import DialogPagamentoFatura
        dialog = DialogPagamentoFatura(self, cartao_id, mes_fatura)
        dialog.dados_atualizados.connect(self.carregar_fatura)
        dialog.dados_atualizados.connect(self.dados_atualizados.emit)
        dialog.exec()

    def _abrir_historico_pagamentos(self):
        """Abre o diálogo de histórico de pagamentos."""
        cartao_id = self.combo_cartao.currentData()
        mes_fatura = self.combo_mes.currentData()
        
        if not cartao_id or not mes_fatura:
            QMessageBox.warning(self, "Aviso", "Selecione um cartão e mês para ver o histórico.")
            return
        
        try:
            # Buscar pagamentos da fatura
            from database import listar_pagamentos_fatura
            pagamentos = listar_pagamentos_fatura(cartao_id, mes_fatura)
            
            if not pagamentos:
                QMessageBox.information(
                    self, 
                    "Histórico de Pagamentos", 
                    "Nenhum pagamento registrado para esta fatura."
                )
                return
            
            # Montar mensagem com histórico
            mensagem = "Histórico de Pagamentos:\n\n"
            for pag in pagamentos:
                data_formatada = datetime.strptime(pag['data_pagamento'], '%Y-%m-%d').strftime('%d/%m/%Y')
                mensagem += f"• {data_formatada} - R$ {pag['valor_pago']:.2f} - {pag['banco_nome']}\n"
            
            QMessageBox.information(self, "Histórico de Pagamentos", mensagem)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar histórico: {str(e)}")
