from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QDateEdit, QLabel, QHeaderView, QCheckBox
)
from PyQt6.QtCore import QDate, pyqtSignal, Qt
from PyQt6.QtGui import QColor
from database import conectar
from screens.dialog_despesa_parcelada import DialogDespesaParcelada
from screens.dialog_despesa_recorrente import DialogDespesaRecorrente
from models.validators import DespesaModel
from pydantic import ValidationError
from decimal import Decimal

class TelaDespesas(QWidget):
    dados_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Despesas")
        self.resize(900, 600)

        self.despesa_id = None
        self.pagina_atual = 0
        self.itens_por_pagina = 20
        self.filtro_parceladas = False  # Novo: controle do filtro
        self.filtro_pagamento = 'todas'  # Novo: filtro de pagamento ('todas', 'pagas', 'nao_pagas')
        self.filtro_vencimento = 'todas'  # Novo: filtro de vencimento

        # 1. ESTILO DA TELA (DARK MODE)
        self.setStyleSheet("""
            QWidget { 
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
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        titulo = QLabel("GERENCIAR DESPESAS")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #ff0055; margin-bottom: 5px;")
        layout.addWidget(titulo)

        # =============================
        # FORMULÁRIO (ADICIONADO CAMPO BANCO)
        # =============================
        form = QHBoxLayout()
        form.setSpacing(10)

        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Descrição da despesa...")

        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Valor (Ex: 50.00)")
        self.input_valor.setFixedWidth(100)

        # Data de Lançamento com label
        data_lanc_layout = QVBoxLayout()
        data_lanc_layout.setSpacing(2)
        lbl_data_lanc = QLabel("Data Lançamento")
        lbl_data_lanc.setStyleSheet("font-size: 9px; color: #00ffa3;")
        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        data_lanc_layout.addWidget(lbl_data_lanc)
        data_lanc_layout.addWidget(self.input_data)
        
        # Data de Vencimento com label
        data_venc_layout = QVBoxLayout()
        data_venc_layout.setSpacing(2)
        lbl_data_venc = QLabel("Vencimento")
        lbl_data_venc.setStyleSheet("font-size: 9px; color: #ffa502;")
        self.input_data_vencimento = QDateEdit()
        self.input_data_vencimento.setDate(QDate.currentDate())
        self.input_data_vencimento.setCalendarPopup(True)
        self.input_data_vencimento.setSpecialValueText("Sem vencimento")
        self.input_data_vencimento.setMinimumDate(QDate(2000, 1, 1))
        self.input_data_vencimento.clearMinimumDate()
        data_venc_layout.addWidget(lbl_data_venc)
        data_venc_layout.addWidget(self.input_data_vencimento)
        
        # Data de Pagamento com label
        data_pag_layout = QVBoxLayout()
        data_pag_layout.setSpacing(2)
        lbl_data_pag = QLabel("Pagamento")
        lbl_data_pag.setStyleSheet("font-size: 9px; color: #3742fa;")
        self.input_data_pagamento = QDateEdit()
        self.input_data_pagamento.setCalendarPopup(True)
        self.input_data_pagamento.setSpecialValueText("Não pago")
        self.input_data_pagamento.setMinimumDate(QDate(2000, 1, 1))
        self.input_data_pagamento.clearMinimumDate()
        self.input_data_pagamento.clear()
        self.input_data_pagamento.dateChanged.connect(self.on_data_pagamento_changed)
        data_pag_layout.addWidget(lbl_data_pag)
        data_pag_layout.addWidget(self.input_data_pagamento)

        self.combo_categoria = QComboBox()
        self.combo_categoria.setPlaceholderText("Categoria")
        self.combo_categoria.setMinimumWidth(130)

        self.combo_banco = QComboBox()
        self.combo_banco.setPlaceholderText("Pagar com...")
        self.combo_banco.setMinimumWidth(130)

        self.btn_add = QPushButton("Adicionar")
        self.btn_add.setStyleSheet("background-color: #ff0055; color: white;")
        self.btn_add.clicked.connect(self.salvar_despesa)

        form.addWidget(self.input_desc)
        form.addWidget(self.input_valor)
        form.addLayout(data_lanc_layout)
        form.addLayout(data_venc_layout)
        form.addLayout(data_pag_layout)
        form.addWidget(self.combo_categoria)
        form.addWidget(self.combo_banco)
        form.addWidget(self.btn_add)

        layout.addLayout(form)

        # =============================
        # NOVOS BOTÕES: PARCELADAS E RECORRENTES
        # =============================
        btns_novos = QHBoxLayout()
        btns_novos.setSpacing(15)

        self.btn_nova_parcelada = QPushButton("💳 Nova Despesa Parcelada")
        self.btn_nova_parcelada.setStyleSheet("background-color: #5f27cd; color: white;")
        self.btn_nova_parcelada.clicked.connect(self.abrir_dialog_parcelada)

        self.btn_gerenciar_recorrentes = QPushButton("🔄 Gerenciar Recorrentes")
        self.btn_gerenciar_recorrentes.setStyleSheet("background-color: #00d2d3; color: white;")
        self.btn_gerenciar_recorrentes.clicked.connect(self.abrir_dialog_recorrente)

        # Checkbox para filtrar apenas parceladas
        self.check_filtro_parceladas = QCheckBox("Mostrar apenas parceladas")
        self.check_filtro_parceladas.setStyleSheet("color: #a4b0be;")
        self.check_filtro_parceladas.toggled.connect(self.aplicar_filtro_parceladas)
        
        # ComboBox para filtrar por status de pagamento
        self.combo_filtro_pagamento = QComboBox()
        self.combo_filtro_pagamento.addItems(["Todas", "Pagas", "Não Pagas"])
        self.combo_filtro_pagamento.setStyleSheet("background-color: #1a1a1a; color: white;")
        self.combo_filtro_pagamento.currentTextChanged.connect(self.aplicar_filtro_pagamento)
        
        # ComboBox para filtrar por vencimento
        self.combo_filtro_vencimento = QComboBox()
        self.combo_filtro_vencimento.addItems(["Todas", "Vencidas", "Vencendo em 7 dias", "Vencendo em 30 dias", "Vencendo este mês", "Sem vencimento"])
        self.combo_filtro_vencimento.setStyleSheet("background-color: #1a1a1a; color: white;")
        self.combo_filtro_vencimento.currentTextChanged.connect(self.aplicar_filtro_vencimento)

        btns_novos.addWidget(self.btn_nova_parcelada)
        btns_novos.addWidget(self.btn_gerenciar_recorrentes)
        btns_novos.addStretch()
        btns_novos.addWidget(QLabel("Vencimento:"))
        btns_novos.addWidget(self.combo_filtro_vencimento)
        btns_novos.addWidget(QLabel("Status:"))
        btns_novos.addWidget(self.combo_filtro_pagamento)
        btns_novos.addWidget(self.check_filtro_parceladas)

        layout.addLayout(btns_novos)

        # =============================
        # TABELA (ADICIONADA COLUNA BANCO, TIPO, PAGO, DATA VENCIMENTO E DATA PAGAMENTO)
        # =============================
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(10) # Aumentado para incluir data_vencimento e data_pagamento
        self.tabela.setHorizontalHeaderLabels(["ID", "DESCRIÇÃO", "VALOR", "DATA", "VENCIMENTO", "PAGAMENTO", "CATEGORIA", "BANCO", "TIPO", "PAGO"])
        self.tabela.setColumnHidden(0, True)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.cellDoubleClicked.connect(self.on_double_click)  # Duplo clique para alternar pago

        layout.addWidget(self.tabela)

        # =============================
        # BOTÕES DE AÇÃO
        # =============================
        btns = QHBoxLayout()
        btns.setSpacing(15)

        btn_marcar_pago = QPushButton("✅ Marcar como Pago")
        btn_marcar_pago.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        btn_marcar_pago.clicked.connect(self.marcar_selecionada_como_paga)

        btn_marcar_nao_pago = QPushButton("⏳ Marcar como Não Pago")
        btn_marcar_nao_pago.setStyleSheet("""
            QPushButton { background-color: #f39c12; color: white; }
            QPushButton:hover { background-color: #e67e22; }
        """)
        btn_marcar_nao_pago.clicked.connect(self.marcar_selecionada_como_nao_paga)

        btn_editar = QPushButton("📝 Editar Selecionada")
        btn_excluir = QPushButton("🗑️ Excluir Selecionada")
        btn_excluir.setStyleSheet("""
            QPushButton { border: 1px solid #ff4757; color: #ff4757; }
            QPushButton:hover { background-color: #ff4757; color: white; }
        """)

        btn_editar.clicked.connect(self.editar_despesa)
        btn_excluir.clicked.connect(self.excluir_despesa)

        btns.addStretch()
        btns.addWidget(btn_marcar_pago)
        btns.addWidget(btn_marcar_nao_pago)
        btns.addWidget(btn_editar)
        btns.addWidget(btn_excluir)

        layout.addLayout(btns)

        # ---------- PAGINAÇÃO ----------
        pag = QHBoxLayout()
        self.btn_anterior = QPushButton("◀ Anterior")
        self.btn_anterior.clicked.connect(self.pagina_anterior)
        self.lbl_pagina = QLabel("Página 1")
        self.lbl_pagina.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pagina.setStyleSheet("color: #a4b0be;")
        self.btn_proxima = QPushButton("Próxima ▶")
        self.btn_proxima.clicked.connect(self.proxima_pagina)
        pag.addStretch()
        pag.addWidget(self.btn_anterior)
        pag.addWidget(self.lbl_pagina)
        pag.addWidget(self.btn_proxima)
        pag.addStretch()
        layout.addLayout(pag)

        self.atualizar()

    def atualizar(self):
        self.carregar_categorias()
        self.carregar_bancos() # Novo carregamento
        self.carregar_despesas()

    def carregar_categorias(self):
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

    def carregar_bancos(self):
        """Carrega a lista de bancos cadastrados no sistema."""
        self.combo_banco.clear()
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM bancos ORDER BY nome")
            for b_id, nome in cur.fetchall():
                self.combo_banco.addItem(nome, b_id)
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar bancos: {e}")

    def salvar_despesa(self):
        desc = self.input_desc.text().strip()
        valor_txt = self.input_valor.text().replace(",", ".")
        data = self.input_data.date().toString("yyyy-MM-dd")
        cat_id = self.combo_categoria.currentData()
        banco_id = self.combo_banco.currentData()
        
        # Obter datas de vencimento e pagamento
        data_vencimento = None
        if self.input_data_vencimento.date() != self.input_data_vencimento.minimumDate():
            data_vencimento = self.input_data_vencimento.date().toString("yyyy-MM-dd")
        
        data_pagamento = None
        if self.input_data_pagamento.date() != self.input_data_pagamento.minimumDate():
            data_pagamento = self.input_data_pagamento.date().toString("yyyy-MM-dd")

        if not desc or not valor_txt or cat_id is None or banco_id is None:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos, incluindo o Banco.")
            return

        # Validate-Then-Execute: Validar com Pydantic antes de operações de banco
        try:
            # Converter valor para Decimal
            valor = Decimal(valor_txt)
            
            # Validar com DespesaModel
            despesa_validada = DespesaModel(
                descricao=desc,
                valor=valor,
                data=data,
                categoria_id=cat_id,
                banco_id=banco_id
            )
            
            # Determinar pago baseado em data_pagamento
            pago = 1 if data_pagamento else 0
            
            # Se validação passou, prosseguir com operação de banco
            conn = conectar()
            cur = conn.cursor()

            if self.despesa_id is None:
                cur.execute("""
                    INSERT INTO despesas (descricao, valor, data, categoria_id, banco_id, pago, data_vencimento, data_pagamento) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (despesa_validada.descricao, float(despesa_validada.valor), 
                      despesa_validada.data, despesa_validada.categoria_id, despesa_validada.banco_id,
                      pago, data_vencimento, data_pagamento))
            else:
                cur.execute("""
                    UPDATE despesas SET descricao=?, valor=?, data=?, categoria_id=?, banco_id=?, 
                    pago=?, data_vencimento=?, data_pagamento=?
                    WHERE id=?
                """, (despesa_validada.descricao, float(despesa_validada.valor), 
                      despesa_validada.data, despesa_validada.categoria_id, despesa_validada.banco_id,
                      pago, data_vencimento, data_pagamento, self.despesa_id))
                self.despesa_id = None
                self.btn_add.setText("Adicionar")
                self.btn_add.setStyleSheet("background-color: #ff0055; color: white;")

            conn.commit()
            conn.close()

            self.input_desc.clear()
            self.input_valor.clear()
            self.input_data_pagamento.clear()
            self.input_data_vencimento.setDate(QDate.currentDate())
            self.atualizar()
            self.dados_atualizados.emit()
            
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
                    'data': 'Data',
                    'categoria_id': 'Categoria',
                    'banco_id': 'Banco'
                }.get(campo, campo)
                
                erros.append(f"• {campo_pt}: {mensagem}")
            
            QMessageBox.warning(self, "Erro de Validação", "\n".join(erros))
            
        except (ValueError, Exception) as e:
            QMessageBox.warning(self, "Erro", f"Valor numérico inválido: {str(e)}")

    def carregar_despesas(self):
        self.tabela.setRowCount(0)
        try:
            conn = conectar()
            cur = conn.cursor()
            
            # Construir query base com filtros
            where_clauses = []
            params = []
            
            # Filtro de parceladas
            if self.filtro_parceladas:
                where_clauses.append("d.despesa_parcelada_id IS NOT NULL")
            
            # Filtro de pagamento
            if self.filtro_pagamento == 'pagas':
                where_clauses.append("d.pago = 1")
            elif self.filtro_pagamento == 'nao_pagas':
                where_clauses.append("d.pago = 0")
            
            # Filtro de vencimento
            from datetime import date, timedelta
            from calendar import monthrange
            hoje = date.today()
            
            if self.filtro_vencimento == 'vencidas':
                where_clauses.append("d.data_vencimento < ? AND d.pago = 0")
                params.append(hoje.strftime('%Y-%m-%d'))
            elif self.filtro_vencimento == 'vencendo_7d':
                data_limite = (hoje + timedelta(days=7)).strftime('%Y-%m-%d')
                where_clauses.append("d.data_vencimento >= ? AND d.data_vencimento <= ? AND d.pago = 0")
                params.extend([hoje.strftime('%Y-%m-%d'), data_limite])
            elif self.filtro_vencimento == 'vencendo_30d':
                data_limite = (hoje + timedelta(days=30)).strftime('%Y-%m-%d')
                where_clauses.append("d.data_vencimento >= ? AND d.data_vencimento <= ? AND d.pago = 0")
                params.extend([hoje.strftime('%Y-%m-%d'), data_limite])
            elif self.filtro_vencimento == 'vencendo_mes':
                primeiro_dia = date(hoje.year, hoje.month, 1).strftime('%Y-%m-%d')
                ultimo_dia_num = monthrange(hoje.year, hoje.month)[1]
                ultimo_dia = date(hoje.year, hoje.month, ultimo_dia_num).strftime('%Y-%m-%d')
                where_clauses.append("d.data_vencimento >= ? AND d.data_vencimento <= ? AND d.pago = 0")
                params.extend([primeiro_dia, ultimo_dia])
            elif self.filtro_vencimento == 'sem_vencimento':
                where_clauses.append("d.data_vencimento IS NULL")
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Contar total de registros
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM despesas d 
                JOIN categorias c ON d.categoria_id = c.id
                WHERE {where_sql}
            """, params)
            
            total = cur.fetchone()[0]
            total_paginas = max(1, (total + self.itens_por_pagina - 1) // self.itens_por_pagina)
            self.pagina_atual = max(0, min(self.pagina_atual, total_paginas - 1))
            offset = self.pagina_atual * self.itens_por_pagina
            self.lbl_pagina.setText(f"Página {self.pagina_atual + 1} de {total_paginas}")
            self.btn_anterior.setEnabled(self.pagina_atual > 0)
            self.btn_proxima.setEnabled(self.pagina_atual < total_paginas - 1)
            
            # Query principal com filtros
            cur.execute(f"""
                SELECT 
                    d.id, 
                    d.descricao, 
                    d.valor, 
                    d.data,
                    d.data_vencimento,
                    d.data_pagamento,
                    c.nome,
                    b.nome,
                    d.parcela_numero,
                    d.parcela_total,
                    d.despesa_parcelada_id,
                    d.despesa_recorrente_id,
                    d.cartao_id,
                    d.mes_fatura,
                    d.pago
                FROM despesas d
                JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN bancos b ON d.banco_id = b.id
                LEFT JOIN despesas_parceladas dp ON d.despesa_parcelada_id = dp.id
                LEFT JOIN despesas_recorrentes dr ON d.despesa_recorrente_id = dr.id
                WHERE {where_sql}
                ORDER BY d.data DESC
                LIMIT ? OFFSET ?
            """, params + [self.itens_por_pagina, offset])
            
            for row_data in cur.fetchall():
                row = self.tabela.rowCount()
                self.tabela.insertRow(row)
                
                # Extrair dados
                despesa_id, descricao, valor, data, data_vencimento, data_pagamento, categoria, banco, \
                parcela_numero, parcela_total, despesa_parcelada_id, despesa_recorrente_id, \
                cartao_id, mes_fatura, pago = row_data
                
                # Converter datas para formato brasileiro
                from database.db import converter_data_iso_para_br
                data_venc_br = converter_data_iso_para_br(data_vencimento) if data_vencimento else ""
                data_pag_br = converter_data_iso_para_br(data_pagamento) if data_pagamento else ""
                
                # Determinar tipo da despesa
                if cartao_id and mes_fatura:
                    tipo = "Fatura Cartão"
                    tipo_icon = "💳 "
                elif despesa_parcelada_id:
                    tipo = f"Parcelada ({parcela_numero}/{parcela_total})"
                    tipo_icon = "💳 "
                elif despesa_recorrente_id:
                    tipo = "Recorrente"
                    tipo_icon = "🔄 "
                else:
                    tipo = "Normal"
                    tipo_icon = ""
                
                # Preencher colunas
                colunas = [
                    str(despesa_id),
                    descricao,
                    f"R$ {valor:.2f}",
                    data,
                    data_venc_br,
                    data_pag_br,
                    categoria,
                    banco if banco else "Não definido",
                    tipo_icon + tipo
                ]
                
                for col, item in enumerate(colunas):
                    tab_item = QTableWidgetItem(item)
                    if col == 2:  # Valor
                        tab_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    elif col in [4, 5]:  # Datas de vencimento e pagamento
                        tab_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    elif col == 8:  # Tipo
                        tab_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        # Colorir baseado no tipo
                        if cartao_id and mes_fatura:
                            tab_item.setForeground(Qt.GlobalColor.magenta)
                        elif despesa_parcelada_id:
                            tab_item.setForeground(Qt.GlobalColor.cyan)
                        elif despesa_recorrente_id:
                            tab_item.setForeground(Qt.GlobalColor.green)
                    
                    # Aplicar destaque visual para despesas vencidas
                    if col == 4 and data_vencimento and not pago:  # Coluna vencimento
                        from datetime import date
                        hoje = date.today().strftime('%Y-%m-%d')
                        if data_vencimento < hoje:
                            tab_item.setBackground(QColor(255, 0, 0, 50))  # Vermelho para vencidas
                            tab_item.setForeground(Qt.GlobalColor.red)
                        elif data_vencimento == hoje:
                            tab_item.setBackground(QColor(255, 255, 0, 50))  # Amarelo para vencendo hoje
                            tab_item.setForeground(Qt.GlobalColor.yellow)
                    
                    # Aplicar cor verde se pago
                    if pago:
                        tab_item.setBackground(QColor(0, 100, 0, 50))  # Verde transparente
                    
                    self.tabela.setItem(row, col, tab_item)
                
                # Adicionar texto na coluna PAGO (col 9) - sem checkbox
                pago_text = "✅ PAGO" if pago else "⏳ PENDENTE"
                pago_item = QTableWidgetItem(pago_text)
                pago_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if pago:
                    pago_item.setForeground(Qt.GlobalColor.green)
                    pago_item.setBackground(QColor(0, 100, 0, 50))
                else:
                    pago_item.setForeground(Qt.GlobalColor.yellow)
                self.tabela.setItem(row, 9, pago_item)
            
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar despesas: {e}")

    def pagina_anterior(self):
        if self.pagina_atual > 0:
            self.pagina_atual -= 1
            self.carregar_despesas()

    def proxima_pagina(self):
        self.pagina_atual += 1
        self.carregar_despesas()

    def editar_despesa(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione uma despesa para editar.")
            return

        self.despesa_id = int(self.tabela.item(linha, 0).text())
        self.input_desc.setText(self.tabela.item(linha, 1).text())
        
        valor_limpo = self.tabela.item(linha, 2).text().replace("R$ ", "")
        self.input_valor.setText(valor_limpo)

        # Recuperar Categoria
        categoria_nome = self.tabela.item(linha, 4).text()
        index_cat = self.combo_categoria.findText(categoria_nome)
        if index_cat >= 0:
            self.combo_categoria.setCurrentIndex(index_cat)

        # Recuperar Banco
        banco_nome = self.tabela.item(linha, 5).text()
        index_banco = self.combo_banco.findText(banco_nome)
        if index_banco >= 0:
            self.combo_banco.setCurrentIndex(index_banco)

        self.btn_add.setText("Salvar Alteração")
        self.btn_add.setStyleSheet("background-color: #3742fa; color: white;")

    def excluir_despesa(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            return

        despesa_id = int(self.tabela.item(linha, 0).text())
        resp = QMessageBox.question(self, "Confirmar", "Deseja realmente excluir esta despesa?")

        if resp == QMessageBox.StandardButton.Yes:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM despesas WHERE id=?", (despesa_id,))
            conn.commit()
            conn.close()

            self.atualizar()
            self.dados_atualizados.emit()

    def abrir_dialog_parcelada(self):
        """Abre o dialog para criar nova despesa parcelada."""
        dialog = DialogDespesaParcelada(self)
        dialog.dados_atualizados.connect(self.atualizar)
        dialog.dados_atualizados.connect(self.dados_atualizados.emit)
        dialog.exec()

    def abrir_dialog_recorrente(self):
        """Abre o dialog para gerenciar despesas recorrentes."""
        dialog = DialogDespesaRecorrente(self)
        dialog.dados_atualizados.connect(self.atualizar)
        dialog.dados_atualizados.connect(self.dados_atualizados.emit)
        dialog.exec()

    def aplicar_filtro_parceladas(self, checked):
        """Aplica ou remove o filtro de despesas parceladas."""
        self.filtro_parceladas = checked
        self.pagina_atual = 0  # Resetar para primeira página
        self.carregar_despesas()
    
    def aplicar_filtro_pagamento(self, texto):
        """Aplica filtro de status de pagamento."""
        if texto == "Todas":
            self.filtro_pagamento = 'todas'
        elif texto == "Pagas":
            self.filtro_pagamento = 'pagas'
        elif texto == "Não Pagas":
            self.filtro_pagamento = 'nao_pagas'
        
        self.pagina_atual = 0  # Resetar para primeira página
        self.carregar_despesas()
    
    def on_double_click(self, row, col):
        """Alterna o status de pago ao dar duplo clique na linha."""
        despesa_id = int(self.tabela.item(row, 0).text())
        
        # Verificar status atual
        pago_item = self.tabela.item(row, 9)
        pago_atual = "✅ PAGO" in pago_item.text()
        
        # Alternar status
        self.marcar_despesa_paga(despesa_id, not pago_atual)
    
    def marcar_selecionada_como_paga(self):
        """Marca a despesa selecionada como paga."""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione uma despesa para marcar como paga.")
            return
        
        despesa_id = int(self.tabela.item(linha, 0).text())
        self.marcar_despesa_paga(despesa_id, True)
    
    def marcar_selecionada_como_nao_paga(self):
        """Marca a despesa selecionada como não paga."""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione uma despesa para marcar como não paga.")
            return
        
        despesa_id = int(self.tabela.item(linha, 0).text())
        self.marcar_despesa_paga(despesa_id, False)
    
    def marcar_despesa_paga(self, despesa_id, pago):
        """Marca uma despesa como paga ou não paga."""
        from database.db import marcar_despesa_paga
        from utils.logger import logger
        
        try:
            sucesso = marcar_despesa_paga(despesa_id, pago)
            if sucesso:
                logger.info(f"Despesa {despesa_id} marcada como {'paga' if pago else 'não paga'}")
                self.carregar_despesas()  # Recarregar para atualizar cores
                self.dados_atualizados.emit()
                
                # Feedback visual
                status_text = "paga" if pago else "não paga"
                QMessageBox.information(self, "Sucesso", f"Despesa marcada como {status_text}!")
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível atualizar o status de pagamento.")
        except Exception as e:
            logger.error(f"Erro ao marcar despesa como paga: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar status: {e}")

    def on_data_pagamento_changed(self, date):
        """
        Sincronização visual: quando data_pagamento é definida/removida.
        Requirements: 2.1, 2.2, 2.4
        """
        # Se a data é válida (não é a data mínima), considera como "pago"
        # Caso contrário, considera como "não pago"
        # Nota: A sincronização real com o banco acontece no salvar_despesa
        pass  # A lógica visual já está implementada no salvar_despesa

    def aplicar_filtro_vencimento(self, texto):
        """
        Aplica filtro de vencimento nas despesas.
        Requirements: 7.1, 7.2, 7.3, 7.5, 7.6
        """
        mapa = {
            "Todas": "todas",
            "Vencidas": "vencidas",
            "Vencendo em 7 dias": "vencendo_7d",
            "Vencendo em 30 dias": "vencendo_30d",
            "Vencendo este mês": "vencendo_mes",
            "Sem vencimento": "sem_vencimento"
        }
        self.filtro_vencimento = mapa.get(texto, "todas")
        self.pagina_atual = 0
        self.carregar_despesas()
