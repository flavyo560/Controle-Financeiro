from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QHeaderView, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from database import conectar, listar_cartoes, desativar_cartao, excluir_cartao

class TelaCartoes(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestão de Cartões de Crédito")
        self.resize(1000, 600)
        
        # Estilo dark mode seguindo o padrão do projeto
        self.setStyleSheet("""
            QWidget { 
                background-color: #0b0b0b; 
                color: white; 
            }
            QLabel { 
                color: #a4b0be; 
                font-weight: bold; 
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
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 3px;
                text-align: center;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #00ffa3;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Título
        titulo = QLabel("💳 GERENCIAR CARTÕES DE CRÉDITO")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #ff0055; margin-bottom: 5px;")
        layout.addWidget(titulo)

        # Toolbar superior com botões de ação
        toolbar = QHBoxLayout()
        toolbar.setSpacing(15)

        self.btn_novo = QPushButton("➕ Novo Cartão")
        self.btn_novo.setStyleSheet("background-color: #ff0055; color: white;")
        self.btn_novo.clicked.connect(self.novo_cartao)

        self.btn_editar = QPushButton("📝 Editar")
        self.btn_editar.clicked.connect(self.editar_cartao)

        self.btn_desativar = QPushButton("🚫 Desativar")
        self.btn_desativar.setStyleSheet("""
            QPushButton { 
                background-color: #1a1a1a; 
                color: #ffa502; 
                border: 1px solid #ffa502; 
            }
            QPushButton:hover { 
                background-color: #ffa502; 
                color: white; 
            }
        """)
        self.btn_desativar.clicked.connect(self.desativar_cartao_selecionado)

        self.btn_excluir = QPushButton("🗑️ Excluir")
        self.btn_excluir.setStyleSheet("""
            QPushButton { 
                background-color: #1a1a1a; 
                color: #ff4757; 
                border: 1px solid #ff4757; 
            }
            QPushButton:hover { 
                background-color: #ff4757; 
                color: white; 
            }
        """)
        self.btn_excluir.clicked.connect(self.excluir_cartao_selecionado)

        toolbar.addWidget(self.btn_novo)
        toolbar.addWidget(self.btn_editar)
        toolbar.addWidget(self.btn_desativar)
        toolbar.addWidget(self.btn_excluir)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Tabela de cartões
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "NOME", "BANDEIRA", "LIMITE TOTAL", 
            "LIMITE DISPONÍVEL", "LIMITE UTILIZADO", "% USO", "STATUS"
        ])
        self.tabela.setColumnHidden(0, True)  # Ocultar coluna ID
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.doubleClicked.connect(self.ver_faturas)

        layout.addWidget(self.tabela)

        # Botões inferiores
        btns_inferior = QHBoxLayout()
        btns_inferior.setSpacing(15)

        self.btn_ver_faturas = QPushButton("📊 Ver Faturas")
        self.btn_ver_faturas.setStyleSheet("background-color: #5f27cd; color: white;")
        self.btn_ver_faturas.clicked.connect(self.ver_faturas)

        self.btn_nova_compra = QPushButton("🛒 Nova Compra")
        self.btn_nova_compra.setStyleSheet("background-color: #00d2d3; color: white;")
        self.btn_nova_compra.clicked.connect(self.nova_compra)

        self.btn_pagar_fatura = QPushButton("💰 Pagar Fatura")
        self.btn_pagar_fatura.setStyleSheet("background-color: #00ffa3; color: black;")
        self.btn_pagar_fatura.clicked.connect(self.pagar_fatura)

        btns_inferior.addStretch()
        btns_inferior.addWidget(self.btn_ver_faturas)
        btns_inferior.addWidget(self.btn_nova_compra)
        btns_inferior.addWidget(self.btn_pagar_fatura)

        layout.addLayout(btns_inferior)

        # Carregar dados
        self.atualizar()

    def atualizar(self):
        """Recarrega a lista de cartões."""
        self.carregar_cartoes()

    def carregar_cartoes(self):
        """Carrega os cartões do banco de dados e preenche a tabela."""
        self.tabela.setRowCount(0)
        
        try:
            cartoes = listar_cartoes(apenas_ativos=True)
            
            for cartao in cartoes:
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                
                # ID (oculto)
                self.tabela.setItem(row, 0, QTableWidgetItem(str(cartao['id'])))
                
                # Nome
                self.tabela.setItem(row, 1, QTableWidgetItem(cartao['nome']))
                
                # Bandeira
                bandeira = cartao['bandeira'] if cartao['bandeira'] else "-"
                self.tabela.setItem(row, 2, QTableWidgetItem(bandeira))
                
                # Limite Total
                item_limite_total = QTableWidgetItem(f"R$ {cartao['limite_total']:.2f}")
                item_limite_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 3, item_limite_total)
                
                # Limite Disponível
                item_disponivel = QTableWidgetItem(f"R$ {cartao['limite_disponivel']:.2f}")
                item_disponivel.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if cartao['limite_disponivel'] < 0:
                    item_disponivel.setForeground(QColor("#ff4757"))
                else:
                    item_disponivel.setForeground(QColor("#00ffa3"))
                self.tabela.setItem(row, 4, item_disponivel)
                
                # Limite Utilizado
                item_utilizado = QTableWidgetItem(f"R$ {cartao['limite_utilizado']:.2f}")
                item_utilizado.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(row, 5, item_utilizado)
                
                # % Uso com barra de progresso visual
                percentual = cartao['percentual_uso']
                
                # Criar widget container para a barra de progresso
                progress_widget = QWidget()
                progress_layout = QHBoxLayout(progress_widget)
                progress_layout.setContentsMargins(5, 2, 5, 2)
                
                progress_bar = QProgressBar()
                progress_bar.setMinimum(0)
                progress_bar.setMaximum(100)
                progress_bar.setValue(int(percentual))
                progress_bar.setFormat(f"{percentual:.1f}%")
                
                # Colorir barra baseado no percentual
                if percentual >= 80:
                    progress_bar.setStyleSheet("""
                        QProgressBar::chunk { background-color: #ff4757; }
                    """)
                    # Destacar linha inteira em vermelho
                    for col in range(self.tabela.columnCount()):
                        if self.tabela.item(row, col):
                            self.tabela.item(row, col).setBackground(QColor("#3d1f1f"))
                elif percentual >= 50:
                    progress_bar.setStyleSheet("""
                        QProgressBar::chunk { background-color: #ffa502; }
                    """)
                
                progress_layout.addWidget(progress_bar)
                self.tabela.setCellWidget(row, 6, progress_widget)
                
                # Status
                status_text = "Ativo" if cartao['status'] == 1 else "Inativo"
                item_status = QTableWidgetItem(status_text)
                item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if cartao['status'] == 1:
                    item_status.setForeground(QColor("#00ffa3"))
                else:
                    item_status.setForeground(QColor("#a4b0be"))
                self.tabela.setItem(row, 7, item_status)
                
        except Exception as e:
            print(f"Erro ao carregar cartões: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar cartões: {e}")

    def novo_cartao(self):
        """Abre o diálogo para criar um novo cartão."""
        from screens.dialog_cadastro_cartao import DialogCadastroCartao
        dialog = DialogCadastroCartao(self)
        dialog.dados_atualizados.connect(self.atualizar)
        dialog.dados_atualizados.connect(self.dados_atualizados.emit)
        dialog.exec()

    def editar_cartao(self):
        """Abre o diálogo para editar o cartão selecionado."""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione um cartão para editar.")
            return
        
        from screens.dialog_cadastro_cartao import DialogCadastroCartao
        cartao_id = int(self.tabela.item(linha, 0).text())
        dialog = DialogCadastroCartao(self, cartao_id=cartao_id)
        dialog.dados_atualizados.connect(self.atualizar)
        dialog.dados_atualizados.connect(self.dados_atualizados.emit)
        dialog.exec()

    def desativar_cartao_selecionado(self):
        """Desativa o cartão selecionado."""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione um cartão para desativar.")
            return
        
        cartao_id = int(self.tabela.item(linha, 0).text())
        nome_cartao = self.tabela.item(linha, 1).text()
        limite_utilizado_text = self.tabela.item(linha, 5).text().replace("R$ ", "")
        
        # Aviso se houver limite utilizado
        mensagem = f"Deseja desativar o cartão '{nome_cartao}'?\n\n"
        mensagem += "O cartão não aparecerá mais para novos lançamentos, "
        mensagem += "mas seu histórico permanecerá salvo."
        
        if float(limite_utilizado_text) > 0:
            mensagem += f"\n\n⚠️ ATENÇÃO: Este cartão possui limite utilizado de R$ {limite_utilizado_text}."
        
        confirm = QMessageBox.question(
            self, "Desativar Cartão", mensagem,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                desativar_cartao(cartao_id)
                self.atualizar()
                self.dados_atualizados.emit()
                QMessageBox.information(self, "Sucesso", "Cartão desativado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao desativar cartão: {e}")

    def excluir_cartao_selecionado(self):
        """Exclui o cartão selecionado."""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione um cartão para excluir.")
            return
        
        cartao_id = int(self.tabela.item(linha, 0).text())
        nome_cartao = self.tabela.item(linha, 1).text()
        
        confirm = QMessageBox.question(
            self, "Excluir Cartão",
            f"Deseja realmente excluir o cartão '{nome_cartao}'?\n\n"
            "⚠️ Esta ação não pode ser desfeita!\n"
            "O cartão só pode ser excluído se não houver compras associadas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                excluir_cartao(cartao_id)
                self.atualizar()
                self.dados_atualizados.emit()
                QMessageBox.information(self, "Sucesso", "Cartão excluído com sucesso!")
            except ValueError as e:
                QMessageBox.warning(self, "Aviso", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir cartão: {e}")

    def ver_faturas(self):
        """Abre o diálogo de visualização de faturas do cartão selecionado."""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione um cartão para ver as faturas.")
            return
        
        from screens.dialog_fatura import DialogFatura
        cartao_id = int(self.tabela.item(linha, 0).text())
        dialog = DialogFatura(self, cartao_id=cartao_id)
        dialog.dados_atualizados.connect(self.atualizar)
        dialog.dados_atualizados.connect(self.dados_atualizados.emit)
        dialog.exec()

    def nova_compra(self):
        """Abre o diálogo para registrar uma nova compra no cartão."""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione um cartão para registrar uma compra.")
            return
        
        from screens.dialog_compra_cartao import DialogCompraCartao
        cartao_id = int(self.tabela.item(linha, 0).text())
        dialog = DialogCompraCartao(self, cartao_id=cartao_id)
        dialog.dados_atualizados.connect(self.atualizar)
        dialog.dados_atualizados.connect(self.dados_atualizados.emit)
        dialog.exec()

    def pagar_fatura(self):
        """Abre o diálogo para pagar a fatura do cartão selecionado."""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione um cartão para pagar a fatura.")
            return
        
        from screens.dialog_fatura import DialogFatura
        cartao_id = int(self.tabela.item(linha, 0).text())
        # Abre o diálogo de fatura, onde o usuário pode registrar pagamentos
        dialog = DialogFatura(self, cartao_id=cartao_id)
        dialog.dados_atualizados.connect(self.atualizar)
        dialog.dados_atualizados.connect(self.dados_atualizados.emit)
        dialog.exec()
