from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QSpinBox, QDateEdit,
    QComboBox, QLabel, QMessageBox
)
from PyQt6.QtCore import QDate, pyqtSignal
from database import conectar, criar_despesa_parcelada
from models.validators import DespesaParceladaModel
from pydantic import ValidationError
from decimal import Decimal


class DialogDespesaParcelada(QDialog):
    """Dialog para registro de despesas parceladas."""
    
    dados_atualizados = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova Despesa Parcelada")
        self.setModal(True)
        self.resize(500, 400)
        
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
            QPushButton#btn_ok {
                background-color: #ff0055;
                color: white;
            }
            QPushButton#btn_ok:hover {
                background-color: #e6004d;
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
        titulo = QLabel("REGISTRAR DESPESA PARCELADA")
        titulo.setStyleSheet("font-size:16px; font-weight:bold; color: #ff0055; margin-bottom: 10px;")
        layout.addWidget(titulo)
        
        # Formulário
        form = QFormLayout()
        form.setSpacing(10)
        
        # Campo Descrição
        self.input_descricao = QLineEdit()
        self.input_descricao.setPlaceholderText("Ex: Notebook Dell")
        form.addRow("Descrição:", self.input_descricao)
        
        # Campo Valor Total
        self.input_valor_total = QLineEdit()
        self.input_valor_total.setPlaceholderText("Ex: 3000.00")
        form.addRow("Valor Total:", self.input_valor_total)
        
        # Campo Número de Parcelas
        self.input_numero_parcelas = QSpinBox()
        self.input_numero_parcelas.setMinimum(2)
        self.input_numero_parcelas.setMaximum(120)
        self.input_numero_parcelas.setValue(12)
        form.addRow("Número de Parcelas:", self.input_numero_parcelas)
        
        # Campo Data Primeira Parcela
        self.input_data_primeira = QDateEdit()
        self.input_data_primeira.setDate(QDate.currentDate())
        self.input_data_primeira.setCalendarPopup(True)
        form.addRow("Data 1ª Parcela:", self.input_data_primeira)
        
        # Campo Categoria
        self.combo_categoria = QComboBox()
        self.combo_categoria.setPlaceholderText("Selecione a categoria")
        form.addRow("Categoria:", self.combo_categoria)
        
        # Campo Banco
        self.combo_banco = QComboBox()
        self.combo_banco.setPlaceholderText("Selecione o banco")
        form.addRow("Banco:", self.combo_banco)
        
        layout.addLayout(form)
        
        # Label de Preview
        self.label_preview = QLabel("Valor de cada parcela: R$ 0,00")
        self.label_preview.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ff0055; 
            padding: 10px; 
            background-color: #1a1a1a; 
            border-radius: 6px;
            border: 1px solid #333333;
        """)
        layout.addWidget(self.label_preview)
        
        # Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("Criar Despesa Parcelada")
        self.btn_ok.setObjectName("btn_ok")
        self.btn_ok.clicked.connect(self.salvar)
        
        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_cancelar)
        botoes_layout.addWidget(self.btn_ok)
        
        layout.addLayout(botoes_layout)

    def _carregar_dados(self):
        """Carrega categorias e bancos do banco de dados."""
        self._carregar_categorias()
        self._carregar_bancos()

    def _carregar_categorias(self):
        """Carrega categorias de despesa."""
        self.combo_categoria.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM categorias WHERE tipo = 'despesa' ORDER BY nome")
            for cat_id, nome in cur.fetchall():
                self.combo_categoria.addItem(nome, cat_id)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")

    def _carregar_bancos(self):
        """Carrega bancos cadastrados."""
        self.combo_banco.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM bancos ORDER BY nome")
            for banco_id, nome in cur.fetchall():
                self.combo_banco.addItem(nome, banco_id)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar bancos: {e}")

    def _conectar_sinais(self):
        """Conecta sinais para atualização em tempo real do preview."""
        self.input_valor_total.textChanged.connect(self.calcular_preview)
        self.input_numero_parcelas.valueChanged.connect(self.calcular_preview)

    def calcular_preview(self):
        """Calcula e atualiza o preview do valor de cada parcela."""
        try:
            valor_total_txt = self.input_valor_total.text().replace(",", ".")
            if not valor_total_txt:
                self.label_preview.setText("Valor de cada parcela: R$ 0,00")
                return
            
            valor_total = float(valor_total_txt)
            numero_parcelas = self.input_numero_parcelas.value()
            
            if numero_parcelas > 0:
                valor_parcela = valor_total / numero_parcelas
                self.label_preview.setText(f"Valor de cada parcela: R$ {valor_parcela:.2f}")
            else:
                self.label_preview.setText("Valor de cada parcela: R$ 0,00")
                
        except ValueError:
            self.label_preview.setText("Valor de cada parcela: R$ 0,00")

    def salvar(self):
        """Valida e salva a despesa parcelada."""
        # Coletar dados do formulário
        descricao = self.input_descricao.text().strip()
        valor_total_txt = self.input_valor_total.text().replace(",", ".")
        numero_parcelas = self.input_numero_parcelas.value()
        data_primeira = self.input_data_primeira.date().toString("yyyy-MM-dd")
        categoria_id = self.combo_categoria.currentData()
        banco_id = self.combo_banco.currentData()
        
        # Validate-Then-Execute: Validar com Pydantic antes de operações de banco
        try:
            # Converter valor para Decimal
            valor_total = Decimal(valor_total_txt) if valor_total_txt else Decimal(0)
            
            # Validar com DespesaParceladaModel
            despesa_validada = DespesaParceladaModel(
                descricao=descricao,
                valor_total=valor_total,
                numero_parcelas=numero_parcelas,
                data_primeira_parcela=data_primeira,
                categoria_id=categoria_id,
                banco_id=banco_id
            )
            
            # Se validação passou, criar despesa parcelada
            despesa_parcelada_id = criar_despesa_parcelada(
                descricao=despesa_validada.descricao,
                valor_total=float(despesa_validada.valor_total),
                numero_parcelas=despesa_validada.numero_parcelas,
                data_primeira_parcela=despesa_validada.data_primeira_parcela,
                categoria_id=despesa_validada.categoria_id,
                banco_id=despesa_validada.banco_id
            )
            
            # Exibir mensagem de sucesso
            valor_parcela = float(despesa_validada.valor_total) / despesa_validada.numero_parcelas
            QMessageBox.information(
                self, 
                "Sucesso", 
                f"Despesa parcelada criada com sucesso!\n"
                f"{despesa_validada.numero_parcelas} parcelas de R$ {valor_parcela:.2f} foram geradas."
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
                    'descricao': 'Descrição',
                    'valor_total': 'Valor Total',
                    'numero_parcelas': 'Número de Parcelas',
                    'data_primeira_parcela': 'Data da Primeira Parcela',
                    'categoria_id': 'Categoria',
                    'banco_id': 'Banco'
                }.get(campo, campo)
                
                erros.append(f"• {campo_pt}: {mensagem}")
            
            QMessageBox.warning(self, "Erro de Validação", "\n".join(erros))
            
        except (ValueError, Exception) as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar despesa parcelada: {str(e)}")
