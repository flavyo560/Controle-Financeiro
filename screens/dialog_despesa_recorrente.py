from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QSpinBox, QDateEdit,
    QComboBox, QLabel, QMessageBox, QTableWidget,
    QTableWidgetItem, QCheckBox, QWidget, QHeaderView
)
from PyQt6.QtCore import QDate, pyqtSignal, Qt
from database import (
    conectar, criar_despesa_recorrente, listar_despesas_recorrentes,
    editar_despesa_recorrente, desativar_despesa_recorrente,
    excluir_despesa_recorrente, listar_lancamentos_recorrente
)
from models.validators import DespesaRecorrenteModel
from pydantic import ValidationError
from decimal import Decimal


class DialogDespesaRecorrente(QDialog):
    """Dialog para gerenciamento de despesas recorrentes."""
    
    dados_atualizados = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Despesas Recorrentes")
        self.setModal(True)
        self.resize(900, 600)
        
        self.modo_edicao = False
        self.recorrente_id_edicao = None
        
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
            QPushButton#btn_adicionar, QPushButton#btn_salvar {
                background-color: #ff0055;
                color: white;
            }
            QPushButton#btn_adicionar:hover, QPushButton#btn_salvar:hover {
                background-color: #e6004d;
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
            }
            QHeaderView::section {
                background-color: #1f1f1f;
                color: #a4b0be;
                padding: 8px;
                border: 1px solid #333333;
                font-weight: bold;
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
        self._carregar_dados()
        self._carregar_tabela()

    def _setup_ui(self):
        """Configura a interface do dialog."""
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(20, 20, 20, 20)
        self.layout_principal.setSpacing(15)
        
        # Título
        self.titulo = QLabel("GERENCIAR DESPESAS RECORRENTES")
        self.titulo.setStyleSheet("font-size:16px; font-weight:bold; color: #ff0055; margin-bottom: 10px;")
        self.layout_principal.addWidget(self.titulo)
        
        # Container para modo listagem
        self.container_listagem = QWidget()
        self._setup_modo_listagem()
        self.layout_principal.addWidget(self.container_listagem)
        
        # Container para modo edição (inicialmente oculto)
        self.container_edicao = QWidget()
        self._setup_modo_edicao()
        self.layout_principal.addWidget(self.container_edicao)
        
        # Mostrar modo listagem por padrão
        self.container_listagem.setVisible(True)
        self.container_edicao.setVisible(False)

    def _setup_modo_listagem(self):
        """Configura o modo de listagem."""
        layout = QVBoxLayout(self.container_listagem)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels([
            "Descrição", "Valor", "Dia", "Categoria", "Banco", "Status"
        ])
        self.tabela.horizontalHeader().setStretchLastSection(False)
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.tabela)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        
        self.btn_adicionar = QPushButton("Adicionar")
        self.btn_adicionar.setObjectName("btn_adicionar")
        self.btn_adicionar.clicked.connect(self.adicionar_recorrente)
        
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.clicked.connect(self.editar_recorrente)
        
        self.btn_desativar = QPushButton("Desativar")
        self.btn_desativar.clicked.connect(self.desativar_recorrente)
        
        self.btn_excluir = QPushButton("Excluir")
        self.btn_excluir.clicked.connect(self.excluir_recorrente)
        
        self.btn_ver_historico = QPushButton("Ver Histórico")
        self.btn_ver_historico.clicked.connect(self.ver_historico)
        
        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.clicked.connect(self.accept)
        
        botoes_layout.addWidget(self.btn_adicionar)
        botoes_layout.addWidget(self.btn_editar)
        botoes_layout.addWidget(self.btn_desativar)
        botoes_layout.addWidget(self.btn_excluir)
        botoes_layout.addWidget(self.btn_ver_historico)
        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_fechar)
        
        layout.addLayout(botoes_layout)

    def _setup_modo_edicao(self):
        """Configura o modo de edição/criação."""
        layout = QVBoxLayout(self.container_edicao)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Formulário
        form = QFormLayout()
        form.setSpacing(10)
        
        # Campo Descrição
        self.input_descricao = QLineEdit()
        self.input_descricao.setPlaceholderText("Ex: Aluguel")
        form.addRow("Descrição:", self.input_descricao)
        
        # Campo Valor
        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Ex: 1500.00")
        form.addRow("Valor:", self.input_valor)
        
        # Campo Dia do Mês
        self.input_dia_mes = QSpinBox()
        self.input_dia_mes.setMinimum(1)
        self.input_dia_mes.setMaximum(31)
        self.input_dia_mes.setValue(1)
        form.addRow("Dia do Mês:", self.input_dia_mes)
        
        # Campo Categoria
        self.combo_categoria = QComboBox()
        self.combo_categoria.setPlaceholderText("Selecione a categoria")
        form.addRow("Categoria:", self.combo_categoria)
        
        # Campo Banco
        self.combo_banco = QComboBox()
        self.combo_banco.setPlaceholderText("Selecione o banco")
        form.addRow("Banco:", self.combo_banco)
        
        # Campo Data Início
        self.input_data_inicio = QDateEdit()
        self.input_data_inicio.setDate(QDate.currentDate())
        self.input_data_inicio.setCalendarPopup(True)
        form.addRow("Data Início:", self.input_data_inicio)
        
        # Campo Data Fim (opcional)
        data_fim_layout = QHBoxLayout()
        self.check_data_fim = QCheckBox("Definir data de término")
        self.input_data_fim = QDateEdit()
        self.input_data_fim.setDate(QDate.currentDate().addYears(1))
        self.input_data_fim.setCalendarPopup(True)
        self.input_data_fim.setEnabled(False)
        self.check_data_fim.toggled.connect(self.input_data_fim.setEnabled)
        data_fim_layout.addWidget(self.check_data_fim)
        data_fim_layout.addWidget(self.input_data_fim)
        form.addRow("Data Fim:", data_fim_layout)
        
        # Checkbox para atualizar lançamentos futuros (apenas em modo edição)
        self.check_atualizar_futuros = QCheckBox("Atualizar lançamentos futuros")
        self.check_atualizar_futuros.setVisible(False)
        form.addRow("", self.check_atualizar_futuros)
        
        layout.addLayout(form)
        
        # Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        
        self.btn_cancelar_edicao = QPushButton("Cancelar")
        self.btn_cancelar_edicao.clicked.connect(self.cancelar_edicao)
        
        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.setObjectName("btn_salvar")
        self.btn_salvar.clicked.connect(self.salvar_recorrente)
        
        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_cancelar_edicao)
        botoes_layout.addWidget(self.btn_salvar)
        
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

    def _carregar_tabela(self):
        """Carrega as despesas recorrentes na tabela."""
        try:
            despesas = listar_despesas_recorrentes(incluir_inativas=True)
            
            self.tabela.setRowCount(len(despesas))
            
            for row, despesa in enumerate(despesas):
                # Descrição
                self.tabela.setItem(row, 0, QTableWidgetItem(despesa['descricao']))
                
                # Valor
                valor_item = QTableWidgetItem(f"R$ {despesa['valor']:.2f}")
                valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 1, valor_item)
                
                # Dia
                dia_item = QTableWidgetItem(str(despesa['dia_mes']))
                dia_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela.setItem(row, 2, dia_item)
                
                # Categoria
                self.tabela.setItem(row, 3, QTableWidgetItem(despesa['categoria_nome'] or '-'))
                
                # Banco
                self.tabela.setItem(row, 4, QTableWidgetItem(despesa['banco_nome'] or '-'))
                
                # Status
                status = "Ativa" if despesa['ativa'] else "Inativa"
                status_item = QTableWidgetItem(status)
                if despesa['ativa']:
                    status_item.setForeground(Qt.GlobalColor.green)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela.setItem(row, 5, status_item)
                
                # Armazenar ID na linha
                self.tabela.item(row, 0).setData(Qt.ItemDataRole.UserRole, despesa['id'])
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar despesas recorrentes: {str(e)}")

    def alternar_modo_edicao(self, modo_edicao=True, recorrente_id=None):
        """Alterna entre modo listagem e modo edição."""
        self.modo_edicao = modo_edicao
        self.recorrente_id_edicao = recorrente_id
        
        if modo_edicao:
            self.container_listagem.setVisible(False)
            self.container_edicao.setVisible(True)
            
            if recorrente_id:
                # Modo edição - carregar dados
                self.titulo.setText("EDITAR DESPESA RECORRENTE")
                self.btn_salvar.setText("Salvar Alterações")
                self.check_atualizar_futuros.setVisible(True)
                self._carregar_dados_edicao(recorrente_id)
            else:
                # Modo criação - limpar campos
                self.titulo.setText("ADICIONAR DESPESA RECORRENTE")
                self.btn_salvar.setText("Criar Despesa Recorrente")
                self.check_atualizar_futuros.setVisible(False)
                self._limpar_campos()
        else:
            self.container_edicao.setVisible(False)
            self.container_listagem.setVisible(True)
            self.titulo.setText("GERENCIAR DESPESAS RECORRENTES")

    def _limpar_campos(self):
        """Limpa os campos do formulário."""
        self.input_descricao.clear()
        self.input_valor.clear()
        self.input_dia_mes.setValue(1)
        self.combo_categoria.setCurrentIndex(-1)
        self.combo_banco.setCurrentIndex(-1)
        self.input_data_inicio.setDate(QDate.currentDate())
        self.check_data_fim.setChecked(False)
        self.input_data_fim.setDate(QDate.currentDate().addYears(1))
        self.check_atualizar_futuros.setChecked(False)

    def _carregar_dados_edicao(self, recorrente_id):
        """Carrega os dados de uma despesa recorrente para edição."""
        try:
            despesas = listar_despesas_recorrentes(incluir_inativas=True)
            despesa = next((d for d in despesas if d['id'] == recorrente_id), None)
            
            if not despesa:
                QMessageBox.warning(self, "Erro", "Despesa recorrente não encontrada.")
                self.cancelar_edicao()
                return
            
            self.input_descricao.setText(despesa['descricao'])
            self.input_valor.setText(str(despesa['valor']))
            self.input_dia_mes.setValue(despesa['dia_mes'])
            
            # Selecionar categoria
            index = self.combo_categoria.findData(despesa['categoria_id'])
            if index >= 0:
                self.combo_categoria.setCurrentIndex(index)
            
            # Selecionar banco
            index = self.combo_banco.findData(despesa['banco_id'])
            if index >= 0:
                self.combo_banco.setCurrentIndex(index)
            
            # Data início
            from datetime import datetime
            data_inicio = datetime.strptime(despesa['data_inicio'], '%Y-%m-%d')
            self.input_data_inicio.setDate(QDate(data_inicio.year, data_inicio.month, data_inicio.day))
            
            # Data fim
            if despesa['data_fim']:
                self.check_data_fim.setChecked(True)
                data_fim = datetime.strptime(despesa['data_fim'], '%Y-%m-%d')
                self.input_data_fim.setDate(QDate(data_fim.year, data_fim.month, data_fim.day))
            else:
                self.check_data_fim.setChecked(False)
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {str(e)}")

    def adicionar_recorrente(self):
        """Abre o modo de criação."""
        self.alternar_modo_edicao(modo_edicao=True, recorrente_id=None)

    def editar_recorrente(self):
        """Abre o modo de edição para a despesa selecionada."""
        linha_selecionada = self.tabela.currentRow()
        if linha_selecionada < 0:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma despesa recorrente para editar.")
            return
        
        recorrente_id = self.tabela.item(linha_selecionada, 0).data(Qt.ItemDataRole.UserRole)
        self.alternar_modo_edicao(modo_edicao=True, recorrente_id=recorrente_id)

    def cancelar_edicao(self):
        """Cancela a edição e volta para o modo listagem."""
        self.alternar_modo_edicao(modo_edicao=False)

    def salvar_recorrente(self):
        """Valida e salva a despesa recorrente (criação ou edição)."""
        # Coletar dados do formulário
        descricao = self.input_descricao.text().strip()
        valor_txt = self.input_valor.text().replace(",", ".")
        dia_mes = self.input_dia_mes.value()
        categoria_id = self.combo_categoria.currentData()
        banco_id = self.combo_banco.currentData()
        data_inicio = self.input_data_inicio.date().toString("yyyy-MM-dd")
        data_fim = self.input_data_fim.date().toString("yyyy-MM-dd") if self.check_data_fim.isChecked() else None
        
        # Validate-Then-Execute: Validar com Pydantic antes de operações de banco
        try:
            # Converter valor para Decimal
            valor = Decimal(valor_txt) if valor_txt else Decimal(0)
            
            # Validar com DespesaRecorrenteModel
            despesa_validada = DespesaRecorrenteModel(
                descricao=descricao,
                valor=valor,
                dia_mes=dia_mes,
                categoria_id=categoria_id,
                banco_id=banco_id,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            # Se validação passou, prosseguir com operação de banco
            if self.recorrente_id_edicao:
                # Modo edição
                novos_dados = {
                    'descricao': despesa_validada.descricao,
                    'valor': float(despesa_validada.valor),
                    'dia_mes': despesa_validada.dia_mes,
                    'categoria_id': despesa_validada.categoria_id,
                    'banco_id': despesa_validada.banco_id,
                    'data_inicio': despesa_validada.data_inicio,
                    'data_fim': despesa_validada.data_fim
                }
                atualizar_futuros = self.check_atualizar_futuros.isChecked()
                
                editar_despesa_recorrente(
                    self.recorrente_id_edicao,
                    novos_dados,
                    atualizar_lancamentos_futuros=atualizar_futuros
                )
                
                QMessageBox.information(self, "Sucesso", "Despesa recorrente atualizada com sucesso!")
            else:
                # Modo criação
                criar_despesa_recorrente(
                    descricao=despesa_validada.descricao,
                    valor=float(despesa_validada.valor),
                    dia_mes=despesa_validada.dia_mes,
                    categoria_id=despesa_validada.categoria_id,
                    banco_id=despesa_validada.banco_id,
                    data_inicio=despesa_validada.data_inicio,
                    data_fim=despesa_validada.data_fim
                )
                
                QMessageBox.information(self, "Sucesso", "Despesa recorrente criada com sucesso!")
            
            # Emitir sinal de atualização
            self.dados_atualizados.emit()
            
            # Voltar para modo listagem e recarregar tabela
            self.alternar_modo_edicao(modo_edicao=False)
            self._carregar_tabela()
            
        except ValidationError as e:
            # Exibir mensagens de erro específicas por campo
            erros = []
            for erro in e.errors():
                campo = erro['loc'][0] if erro['loc'] else 'campo'
                mensagem = erro['msg']
                
                # Traduzir nomes de campos para português
                campo_pt = {
                    'descricao': 'Descrição',
                    'valor': 'Valor',
                    'dia_mes': 'Dia do Mês',
                    'categoria_id': 'Categoria',
                    'banco_id': 'Banco',
                    'data_inicio': 'Data Início',
                    'data_fim': 'Data Fim'
                }.get(campo, campo)
                
                erros.append(f"• {campo_pt}: {mensagem}")
            
            QMessageBox.warning(self, "Erro de Validação", "\n".join(erros))
            
        except (ValueError, Exception) as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar despesa recorrente: {str(e)}")

    def desativar_recorrente(self):
        """Desativa a despesa recorrente selecionada."""
        linha_selecionada = self.tabela.currentRow()
        if linha_selecionada < 0:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma despesa recorrente para desativar.")
            return
        
        recorrente_id = self.tabela.item(linha_selecionada, 0).data(Qt.ItemDataRole.UserRole)
        descricao = self.tabela.item(linha_selecionada, 0).text()
        
        resposta = QMessageBox.question(
            self,
            "Confirmar Desativação",
            f"Deseja desativar a despesa recorrente '{descricao}'?\n\n"
            "Os lançamentos já criados serão mantidos, mas novos lançamentos não serão gerados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                desativar_despesa_recorrente(recorrente_id)
                QMessageBox.information(self, "Sucesso", "Despesa recorrente desativada com sucesso!")
                
                # Emitir sinal e recarregar tabela
                self.dados_atualizados.emit()
                self._carregar_tabela()
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao desativar despesa recorrente: {str(e)}")

    def excluir_recorrente(self):
        """Exclui a despesa recorrente selecionada."""
        linha_selecionada = self.tabela.currentRow()
        if linha_selecionada < 0:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma despesa recorrente para excluir.")
            return
        
        recorrente_id = self.tabela.item(linha_selecionada, 0).data(Qt.ItemDataRole.UserRole)
        descricao = self.tabela.item(linha_selecionada, 0).text()
        
        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir a despesa recorrente '{descricao}'?\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                excluir_despesa_recorrente(recorrente_id, excluir_lancamentos=False)
                QMessageBox.information(self, "Sucesso", "Despesa recorrente excluída com sucesso!")
                
                # Emitir sinal e recarregar tabela
                self.dados_atualizados.emit()
                self._carregar_tabela()
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir despesa recorrente: {str(e)}")

    def ver_historico(self):
        """Exibe o histórico de lançamentos da despesa recorrente selecionada."""
        linha_selecionada = self.tabela.currentRow()
        if linha_selecionada < 0:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma despesa recorrente para ver o histórico.")
            return
        
        recorrente_id = self.tabela.item(linha_selecionada, 0).data(Qt.ItemDataRole.UserRole)
        descricao = self.tabela.item(linha_selecionada, 0).text()
        
        # Criar dialog de histórico
        dialog = DialogHistoricoRecorrente(self, recorrente_id, descricao)
        dialog.exec()


class DialogHistoricoRecorrente(QDialog):
    """Dialog para exibir o histórico de lançamentos de uma despesa recorrente."""
    
    def __init__(self, parent, recorrente_id, descricao):
        super().__init__(parent)
        self.recorrente_id = recorrente_id
        self.descricao = descricao
        
        self.setWindowTitle(f"Histórico: {descricao}")
        self.setModal(True)
        self.resize(700, 500)
        
        # Aplicar estilo dark mode
        self.setStyleSheet("""
            QDialog { 
                background-color: #0b0b0b; 
                color: white; 
            }
            QLabel { 
                color: #a4b0be; 
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
            QHeaderView::section {
                background-color: #1f1f1f;
                color: #a4b0be;
                padding: 8px;
                border: 1px solid #333333;
                font-weight: bold;
            }
        """)
        
        self._setup_ui()
        self._carregar_historico()

    def _setup_ui(self):
        """Configura a interface do dialog."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        titulo = QLabel(f"HISTÓRICO DE LANÇAMENTOS: {self.descricao}")
        titulo.setStyleSheet("font-size:14px; font-weight:bold; color: #ff0055; margin-bottom: 10px;")
        layout.addWidget(titulo)
        
        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Data", "Descrição", "Valor", "Categoria"])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabela)
        
        # Botão Fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar)

    def _carregar_historico(self):
        """Carrega o histórico de lançamentos."""
        try:
            lancamentos = listar_lancamentos_recorrente(self.recorrente_id)
            
            self.tabela.setRowCount(len(lancamentos))
            
            for row, lanc in enumerate(lancamentos):
                # Data
                from datetime import datetime
                data = datetime.strptime(lanc['data'], '%Y-%m-%d')
                data_item = QTableWidgetItem(data.strftime('%d/%m/%Y'))
                data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela.setItem(row, 0, data_item)
                
                # Descrição
                self.tabela.setItem(row, 1, QTableWidgetItem(lanc['descricao']))
                
                # Valor
                valor_item = QTableWidgetItem(f"R$ {lanc['valor']:.2f}")
                valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 2, valor_item)
                
                # Categoria
                self.tabela.setItem(row, 3, QTableWidgetItem(lanc['categoria_nome'] or '-'))
            
            if len(lancamentos) == 0:
                QMessageBox.information(self, "Informação", "Nenhum lançamento encontrado para esta despesa recorrente.")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar histórico: {str(e)}")
