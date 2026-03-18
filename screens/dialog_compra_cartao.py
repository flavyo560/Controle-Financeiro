from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QDateEdit, QComboBox, 
    QLabel, QMessageBox, QRadioButton, QButtonGroup,
    QSpinBox, QWidget
)
from PyQt6.QtCore import QDate, pyqtSignal
from database import (
    conectar, criar_compra_cartao, criar_compra_parcelada_cartao,
    calcular_mes_fatura, obter_info_limite
)
from datetime import datetime
from models.validators import CompraCartaoModel
from pydantic import ValidationError
from decimal import Decimal


class DialogCompraCartao(QDialog):
    """Dialog para registro de compras no cartão de crédito."""
    
    dados_atualizados = pyqtSignal()

    def __init__(self, parent=None, cartao_id=None):
        super().__init__(parent)
        self.setWindowTitle("Nova Compra no Cartão")
        self.setModal(True)
        self.resize(550, 500)
        
        # Armazenar cartao_id para pré-seleção
        self.cartao_id_preselecionar = cartao_id
        
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
            QLineEdit, QComboBox, QDateEdit, QSpinBox {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
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
            QRadioButton {
                color: #a4b0be;
                font-weight: bold;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #333333;
                border-radius: 9px;
                background-color: #1a1a1a;
            }
            QRadioButton::indicator:checked {
                background-color: #ff0055;
                border: 2px solid #ff0055;
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
        titulo = QLabel("REGISTRAR COMPRA NO CARTÃO")
        titulo.setStyleSheet("font-size:16px; font-weight:bold; color: #ff0055; margin-bottom: 10px;")
        layout.addWidget(titulo)
        
        # Radio buttons para tipo de compra
        tipo_layout = QHBoxLayout()
        tipo_layout.setSpacing(20)
        
        self.radio_vista = QRadioButton("À Vista")
        self.radio_parcelada = QRadioButton("Parcelada")
        self.radio_vista.setChecked(True)
        
        self.grupo_tipo = QButtonGroup()
        self.grupo_tipo.addButton(self.radio_vista)
        self.grupo_tipo.addButton(self.radio_parcelada)
        
        tipo_layout.addWidget(self.radio_vista)
        tipo_layout.addWidget(self.radio_parcelada)
        tipo_layout.addStretch()
        
        layout.addLayout(tipo_layout)
        
        # Formulário
        form = QFormLayout()
        form.setSpacing(10)
        
        # Campo Cartão
        self.combo_cartao = QComboBox()
        self.combo_cartao.setPlaceholderText("Selecione o cartão")
        form.addRow("Cartão:", self.combo_cartao)
        
        # Campo Descrição
        self.input_descricao = QLineEdit()
        self.input_descricao.setPlaceholderText("Ex: Compra no supermercado")
        form.addRow("Descrição:", self.input_descricao)
        
        # Campo Valor
        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Ex: 150.00")
        form.addRow("Valor:", self.input_valor)
        
        # Campo Data da Compra
        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        form.addRow("Data da Compra:", self.input_data)
        
        # Campo Categoria
        self.combo_categoria = QComboBox()
        self.combo_categoria.setPlaceholderText("Selecione a categoria")
        form.addRow("Categoria:", self.combo_categoria)
        
        layout.addLayout(form)
        
        # Container para campos específicos de parcelada
        self.container_parcelada = QWidget()
        form_parcelada = QFormLayout(self.container_parcelada)
        form_parcelada.setContentsMargins(0, 0, 0, 0)
        form_parcelada.setSpacing(10)
        
        # Campo Número de Parcelas
        self.input_parcelas = QSpinBox()
        self.input_parcelas.setMinimum(2)
        self.input_parcelas.setMaximum(120)
        self.input_parcelas.setValue(12)
        form_parcelada.addRow("Número de Parcelas:", self.input_parcelas)
        
        self.container_parcelada.setVisible(False)
        layout.addWidget(self.container_parcelada)
        
        # Labels informativos
        self.label_fatura = QLabel("Fatura: -")
        self.label_fatura.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #00d4ff; 
            padding: 8px; 
            background-color: #1a1a1a; 
            border-radius: 6px;
            border: 1px solid #333333;
        """)
        layout.addWidget(self.label_fatura)
        
        self.label_parcela = QLabel("Valor de cada parcela: R$ 0,00")
        self.label_parcela.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #00d4ff; 
            padding: 8px; 
            background-color: #1a1a1a; 
            border-radius: 6px;
            border: 1px solid #333333;
        """)
        self.label_parcela.setVisible(False)
        layout.addWidget(self.label_parcela)
        
        # Label de aviso de limite
        self.label_aviso_limite = QLabel("⚠️ Compra excede limite disponível")
        self.label_aviso_limite.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #ff9900; 
            padding: 8px; 
            background-color: #2a1a00; 
            border-radius: 6px;
            border: 1px solid #ff9900;
        """)
        self.label_aviso_limite.setVisible(False)
        layout.addWidget(self.label_aviso_limite)
        
        # Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.btn_salvar = QPushButton("Registrar Compra")
        self.btn_salvar.setObjectName("btn_salvar")
        self.btn_salvar.clicked.connect(self.salvar)
        
        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_cancelar)
        botoes_layout.addWidget(self.btn_salvar)
        
        layout.addLayout(botoes_layout)

    def _carregar_dados(self):
        """Carrega cartões e categorias do banco de dados."""
        self._carregar_cartoes()
        self._carregar_categorias()
        
        # Pré-selecionar cartão se cartao_id foi fornecido
        if hasattr(self, 'cartao_id_preselecionar') and self.cartao_id_preselecionar:
            for i in range(self.combo_cartao.count()):
                if self.combo_cartao.itemData(i) == self.cartao_id_preselecionar:
                    self.combo_cartao.setCurrentIndex(i)
                    break

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

    def _carregar_categorias(self):
        """Carrega categorias de despesa."""
        self.combo_categoria.clear()
        self.combo_categoria.addItem("(Sem categoria)", None)
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM categorias WHERE tipo = 'despesa' ORDER BY nome")
            for cat_id, nome in cur.fetchall():
                self.combo_categoria.addItem(nome, cat_id)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")

    def _conectar_sinais(self):
        """Conecta sinais para atualização em tempo real."""
        # Alternar entre à vista e parcelada
        self.radio_vista.toggled.connect(self._alternar_tipo_compra)
        self.radio_parcelada.toggled.connect(self._alternar_tipo_compra)
        
        # Atualizar cálculos em tempo real
        self.combo_cartao.currentIndexChanged.connect(self._atualizar_calculos)
        self.input_data.dateChanged.connect(self._atualizar_calculos)
        self.input_valor.textChanged.connect(self._atualizar_calculos)
        self.input_parcelas.valueChanged.connect(self._atualizar_calculos)

    def _alternar_tipo_compra(self):
        """Alterna entre modo à vista e parcelada."""
        parcelada = self.radio_parcelada.isChecked()
        self.container_parcelada.setVisible(parcelada)
        self.label_parcela.setVisible(parcelada)
        self._atualizar_calculos()

    def _atualizar_calculos(self):
        """Atualiza os cálculos em tempo real (mês da fatura, valor da parcela, limite)."""
        # Calcular e exibir mês da fatura
        self._calcular_mes_fatura()
        
        # Calcular e exibir valor da parcela (se parcelada)
        if self.radio_parcelada.isChecked():
            self._calcular_valor_parcela()
        
        # Verificar limite disponível
        self._verificar_limite()

    def _calcular_mes_fatura(self):
        """Calcula e exibe o mês da fatura."""
        cartao_id = self.combo_cartao.currentData()
        if not cartao_id:
            self.label_fatura.setText("Fatura: -")
            return
        
        try:
            # Buscar dia de fechamento do cartão
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT dia_fechamento FROM cartoes WHERE id = ?", (cartao_id,))
            resultado = cur.fetchone()
            conn.close()
            
            if not resultado:
                self.label_fatura.setText("Fatura: -")
                return
            
            dia_fechamento = resultado[0]
            data_compra = self.input_data.date().toString("yyyy-MM-dd")
            
            # Calcular mês da fatura
            mes_fatura = calcular_mes_fatura(data_compra, dia_fechamento)
            
            # Formatar para exibição (MM/YYYY)
            mes_fatura_dt = datetime.strptime(mes_fatura, '%Y-%m')
            mes_fatura_formatado = mes_fatura_dt.strftime('%m/%Y')
            
            if self.radio_parcelada.isChecked():
                self.label_fatura.setText(f"Primeira parcela na fatura: {mes_fatura_formatado}")
            else:
                self.label_fatura.setText(f"Fatura: {mes_fatura_formatado}")
                
        except Exception as e:
            print(f"Erro ao calcular mês da fatura: {e}")
            self.label_fatura.setText("Fatura: -")

    def _calcular_valor_parcela(self):
        """Calcula e exibe o valor de cada parcela."""
        try:
            valor_txt = self.input_valor.text().replace(",", ".")
            if not valor_txt:
                self.label_parcela.setText("Valor de cada parcela: R$ 0,00")
                return
            
            valor_total = float(valor_txt)
            numero_parcelas = self.input_parcelas.value()
            
            if numero_parcelas > 0:
                valor_parcela = valor_total / numero_parcelas
                self.label_parcela.setText(f"Valor de cada parcela: R$ {valor_parcela:.2f}")
            else:
                self.label_parcela.setText("Valor de cada parcela: R$ 0,00")
                
        except ValueError:
            self.label_parcela.setText("Valor de cada parcela: R$ 0,00")

    def _verificar_limite(self):
        """Verifica se a compra excede o limite disponível."""
        cartao_id = self.combo_cartao.currentData()
        if not cartao_id:
            self.label_aviso_limite.setVisible(False)
            return
        
        try:
            valor_txt = self.input_valor.text().replace(",", ".")
            if not valor_txt:
                self.label_aviso_limite.setVisible(False)
                return
            
            valor = float(valor_txt)
            
            # Obter informações de limite
            info_limite = obter_info_limite(cartao_id)
            limite_disponivel = info_limite['limite_disponivel']
            
            # Exibir aviso se exceder limite
            if valor > limite_disponivel:
                self.label_aviso_limite.setText(
                    f"⚠️ Compra excede limite disponível (R$ {limite_disponivel:.2f})"
                )
                self.label_aviso_limite.setVisible(True)
            else:
                self.label_aviso_limite.setVisible(False)
                
        except (ValueError, KeyError):
            self.label_aviso_limite.setVisible(False)
        except Exception as e:
            print(f"Erro ao verificar limite: {e}")
            self.label_aviso_limite.setVisible(False)

    def salvar(self):
        """Valida e salva a compra no cartão."""
        # Coletar dados do formulário
        cartao_id = self.combo_cartao.currentData()
        descricao = self.input_descricao.text().strip()
        valor_txt = self.input_valor.text().replace(",", ".")
        data_compra = self.input_data.date().toString("yyyy-MM-dd")
        categoria_id = self.combo_categoria.currentData()
        
        # Validate-Then-Execute: Validar com Pydantic antes de operações de banco
        try:
            # Converter valor para Decimal
            valor = Decimal(valor_txt) if valor_txt else Decimal(0)
            
            # Validar com CompraCartaoModel
            compra_validada = CompraCartaoModel(
                cartao_id=cartao_id if cartao_id else 0,
                descricao=descricao,
                valor=valor,
                data_compra=data_compra,
                categoria_id=categoria_id
            )
            
            # Verificar limite e avisar (mas permitir continuar)
            info_limite = obter_info_limite(compra_validada.cartao_id)
            if float(compra_validada.valor) > info_limite['limite_disponivel']:
                resposta = QMessageBox.question(
                    self,
                    "Limite Excedido",
                    f"A compra de R$ {float(compra_validada.valor):.2f} excede o limite disponível "
                    f"de R$ {info_limite['limite_disponivel']:.2f}.\n\n"
                    "Deseja continuar mesmo assim?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if resposta == QMessageBox.StandardButton.No:
                    return
            
            # Se validação passou, criar compra
            if self.radio_vista.isChecked():
                # Compra à vista
                compra_id = criar_compra_cartao(
                    cartao_id=compra_validada.cartao_id,
                    descricao=compra_validada.descricao,
                    valor=float(compra_validada.valor),
                    data_compra=compra_validada.data_compra,
                    categoria_id=compra_validada.categoria_id
                )
                
                QMessageBox.information(
                    self, 
                    "Sucesso", 
                    f"Compra à vista registrada com sucesso!\n"
                    f"Valor: R$ {float(compra_validada.valor):.2f}"
                )
            else:
                # Compra parcelada
                numero_parcelas = self.input_parcelas.value()
                
                compra_parcelada_id = criar_compra_parcelada_cartao(
                    cartao_id=compra_validada.cartao_id,
                    descricao=compra_validada.descricao,
                    valor_total=float(compra_validada.valor),
                    numero_parcelas=numero_parcelas,
                    data_compra=compra_validada.data_compra,
                    categoria_id=compra_validada.categoria_id
                )
                
                valor_parcela = float(compra_validada.valor) / numero_parcelas
                QMessageBox.information(
                    self, 
                    "Sucesso", 
                    f"Compra parcelada registrada com sucesso!\n"
                    f"{numero_parcelas} parcelas de R$ {valor_parcela:.2f}"
                )
            
            # Emitir sinal de atualização
            self.dados_atualizados.emit()
            
            # Fechar dialog
            self.accept()
            
        except ValidationError as e:
            # Exibir mensagens de erro específicas por campo
            erros = []
            for erro in e.errors():
                campo = erro['loc'][0] if erro['loc'] else 'campo'
                mensagem = erro['msg']
                
                # Traduzir nomes de campos para português
                campo_pt = {
                    'cartao_id': 'Cartão',
                    'descricao': 'Descrição',
                    'valor': 'Valor',
                    'data_compra': 'Data da Compra',
                    'categoria_id': 'Categoria'
                }.get(campo, campo)
                
                erros.append(f"• {campo_pt}: {mensagem}")
            
            QMessageBox.warning(self, "Erro de Validação", "\n".join(erros))
            
        except (ValueError, KeyError, Exception) as e:
            QMessageBox.critical(self, "Erro", f"Erro ao registrar compra: {str(e)}")
