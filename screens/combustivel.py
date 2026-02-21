from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, 
    QDateEdit, QLabel, QHeaderView, QCheckBox
)
from PyQt6.QtCore import QDate, pyqtSignal, Qt
from database.db import conectar, listar_veiculos_ativos

class TelaCombustivel(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.id_edicao = None # Controle de edição
        self.setWindowTitle("Controle de Combustível")
        self.resize(1100, 700)
        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: white; }
            QLabel { color: #a4b0be; font-weight: bold; }
            QLineEdit, QComboBox, QDateEdit { background-color: #1a1a1a; border: 1px solid #333; border-radius: 6px; padding: 8px; color: white; }
            QTableWidget { background-color: #121212; gridline-color: #252525; color: white; border: none; }
            QHeaderView::section { background-color: #1a1a1a; color: #ffb100; padding: 5px; font-weight: bold; border: 1px solid #252525; }
            QPushButton { background-color: #1f1f1f; color: white; border: 1px solid #333; padding: 10px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { border: 1px solid #ffb100; background-color: #252525; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        self.label_titulo = QLabel("⛽ CONTROLE DE ABASTECIMENTO")
        self.label_titulo.setStyleSheet("font-size:18px; color: #ffb100;")
        layout.addWidget(self.label_titulo)

        # --- LINHA 1: DATA, KM, VALOR ---
        linha1 = QHBoxLayout()
        self.input_data = QDateEdit(); self.input_data.setDate(QDate.currentDate()); self.input_data.setCalendarPopup(True)
        self.input_km = QLineEdit(); self.input_km.setPlaceholderText("KM Atual")
        self.input_valor = QLineEdit(); self.input_valor.setPlaceholderText("Valor Total R$")
        linha1.addWidget(QLabel("Data:")); linha1.addWidget(self.input_data)
        linha1.addWidget(QLabel("KM:")); linha1.addWidget(self.input_km)
        linha1.addWidget(QLabel("Total R$:")); linha1.addWidget(self.input_valor)
        layout.addLayout(linha1)

        # --- LINHA VEÍCULO E BANCO ---
        linha_seletores = QHBoxLayout()
        self.combo_veiculos = QComboBox(); self.combo_veiculos.setFixedWidth(200)
        linha_seletores.addWidget(QLabel("Veículo:"))
        linha_seletores.addWidget(self.combo_veiculos)

        self.combo_bancos = QComboBox(); self.combo_bancos.setFixedWidth(200)
        self.check_padrao = QCheckBox("Banco padrão")
        linha_seletores.addWidget(QLabel("Pagar com:"))
        linha_seletores.addWidget(self.combo_bancos)
        linha_seletores.addWidget(self.check_padrao)
        
        linha_seletores.addStretch()
        layout.addLayout(linha_seletores)

        # --- LINHA 2: LITROS E TIPO ---
        linha2 = QHBoxLayout()
        self.input_litros_gas = QLineEdit(); self.input_litros_gas.setPlaceholderText("L. Gasolina")
        self.input_litros_eta = QLineEdit(); self.input_litros_eta.setPlaceholderText("L. Etanol")
        self.combo_tipo = QComboBox(); self.combo_tipo.addItems(["Mistura Flex", "Gasolina", "Etanol", "Diesel"])
        
        self.btn_add = QPushButton("Registrar Abastecimento")
        self.btn_add.setStyleSheet("background-color: #ffb100; color: black;")
        self.btn_add.clicked.connect(self.salvar_abastecimento)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setVisible(False)
        self.btn_cancelar.clicked.connect(self.limpar_campos)

        linha2.addWidget(QLabel("Gasolina (L):")); linha2.addWidget(self.input_litros_gas)
        linha2.addWidget(QLabel("Etanol (L):")); linha2.addWidget(self.input_litros_eta)
        linha2.addWidget(QLabel("Tipo:")); linha2.addWidget(self.combo_tipo)
        linha2.addWidget(self.btn_add)
        linha2.addWidget(self.btn_cancelar)
        layout.addLayout(linha2)

        # --- TABELA ---
        self.tabela = QTableWidget(); self.tabela.setColumnCount(9)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "VEÍCULO", "DATA", "KM", "L. TOTAL", "GASOLINA", "ETANOL", "VALOR", "TIPO"
        ])
        self.tabela.setColumnHidden(0, True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # CONECTAR DUPLO CLIQUE PARA EDITAR
        self.tabela.cellDoubleClicked.connect(self.preparar_edicao)
        
        layout.addWidget(self.tabela)

        self.btn_excluir = QPushButton("🗑️ Excluir"); self.btn_excluir.setFixedWidth(120); self.btn_excluir.clicked.connect(self.excluir_abastecimento)
        layout.addWidget(self.btn_excluir, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.atualizar()

    def carregar_combos(self):
        self.combo_bancos.clear()
        try:
            conn = conectar(); cur = conn.cursor()
            cur.execute("SELECT id, nome FROM bancos WHERE status = 1 ORDER BY nome")
            for b_id, nome in cur.fetchall(): self.combo_bancos.addItem(nome, b_id)
            
            cur.execute("SELECT valor FROM configuracoes WHERE chave = 'banco_padrao_combustivel'")
            res = cur.fetchone()
            if res:
                idx = self.combo_bancos.findData(int(res[0]))
                if idx >= 0: self.combo_bancos.setCurrentIndex(idx)
            conn.close()
        except: pass

        self.combo_veiculos.clear()
        self.combo_veiculos.addItem("Não Informado", None)
        veiculos = listar_veiculos_ativos()
        for v_id, v_nome in veiculos:
            self.combo_veiculos.addItem(v_nome, v_id)

    def preparar_edicao(self, linha, coluna):
        """Carrega os dados da tabela para os inputs"""
        self.id_edicao = self.tabela.item(linha, 0).text()
        
        # Nome do Veículo
        veiculo_nome = self.tabela.item(linha, 1).text()
        idx_v = self.combo_veiculos.findText(veiculo_nome)
        if idx_v >= 0: self.combo_veiculos.setCurrentIndex(idx_v)

        # Data (converte de dd/MM/yyyy para QDate)
        data_str = self.tabela.item(linha, 2).text()
        self.input_data.setDate(QDate.fromString(data_str, "dd/MM/yyyy"))

        self.input_km.setText(self.tabela.item(linha, 3).text())
        
        # Litros
        self.input_litros_gas.setText(self.tabela.item(linha, 5).text())
        self.input_litros_eta.setText(self.tabela.item(linha, 6).text())
        
        # Valor (remove o R$)
        valor_limpo = self.tabela.item(linha, 7).text().replace("R$ ", "").replace(",", "")
        self.input_valor.setText(valor_limpo)

        # Tipo
        idx_t = self.combo_tipo.findText(self.tabela.item(linha, 8).text())
        if idx_t >= 0: self.combo_tipo.setCurrentIndex(idx_t)

        # Visual de Edição
        self.btn_add.setText("✅ Atualizar Lançamento")
        self.btn_add.setStyleSheet("background-color: #ffa500; color: black; font-weight: bold;")
        self.btn_cancelar.setVisible(True)

    def limpar_campos(self):
        self.id_edicao = None
        self.input_km.clear(); self.input_valor.clear()
        self.input_litros_gas.clear(); self.input_litros_eta.clear()
        self.input_data.setDate(QDate.currentDate())
        self.btn_add.setText("Registrar Abastecimento")
        self.btn_add.setStyleSheet("background-color: #ffb100; color: black;")
        self.btn_cancelar.setVisible(False)

    def salvar_abastecimento(self):
        try:
            data = self.input_data.date().toString("yyyy-MM-dd")
            km = float(self.input_km.text().replace(",", ".") or 0)
            valor = float(self.input_valor.text().replace(",", ".") or 0)
            banco_id = self.combo_bancos.currentData()
            veiculo_id = self.combo_veiculos.currentData()

            if km == 0 or valor == 0 or not banco_id:
                QMessageBox.warning(self, "Erro", "Preencha KM, Valor e selecione um Banco.")
                return
            
            gas = float(self.input_litros_gas.text().replace(",", ".") or 0)
            eta = float(self.input_litros_eta.text().replace(",", ".") or 0)
            tipo = self.combo_tipo.currentText()
            
            conn = conectar(); cur = conn.cursor()
            
            if self.id_edicao:
                # MODO UPDATE
                cur.execute("""
                    UPDATE abastecimentos 
                    SET data=?, km=?, litros=?, litros_gasolina=?, litros_etanol=?, valor=?, tipo=?, veiculo_id=?
                    WHERE id=?
                """, (data, km, gas+eta, gas, eta, valor, tipo, veiculo_id, self.id_edicao))
                msg = "Abastecimento atualizado!"
            else:
                # MODO INSERT
                cur.execute("""
                    INSERT INTO abastecimentos 
                    (data, km, litros, litros_gasolina, litros_etanol, valor, tipo, veiculo_id) 
                    VALUES (?,?,?,?,?,?,?,?)
                """, (data, km, gas+eta, gas, eta, valor, tipo, veiculo_id))
                
                # Só gera despesa nova se for registro novo (para não duplicar no financeiro)
                cur.execute("SELECT id FROM categorias WHERE nome = 'Combustível' LIMIT 1")
                res_cat = cur.fetchone(); cat_id = res_cat[0] if res_cat else 1
                desc_veiculo = f" ({self.combo_veiculos.currentText()})" if veiculo_id else ""
                cur.execute("""
                    INSERT INTO despesas (descricao, valor, data, categoria_id, banco_id) 
                    VALUES (?,?,?,?,?)
                """, (f"Combustível: {tipo}{desc_veiculo}", valor, data, cat_id, banco_id))
                msg = "Abastecimento registrado!"

            if self.check_padrao.isChecked():
                cur.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES ('banco_padrao_combustivel', ?)", (str(banco_id),))
            
            conn.commit(); conn.close()
            self.atualizar(); self.dados_atualizados.emit()
            QMessageBox.information(self, "Sucesso", msg)
            self.limpar_campos()

        except Exception as e: QMessageBox.critical(self, "Erro", str(e))

    def carregar_dados(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar(); cur = conn.cursor()
            cur.execute("""
                SELECT a.id, COALESCE(v.nome_identificador, 'Geral'), a.data, a.km, a.litros, 
                       a.litros_gasolina, a.litros_etanol, a.valor, a.tipo 
                FROM abastecimentos a
                LEFT JOIN veiculos v ON a.veiculo_id = v.id
                ORDER BY a.data DESC, a.id DESC
            """)
            
            for row_data in cur.fetchall():
                row = self.tabela.rowCount(); self.tabela.insertRow(row)
                for col, item in enumerate(row_data):
                    val = f"R$ {item:,.2f}" if col == 7 else str(item)
                    if col == 2:
                        try: val = QDate.fromString(item, "yyyy-MM-dd").toString("dd/MM/yyyy")
                        except: pass
                    
                    it = QTableWidgetItem(val)
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabela.setItem(row, col, it)
            conn.close()
        except Exception as e: print(f"Erro ao carregar tabela: {e}")

    def atualizar(self):
        self.carregar_combos()
        self.carregar_dados()

    def excluir_abastecimento(self):
        linha = self.tabela.currentRow()
        if linha < 0: return
        id_reg = self.tabela.item(linha, 0).text()
        if QMessageBox.question(self, "Confirma", "Excluir este registro?") == QMessageBox.StandardButton.Yes:
            conn = conectar(); cur = conn.cursor()
            cur.execute("DELETE FROM abastecimentos WHERE id=?", (id_reg,))
            conn.commit(); conn.close(); self.atualizar(); self.dados_atualizados.emit()