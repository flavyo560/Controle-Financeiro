from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QDateEdit, QComboBox, 
    QLabel, QMessageBox, QWidget
)
from PyQt6.QtCore import QDate, pyqtSignal
from database import (
    conectar, registrar_pagamento_fatura, obter_fatura
)
from datetime import datetime


class DialogPagamentoFatura(QDialog):
    """Dialog para registro de pagamento de fatura do cartão."""
    
    dados_atualizados = pyqtSignal()

    def __init__(self, parent=None, cartao_id=None, mes_fatura=None):
        super().__init__(parent)
        self.cartao_id = cartao_id
        self.mes_fatura = mes_fatura
        self.fatura_info = None
        
        self.setWindowTitle("Registrar Pagamento de Fatura")
        self.setModal(True)
        self.resize(550, 450)
        
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
            QLineEdit, QComboBox, QDateEdit {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
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
            QPushButton#btn_salvar {
                background-color: #ff0055;
                color: white;
            }
            QPushButton#btn_salvar:hover {
                background-color: #e6004d;
            }
            QPushButton#btn_rapido {
                background-color: #00d4ff;
                color: #0b0b0b;
                font-size: 12px;
                padding: 6px 12px;
            }
            QPushButton#btn_rapido:hover {
                background-color: #00b8e6;
            }
        """)
        
        self._setup_ui()
        self._carregar_dados()
        self._conectar_sinais()

    def _setup_ui(self):
        """Configura a interface do dialog."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        titulo = QLabel("REGISTRAR PAGAMENTO DE FATURA")
        titulo.setStyleSheet("font-size:16px; font-weight:bold; color: #ff0055; margin-bottom: 10px;")
        layout.addWidget(titulo)
        
        # Container de informações da fatura
        info_container = QWidget()
        info_container.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        info_layout = QVBoxLayout(info_container)
        info_layout.setSpacing(8)
        
        # Labels informativos (somente leitura)
        self.label_cartao = QLabel("Cartão: -")
        self.label_cartao.setStyleSheet("font-size: 14px; color: #ffffff;")
        
        self.label_mes_fatura = QLabel("Mês da Fatura: -")
        self.label_mes_fatura.setStyleSheet("font-size: 14px; color: #ffffff;")
        
        self.label_saldo_devedor = QLabel("Saldo Devedor: R$ 0,00")
        self.label_saldo_devedor.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff0055;")
        
        info_layout.addWidget(self.label_cartao)
        info_layout.addWidget(self.label_mes_fatura)
        info_layout.addWidget(self.label_saldo_devedor)
        
        layout.addWidget(info_container)
        
        # Formulário de pagamento
        form = QFormLayout()
        form.setSpacing(10)
        
        # Campo Valor do Pagamento com botões rápidos
        valor_layout = QHBoxLayout()
        valor_layout.setSpacing(10)
        
        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Ex: 500.00")
        valor_layout.addWidget(self.input_valor, stretch=1)
        
        self.btn_pagar_total = QPushButton("Pagar Total")
        self.btn_pagar_total.setObjectName("btn_rapido")
        self.btn_pagar_total.setMaximumWidth(100)
        valor_layout.addWidget(self.btn_pagar_total)
        
        self.btn_pagar_minimo = QPushButton("Pagar Mínimo")
        self.btn_pagar_minimo.setObjectName("btn_rapido")
        self.btn_pagar_minimo.setMaximumWidth(110)
        valor_layout.addWidget(self.btn_pagar_minimo)
        
        form.addRow("Valor do Pagamento:", valor_layout)
        
        # Campo Data do Pagamento
        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        form.addRow("Data do Pagamento:", self.input_data)
        
        # Campo Banco de Origem
        self.combo_banco = QComboBox()
        self.combo_banco.setPlaceholderText("Selecione o banco")
        form.addRow("Banco de Origem:", self.combo_banco)
        
        layout.addLayout(form)
        
        # Label de aviso de saldo insuficiente
        self.label_aviso_saldo = QLabel("⚠️ Saldo do banco insuficiente para este pagamento")
        self.label_aviso_saldo.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #ff9900; 
            padding: 8px; 
            background-color: #2a1a00; 
            border-radius: 6px;
            border: 1px solid #ff9900;
        """)
        self.label_aviso_saldo.setVisible(False)
        layout.addWidget(self.label_aviso_saldo)
        
        # Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.btn_salvar = QPushButton("Confirmar Pagamento")
        self.btn_salvar.setObjectName("btn_salvar")
        self.btn_salvar.clicked.connect(self.salvar)
        
        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_cancelar)
        botoes_layout.addWidget(self.btn_salvar)
        
        layout.addLayout(botoes_layout)

    def _carregar_dados(self):
        """Carrega informações da fatura e bancos disponíveis."""
        if not self.cartao_id or not self.mes_fatura:
            QMessageBox.warning(self, "Erro", "Cartão ou mês da fatura não especificado.")
            self.reject()
            return
        
        self._carregar_info_fatura()
        self._carregar_bancos()

    def _carregar_info_fatura(self):
        """Carrega informações da fatura."""
        try:
            # Obter informações da fatura
            self.fatura_info = obter_fatura(self.cartao_id, self.mes_fatura)
            
            # Buscar nome do cartão
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT nome, bandeira FROM cartoes WHERE id = ?", (self.cartao_id,))
            resultado = cur.fetchone()
            conn.close()
            
            if resultado:
                nome_cartao, bandeira = resultado
                texto_cartao = f"{nome_cartao} ({bandeira})" if bandeira else nome_cartao
                self.label_cartao.setText(f"Cartão: {texto_cartao}")
            
            # Formatar mês da fatura
            mes_fatura_dt = datetime.strptime(self.mes_fatura, '%Y-%m')
            mes_fatura_formatado = mes_fatura_dt.strftime('%m/%Y')
            self.label_mes_fatura.setText(f"Mês da Fatura: {mes_fatura_formatado}")
            
            # Exibir saldo devedor
            saldo_devedor = self.fatura_info['saldo_devedor']
            self.label_saldo_devedor.setText(f"Saldo Devedor: R$ {saldo_devedor:.2f}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar informações da fatura: {str(e)}")
            self.reject()

    def _carregar_bancos(self):
        """Carrega bancos ativos."""
        self.combo_banco.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, nome, saldo_inicial 
                FROM bancos 
                ORDER BY nome
            """)
            for banco_id, nome, saldo in cur.fetchall():
                texto = f"{nome} (Saldo: R$ {saldo:.2f})"
                self.combo_banco.addItem(texto, banco_id)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar bancos: {e}")

    def _conectar_sinais(self):
        """Conecta sinais para atualização em tempo real."""
        self.btn_pagar_total.clicked.connect(self._preencher_valor_total)
        self.btn_pagar_minimo.clicked.connect(self._preencher_valor_minimo)
        self.input_valor.textChanged.connect(self._verificar_saldo_banco)
        self.combo_banco.currentIndexChanged.connect(self._verificar_saldo_banco)

    def _preencher_valor_total(self):
        """Preenche o campo de valor com o saldo devedor total."""
        if self.fatura_info:
            saldo_devedor = self.fatura_info['saldo_devedor']
            self.input_valor.setText(f"{saldo_devedor:.2f}")

    def _preencher_valor_minimo(self):
        """Preenche o campo de valor com 10% do saldo devedor (pagamento mínimo)."""
        if self.fatura_info:
            saldo_devedor = self.fatura_info['saldo_devedor']
            valor_minimo = saldo_devedor * 0.10
            self.input_valor.setText(f"{valor_minimo:.2f}")

    def _verificar_saldo_banco(self):
        """Verifica se o banco tem saldo suficiente para o pagamento."""
        banco_id = self.combo_banco.currentData()
        if not banco_id:
            self.label_aviso_saldo.setVisible(False)
            return
        
        try:
            valor_txt = self.input_valor.text().replace(",", ".")
            if not valor_txt:
                self.label_aviso_saldo.setVisible(False)
                return
            
            valor = float(valor_txt)
            
            # Buscar saldo do banco
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT saldo_inicial FROM bancos WHERE id = ?", (banco_id,))
            resultado = cur.fetchone()
            conn.close()
            
            if resultado:
                saldo_banco = resultado[0]
                
                # Exibir aviso se saldo insuficiente
                if valor > saldo_banco:
                    self.label_aviso_saldo.setText(
                        f"⚠️ Saldo do banco insuficiente (R$ {saldo_banco:.2f})"
                    )
                    self.label_aviso_saldo.setVisible(True)
                else:
                    self.label_aviso_saldo.setVisible(False)
            else:
                self.label_aviso_saldo.setVisible(False)
                
        except (ValueError, TypeError):
            self.label_aviso_saldo.setVisible(False)
        except Exception as e:
            print(f"Erro ao verificar saldo do banco: {e}")
            self.label_aviso_saldo.setVisible(False)

    def salvar(self):
        """Valida e registra o pagamento da fatura."""
        # Validar campos obrigatórios
        valor_txt = self.input_valor.text().replace(",", ".")
        data_pagamento = self.input_data.date().toString("yyyy-MM-dd")
        banco_id = self.combo_banco.currentData()
        
        # Validações
        if not valor_txt:
            QMessageBox.warning(self, "Erro", "Por favor, informe o valor do pagamento.")
            return
        
        try:
            valor = float(valor_txt)
            if valor <= 0:
                QMessageBox.warning(self, "Erro", "O valor do pagamento deve ser maior que zero.")
                return
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valor inválido. Use apenas números.")
            return
        
        if banco_id is None:
            QMessageBox.warning(self, "Erro", "Por favor, selecione o banco de origem.")
            return
        
        # Validar que valor não excede saldo devedor
        if self.fatura_info:
            saldo_devedor = self.fatura_info['saldo_devedor']
            if valor > saldo_devedor:
                QMessageBox.warning(
                    self,
                    "Erro",
                    f"O valor do pagamento (R$ {valor:.2f}) não pode exceder "
                    f"o saldo devedor (R$ {saldo_devedor:.2f})."
                )
                return
        
        # Verificar saldo do banco e avisar (mas permitir continuar)
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT saldo_inicial, nome FROM bancos WHERE id = ?", (banco_id,))
            resultado = cur.fetchone()
            conn.close()
            
            if resultado:
                saldo_banco, nome_banco = resultado
                if valor > saldo_banco:
                    resposta = QMessageBox.question(
                        self,
                        "Saldo Insuficiente",
                        f"O banco '{nome_banco}' possui saldo de R$ {saldo_banco:.2f}, "
                        f"insuficiente para o pagamento de R$ {valor:.2f}.\n\n"
                        "Deseja continuar mesmo assim?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if resposta == QMessageBox.StandardButton.No:
                        return
        except Exception as e:
            print(f"Erro ao verificar saldo do banco: {e}")
        
        # Registrar pagamento
        try:
            pagamento_id = registrar_pagamento_fatura(
                cartao_id=self.cartao_id,
                mes_fatura=self.mes_fatura,
                valor_pago=valor,
                data_pagamento=data_pagamento,
                banco_id=banco_id
            )
            
            # Calcular novo saldo devedor
            novo_saldo_devedor = saldo_devedor - valor
            
            QMessageBox.information(
                self,
                "Sucesso",
                f"Pagamento registrado com sucesso!\n\n"
                f"Valor pago: R$ {valor:.2f}\n"
                f"Novo saldo devedor: R$ {novo_saldo_devedor:.2f}"
            )
            
            # Emitir sinal de atualização
            self.dados_atualizados.emit()
            
            # Fechar dialog
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao registrar pagamento: {str(e)}")
