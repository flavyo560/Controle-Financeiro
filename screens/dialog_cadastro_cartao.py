from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QSpinBox, QComboBox, 
    QLabel, QMessageBox, QCheckBox
)
from PyQt6.QtCore import pyqtSignal
from database import conectar, criar_cartao, editar_cartao, calcular_limite_utilizado
from models.validators import CartaoModel
from pydantic import ValidationError
from decimal import Decimal


class DialogCadastroCartao(QDialog):
    """Dialog para cadastro e edição de cartões de crédito."""
    
    dados_atualizados = pyqtSignal()

    def __init__(self, parent=None, cartao_id=None):
        super().__init__(parent)
        self.cartao_id = cartao_id
        self.modo_edicao = cartao_id is not None
        
        self.setWindowTitle("Editar Cartão" if self.modo_edicao else "Novo Cartão")
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
            QLineEdit, QComboBox, QSpinBox {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
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
            QCheckBox {
                color: #a4b0be;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #333333;
                border-radius: 3px;
                background-color: #1a1a1a;
            }
            QCheckBox::indicator:checked {
                background-color: #ff0055;
            }
        """)
        
        self._setup_ui()
        
        # Carregar dados se estiver em modo edição
        if self.modo_edicao:
            self._carregar_dados_cartao()

    def _setup_ui(self):
        """Configura a interface do dialog."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        titulo_texto = "EDITAR CARTÃO" if self.modo_edicao else "NOVO CARTÃO"
        titulo = QLabel(titulo_texto)
        titulo.setStyleSheet("font-size:16px; font-weight:bold; color: #ff0055; margin-bottom: 10px;")
        layout.addWidget(titulo)
        
        # Formulário
        form = QFormLayout()
        form.setSpacing(10)
        
        # Campo Nome
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Ex: Nubank Platinum")
        form.addRow("Nome:", self.input_nome)
        
        # Campo Bandeira
        self.combo_bandeira = QComboBox()
        self.combo_bandeira.addItem("", None)  # Opção vazia
        self.combo_bandeira.addItem("Visa", "Visa")
        self.combo_bandeira.addItem("Mastercard", "Mastercard")
        self.combo_bandeira.addItem("Elo", "Elo")
        self.combo_bandeira.addItem("Amex", "Amex")
        self.combo_bandeira.addItem("Hipercard", "Hipercard")
        self.combo_bandeira.addItem("Outro", "Outro")
        form.addRow("Bandeira:", self.combo_bandeira)
        
        # Campo Limite Total
        self.input_limite = QLineEdit()
        self.input_limite.setPlaceholderText("Ex: 5000.00")
        form.addRow("Limite Total:", self.input_limite)
        
        # Campo Dia Fechamento
        self.input_dia_fechamento = QSpinBox()
        self.input_dia_fechamento.setMinimum(1)
        self.input_dia_fechamento.setMaximum(31)
        self.input_dia_fechamento.setValue(10)
        form.addRow("Dia Fechamento:", self.input_dia_fechamento)
        
        # Campo Dia Vencimento
        self.input_dia_vencimento = QSpinBox()
        self.input_dia_vencimento.setMinimum(1)
        self.input_dia_vencimento.setMaximum(31)
        self.input_dia_vencimento.setValue(20)
        form.addRow("Dia Vencimento:", self.input_dia_vencimento)
        
        # Campo Status (apenas em modo edição)
        self.check_ativo = QCheckBox("Cartão Ativo")
        self.check_ativo.setChecked(True)
        form.addRow("Status:", self.check_ativo)
        
        layout.addLayout(form)
        
        # Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.setObjectName("btn_salvar")
        self.btn_salvar.clicked.connect(self.salvar)
        
        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_cancelar)
        botoes_layout.addWidget(self.btn_salvar)
        
        layout.addLayout(botoes_layout)

    def _carregar_dados_cartao(self):
        """Carrega os dados do cartão para edição."""
        try:
            conn = conectar()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT nome, bandeira, limite_total, dia_fechamento, 
                       dia_vencimento, status
                FROM cartoes
                WHERE id = ?
            """, (self.cartao_id,))
            
            resultado = cur.fetchone()
            conn.close()
            
            if not resultado:
                QMessageBox.warning(self, "Erro", "Cartão não encontrado.")
                self.reject()
                return
            
            nome, bandeira, limite_total, dia_fechamento, dia_vencimento, status = resultado
            
            # Preencher campos
            self.input_nome.setText(nome)
            
            # Selecionar bandeira
            if bandeira:
                index = self.combo_bandeira.findData(bandeira)
                if index >= 0:
                    self.combo_bandeira.setCurrentIndex(index)
            
            self.input_limite.setText(str(limite_total))
            self.input_dia_fechamento.setValue(dia_fechamento)
            self.input_dia_vencimento.setValue(dia_vencimento)
            self.check_ativo.setChecked(status == 1)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados do cartão: {str(e)}")
            self.reject()

    def salvar(self):
        """Valida e salva o cartão (criação ou edição)."""
        # Coletar dados do formulário
        nome = self.input_nome.text().strip()
        limite_txt = self.input_limite.text().replace(",", ".")
        dia_fechamento = self.input_dia_fechamento.value()
        dia_vencimento = self.input_dia_vencimento.value()
        bandeira = self.combo_bandeira.currentData()
        status = 1 if self.check_ativo.isChecked() else 0
        
        # Validate-Then-Execute: Validar com Pydantic antes de operações de banco
        try:
            # Converter limite para Decimal
            limite_total = Decimal(limite_txt) if limite_txt else Decimal(0)
            
            # Validar com CartaoModel
            cartao_validado = CartaoModel(
                nome=nome,
                limite_total=limite_total,
                dia_fechamento=dia_fechamento,
                dia_vencimento=dia_vencimento,
                bandeira=bandeira
            )
            
            # Se validação passou, prosseguir com operação de banco
            if self.modo_edicao:
                # Modo edição - validar que novo limite >= limite_utilizado
                limite_utilizado = calcular_limite_utilizado(self.cartao_id)
                if float(cartao_validado.limite_total) < limite_utilizado:
                    QMessageBox.warning(
                        self, 
                        "Erro", 
                        f"O novo limite (R$ {float(cartao_validado.limite_total):.2f}) não pode ser menor que "
                        f"o limite utilizado (R$ {limite_utilizado:.2f})."
                    )
                    return
                
                novos_dados = {
                    'nome': cartao_validado.nome,
                    'bandeira': cartao_validado.bandeira,
                    'limite_total': float(cartao_validado.limite_total),
                    'dia_fechamento': cartao_validado.dia_fechamento,
                    'dia_vencimento': cartao_validado.dia_vencimento,
                    'status': status
                }
                
                editar_cartao(self.cartao_id, novos_dados)
                
                QMessageBox.information(self, "Sucesso", "Cartão atualizado com sucesso!")
            else:
                # Modo criação
                cartao_id = criar_cartao(
                    nome=cartao_validado.nome,
                    limite_total=float(cartao_validado.limite_total),
                    dia_fechamento=cartao_validado.dia_fechamento,
                    dia_vencimento=cartao_validado.dia_vencimento,
                    bandeira=cartao_validado.bandeira
                )
                
                QMessageBox.information(
                    self, 
                    "Sucesso", 
                    f"Cartão '{cartao_validado.nome}' criado com sucesso!"
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
                    'nome': 'Nome',
                    'limite_total': 'Limite Total',
                    'dia_fechamento': 'Dia Fechamento',
                    'dia_vencimento': 'Dia Vencimento',
                    'bandeira': 'Bandeira'
                }.get(campo, campo)
                
                erros.append(f"• {campo_pt}: {mensagem}")
            
            QMessageBox.warning(self, "Erro de Validação", "\n".join(erros))
            
        except (ValueError, Exception) as e:
            # Tratar erro de nome duplicado
            if "Já existe um cartão com o nome" in str(e):
                QMessageBox.warning(self, "Erro", str(e))
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar cartão: {str(e)}")
