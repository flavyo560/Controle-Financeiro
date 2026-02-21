from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QDateEdit, QLabel, QHeaderView, QComboBox, QCheckBox
)
from PyQt6.QtCore import QDate, pyqtSignal, Qt
from database.db import conectar, listar_veiculos_ativos

class TelaManutencao(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.id_edicao = None # Controle de edição
        self.setWindowTitle("Manutenção de Veículos")
        self.resize(1100, 650)

        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QLabel { color: #a4b0be; font-weight: bold; }
            QLineEdit, QDateEdit, QComboBox {
                background-color: #1a1a1a; border: 1px solid #333333;
                border-radius: 6px; padding: 8px; color: #ffffff;
            }
            QTableWidget {
                background-color: #121212; gridline-color: #252525; color: white;
                selection-background-color: #00ffa3; selection-color: black;
                border: none;
            }
            QHeaderView::section {
                background-color: #1a1a1a; color: #00ffa3;
                padding: 5px; font-weight: bold; border: 1px solid #252525;
            }
            QPushButton {
                background-color: #1f1f1f; color: white; border: 1px solid #333333;
                padding: 10px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { border: 1px solid #00ffa3; background-color: #252525; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        titulo = QLabel("🔧 MANUTENÇÃO E REPAROS")
        titulo.setStyleSheet("font-size:18px; color: #00ffa3;")
        layout.addWidget(titulo)

        # --- LINHA 1 ---
        form1 = QHBoxLayout()
        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        self.input_servico = QLineEdit(); self.input_servico.setPlaceholderText("Serviço")
        self.input_km = QLineEdit(); self.input_km.setPlaceholderText("KM")
        self.input_valor = QLineEdit(); self.input_valor.setPlaceholderText("Valor R$")
        
        form1.addWidget(QLabel("Data:")); form1.addWidget(self.input_data)
        form1.addWidget(QLabel("Serviço:")); form1.addWidget(self.input_servico)
        form1.addWidget(QLabel("KM:")); form1.addWidget(self.input_km)
        form1.addWidget(QLabel("R$:")); form1.addWidget(self.input_valor)
        layout.addLayout(form1)

        # --- LINHA 2 (VEÍCULO E BANCO) ---
        form2 = QHBoxLayout()
        self.combo_veiculos = QComboBox(); self.combo_veiculos.setFixedWidth(200)
        self.combo_bancos = QComboBox(); self.combo_bancos.setFixedWidth(200)
        self.check_padrao = QCheckBox("Definir banco padrão")
        
        self.btn_salvar = QPushButton("Registrar Manutenção")
        self.btn_salvar.setStyleSheet("background-color: #00ffa3; color: black;")
        self.btn_salvar.clicked.connect(self.salvar_manutencao)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setVisible(False)
        self.btn_cancelar.clicked.connect(self.limpar_campos)

        form2.addWidget(QLabel("Veículo:")); form2.addWidget(self.combo_veiculos)
        form2.addWidget(QLabel("Banco:")); form2.addWidget(self.combo_bancos)
        form2.addWidget(self.check_padrao); form2.addStretch()
        form2.addWidget(self.btn_cancelar)
        form2.addWidget(self.btn_salvar)
        layout.addLayout(form2)

        # --- TABELA ---
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(["ID", "VEÍCULO", "DATA", "SERVIÇO", "KM", "VALOR"])
        self.tabela.setColumnHidden(0, True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Conectar duplo clique para editar
        self.tabela.cellDoubleClicked.connect(self.preparar_edicao)
        
        layout.addWidget(self.tabela)

        self.btn_excluir = QPushButton("🗑️ Excluir Registro Selecionado")
        self.btn_excluir.setFixedWidth(250)
        self.btn_excluir.setStyleSheet("color: #ff4757; border: 1px solid #ff4757;")
        self.btn_excluir.clicked.connect(self.excluir_manutencao)
        layout.addWidget(self.btn_excluir, alignment=Qt.AlignmentFlag.AlignRight)

        self.atualizar()

    def preparar_edicao(self, linha, coluna):
        """Carrega dados da tabela para o formulário para edição"""
        self.id_edicao = self.tabela.item(linha, 0).text()
        
        # Selecionar veículo no combo
        veiculo_nome = self.tabela.item(linha, 1).text()
        idx_v = self.combo_veiculos.findText(veiculo_nome)
        if idx_v >= 0: self.combo_veiculos.setCurrentIndex(idx_v)

        # Data
        data_str = self.tabela.item(linha, 2).text()
        self.input_data.setDate(QDate.fromString(data_str, "dd/MM/yyyy"))

        self.input_servico.setText(self.tabela.item(linha, 3).text())
        self.input_km.setText(self.tabela.item(linha, 4).text())
        
        # Valor (Limpar R$)
        valor_limpo = self.tabela.item(linha, 5).text().replace("R$ ", "").replace(",", "")
        self.input_valor.setText(valor_limpo)

        # Mudar estado do botão
        self.btn_salvar.setText("✅ Atualizar Manutenção")
        self.btn_salvar.setStyleSheet("background-color: #ffa500; color: black; font-weight: bold;")
        self.btn_cancelar.setVisible(True)

    def limpar_campos(self):
        self.id_edicao = None
        self.input_servico.clear()
        self.input_km.clear()
        self.input_valor.clear()
        self.input_data.setDate(QDate.currentDate())
        self.btn_salvar.setText("Registrar Manutenção")
        self.btn_salvar.setStyleSheet("background-color: #00ffa3; color: black;")
        self.btn_cancelar.setVisible(False)

    def carregar_combos(self):
        self.combo_veiculos.clear()
        self.combo_veiculos.addItem("Geral / Sem Veículo", None)
        for v_id, v_nome in listar_veiculos_ativos():
            self.combo_veiculos.addItem(v_nome, v_id)

        self.combo_bancos.clear()
        try:
            conn = conectar(); cur = conn.cursor()
            cur.execute("SELECT id, nome FROM bancos WHERE status = 1 ORDER BY nome")
            for b_id, nome in cur.fetchall():
                self.combo_bancos.addItem(nome, b_id)
            
            cur.execute("SELECT valor FROM configuracoes WHERE chave = 'banco_padrao_manutencao'")
            res = cur.fetchone()
            if res:
                idx = self.combo_bancos.findData(int(res[0]))
                if idx >= 0: self.combo_bancos.setCurrentIndex(idx)
            conn.close()
        except: pass

    def salvar_manutencao(self):
        try:
            valor = float(self.input_valor.text().replace(",", ".") or 0)
            banco_id = self.combo_bancos.currentData()
            veiculo_id = self.combo_veiculos.currentData()
            servico = self.input_servico.text().strip()
            
            if valor <= 0 or not banco_id or not servico:
                QMessageBox.warning(self, "Erro", "Preencha o serviço, valor e selecione um banco.")
                return
            
            data = self.input_data.date().toString("yyyy-MM-dd")
            km = self.input_km.text()
            conn = conectar(); cur = conn.cursor()
            
            if self.id_edicao:
                # MODO UPDATE
                cur.execute("""
                    UPDATE manutencoes 
                    SET data=?, servico=?, km=?, valor=?, veiculo_id=?
                    WHERE id=?
                """, (data, servico, km, valor, veiculo_id, self.id_edicao))
                msg = "Manutenção atualizada!"
            else:
                # MODO INSERT
                cur.execute("""
                    INSERT INTO manutencoes (data, servico, km, valor, veiculo_id) 
                    VALUES (?,?,?,?,?)
                """, (data, servico, km, valor, veiculo_id))
                
                # Lança no financeiro apenas se for NOVO (para evitar duplicar despesa no banco)
                cur.execute("SELECT id FROM categorias WHERE nome = 'Manutenção' LIMIT 1")
                res_cat = cur.fetchone(); cat_id = res_cat[0] if res_cat else 1
                desc_veiculo = f" [{self.combo_veiculos.currentText()}]" if veiculo_id else ""
                cur.execute("""
                    INSERT INTO despesas (descricao, valor, data, categoria_id, banco_id) 
                    VALUES (?,?,?,?,?)
                """, (f"Manutenção: {servico}{desc_veiculo}", valor, data, cat_id, banco_id))
                msg = "Manutenção registrada!"

            if self.check_padrao.isChecked():
                cur.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES ('banco_padrao_manutencao', ?)", (str(banco_id),))

            conn.commit(); conn.close()
            self.limpar_campos()
            self.atualizar()
            self.dados_atualizados.emit()
            QMessageBox.information(self, "Sucesso", msg)
        except Exception as e: QMessageBox.critical(self, "Erro", str(e))

    def carregar_dados(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar(); cur = conn.cursor()
            cur.execute("""
                SELECT m.id, COALESCE(v.nome_identificador, 'Geral'), m.data, m.servico, m.km, m.valor 
                FROM manutencoes m
                LEFT JOIN veiculos v ON m.veiculo_id = v.id
                ORDER BY m.data DESC
            """)
            for row in cur.fetchall():
                r = self.tabela.rowCount(); self.tabela.insertRow(r)
                for c, item in enumerate(row):
                    val = f"R$ {item:,.2f}" if c == 5 else str(item)
                    if c == 2:
                        try: val = QDate.fromString(item, "yyyy-MM-dd").toString("dd/MM/yyyy")
                        except: pass
                    
                    it = QTableWidgetItem(val)
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabela.setItem(r, c, it)
            conn.close()
        except Exception as e: print(f"Erro ao carregar tabela: {e}")

    def excluir_manutencao(self):
        linha = self.tabela.currentRow()
        if linha < 0: return
        id_reg = self.tabela.item(linha, 0).text()
        if QMessageBox.question(self, "Excluir", "Deseja excluir este registro?") == QMessageBox.StandardButton.Yes:
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("DELETE FROM manutencoes WHERE id=?", (id_reg,))
                conn.commit(); conn.close()
                self.atualizar(); self.dados_atualizados.emit()
            except Exception as e: QMessageBox.critical(self, "Erro", f"Erro ao excluir: {e}")

    def atualizar(self):
        self.carregar_combos()
        self.carregar_dados()