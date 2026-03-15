-- =============================================================================
-- Row Level Security (RLS) Policies
-- Isolamento multi-tenant: cada usuário só acessa seus próprios dados
-- Usa current_setting('app.current_user_id')::INTEGER definido pelo middleware
-- =============================================================================

-- =============================================================================
-- 1. ENABLE ROW LEVEL SECURITY em todas as tabelas com dados de usuário
-- =============================================================================

-- Tabelas com usuario_id direto
ALTER TABLE bancos ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE receitas ENABLE ROW LEVEL SECURITY;
ALTER TABLE despesas ENABLE ROW LEVEL SECURITY;
ALTER TABLE despesas_parceladas ENABLE ROW LEVEL SECURITY;
ALTER TABLE despesas_recorrentes ENABLE ROW LEVEL SECURITY;
ALTER TABLE cartoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE investimentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE transferencias ENABLE ROW LEVEL SECURITY;
ALTER TABLE veiculos ENABLE ROW LEVEL SECURITY;
ALTER TABLE orcamentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuracoes ENABLE ROW LEVEL SECURITY;

-- Tabelas filhas (sem usuario_id direto, herdam via JOIN)
ALTER TABLE compras_cartao ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagamentos_fatura ENABLE ROW LEVEL SECURITY;
ALTER TABLE dividendos ENABLE ROW LEVEL SECURITY;
ALTER TABLE abastecimentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE manutencoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE itens_orcamento ENABLE ROW LEVEL SECURITY;
ALTER TABLE historico_orcamento ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- 2. Políticas para tabelas com usuario_id direto
-- =============================================================================

-- ---- bancos ----
CREATE POLICY "bancos_select_own" ON bancos
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "bancos_insert_own" ON bancos
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "bancos_update_own" ON bancos
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "bancos_delete_own" ON bancos
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- categorias ----
CREATE POLICY "categorias_select_own" ON categorias
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "categorias_insert_own" ON categorias
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "categorias_update_own" ON categorias
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "categorias_delete_own" ON categorias
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- receitas ----
CREATE POLICY "receitas_select_own" ON receitas
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "receitas_insert_own" ON receitas
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "receitas_update_own" ON receitas
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "receitas_delete_own" ON receitas
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- despesas ----
CREATE POLICY "despesas_select_own" ON despesas
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "despesas_insert_own" ON despesas
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "despesas_update_own" ON despesas
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "despesas_delete_own" ON despesas
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- despesas_parceladas ----
CREATE POLICY "despesas_parceladas_select_own" ON despesas_parceladas
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "despesas_parceladas_insert_own" ON despesas_parceladas
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "despesas_parceladas_update_own" ON despesas_parceladas
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "despesas_parceladas_delete_own" ON despesas_parceladas
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- despesas_recorrentes ----
CREATE POLICY "despesas_recorrentes_select_own" ON despesas_recorrentes
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "despesas_recorrentes_insert_own" ON despesas_recorrentes
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "despesas_recorrentes_update_own" ON despesas_recorrentes
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "despesas_recorrentes_delete_own" ON despesas_recorrentes
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- cartoes ----
CREATE POLICY "cartoes_select_own" ON cartoes
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "cartoes_insert_own" ON cartoes
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "cartoes_update_own" ON cartoes
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "cartoes_delete_own" ON cartoes
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- investimentos ----
CREATE POLICY "investimentos_select_own" ON investimentos
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "investimentos_insert_own" ON investimentos
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "investimentos_update_own" ON investimentos
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "investimentos_delete_own" ON investimentos
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- transferencias ----
CREATE POLICY "transferencias_select_own" ON transferencias
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "transferencias_insert_own" ON transferencias
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "transferencias_update_own" ON transferencias
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "transferencias_delete_own" ON transferencias
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- veiculos ----
CREATE POLICY "veiculos_select_own" ON veiculos
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "veiculos_insert_own" ON veiculos
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "veiculos_update_own" ON veiculos
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "veiculos_delete_own" ON veiculos
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- orcamentos ----
CREATE POLICY "orcamentos_select_own" ON orcamentos
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "orcamentos_insert_own" ON orcamentos
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "orcamentos_update_own" ON orcamentos
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "orcamentos_delete_own" ON orcamentos
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- ---- configuracoes ----
CREATE POLICY "configuracoes_select_own" ON configuracoes
    FOR SELECT USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "configuracoes_insert_own" ON configuracoes
    FOR INSERT WITH CHECK (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "configuracoes_update_own" ON configuracoes
    FOR UPDATE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "configuracoes_delete_own" ON configuracoes
    FOR DELETE USING (usuario_id = current_setting('app.current_user_id')::INTEGER);

-- =============================================================================
-- 3. Políticas para tabelas filhas (sem usuario_id direto, via JOIN com pai)
-- =============================================================================

-- ---- compras_cartao (via cartoes.usuario_id) ----
CREATE POLICY "compras_cartao_select_own" ON compras_cartao
    FOR SELECT USING (
        cartao_id IN (SELECT id FROM cartoes WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "compras_cartao_insert_own" ON compras_cartao
    FOR INSERT WITH CHECK (
        cartao_id IN (SELECT id FROM cartoes WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "compras_cartao_update_own" ON compras_cartao
    FOR UPDATE USING (
        cartao_id IN (SELECT id FROM cartoes WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "compras_cartao_delete_own" ON compras_cartao
    FOR DELETE USING (
        cartao_id IN (SELECT id FROM cartoes WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );

-- ---- pagamentos_fatura (via cartoes.usuario_id) ----
CREATE POLICY "pagamentos_fatura_select_own" ON pagamentos_fatura
    FOR SELECT USING (
        cartao_id IN (SELECT id FROM cartoes WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "pagamentos_fatura_insert_own" ON pagamentos_fatura
    FOR INSERT WITH CHECK (
        cartao_id IN (SELECT id FROM cartoes WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "pagamentos_fatura_update_own" ON pagamentos_fatura
    FOR UPDATE USING (
        cartao_id IN (SELECT id FROM cartoes WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "pagamentos_fatura_delete_own" ON pagamentos_fatura
    FOR DELETE USING (
        cartao_id IN (SELECT id FROM cartoes WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );

-- ---- dividendos (via investimentos.usuario_id) ----
CREATE POLICY "dividendos_select_own" ON dividendos
    FOR SELECT USING (
        investimento_id IN (SELECT id FROM investimentos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "dividendos_insert_own" ON dividendos
    FOR INSERT WITH CHECK (
        investimento_id IN (SELECT id FROM investimentos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "dividendos_update_own" ON dividendos
    FOR UPDATE USING (
        investimento_id IN (SELECT id FROM investimentos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "dividendos_delete_own" ON dividendos
    FOR DELETE USING (
        investimento_id IN (SELECT id FROM investimentos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );

-- ---- abastecimentos (via veiculos.usuario_id) ----
CREATE POLICY "abastecimentos_select_own" ON abastecimentos
    FOR SELECT USING (
        veiculo_id IN (SELECT id FROM veiculos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "abastecimentos_insert_own" ON abastecimentos
    FOR INSERT WITH CHECK (
        veiculo_id IN (SELECT id FROM veiculos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "abastecimentos_update_own" ON abastecimentos
    FOR UPDATE USING (
        veiculo_id IN (SELECT id FROM veiculos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "abastecimentos_delete_own" ON abastecimentos
    FOR DELETE USING (
        veiculo_id IN (SELECT id FROM veiculos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );

-- ---- manutencoes (via veiculos.usuario_id) ----
CREATE POLICY "manutencoes_select_own" ON manutencoes
    FOR SELECT USING (
        veiculo_id IN (SELECT id FROM veiculos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "manutencoes_insert_own" ON manutencoes
    FOR INSERT WITH CHECK (
        veiculo_id IN (SELECT id FROM veiculos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "manutencoes_update_own" ON manutencoes
    FOR UPDATE USING (
        veiculo_id IN (SELECT id FROM veiculos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "manutencoes_delete_own" ON manutencoes
    FOR DELETE USING (
        veiculo_id IN (SELECT id FROM veiculos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );

-- ---- itens_orcamento (via orcamentos.usuario_id) ----
CREATE POLICY "itens_orcamento_select_own" ON itens_orcamento
    FOR SELECT USING (
        orcamento_id IN (SELECT id FROM orcamentos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "itens_orcamento_insert_own" ON itens_orcamento
    FOR INSERT WITH CHECK (
        orcamento_id IN (SELECT id FROM orcamentos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "itens_orcamento_update_own" ON itens_orcamento
    FOR UPDATE USING (
        orcamento_id IN (SELECT id FROM orcamentos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );
CREATE POLICY "itens_orcamento_delete_own" ON itens_orcamento
    FOR DELETE USING (
        orcamento_id IN (SELECT id FROM orcamentos WHERE usuario_id = current_setting('app.current_user_id')::INTEGER)
    );

-- ---- historico_orcamento (via itens_orcamento → orcamentos.usuario_id) ----
CREATE POLICY "historico_orcamento_select_own" ON historico_orcamento
    FOR SELECT USING (
        item_orcamento_id IN (
            SELECT io.id FROM itens_orcamento io
            JOIN orcamentos o ON io.orcamento_id = o.id
            WHERE o.usuario_id = current_setting('app.current_user_id')::INTEGER
        )
    );
CREATE POLICY "historico_orcamento_insert_own" ON historico_orcamento
    FOR INSERT WITH CHECK (
        item_orcamento_id IN (
            SELECT io.id FROM itens_orcamento io
            JOIN orcamentos o ON io.orcamento_id = o.id
            WHERE o.usuario_id = current_setting('app.current_user_id')::INTEGER
        )
    );
CREATE POLICY "historico_orcamento_update_own" ON historico_orcamento
    FOR UPDATE USING (
        item_orcamento_id IN (
            SELECT io.id FROM itens_orcamento io
            JOIN orcamentos o ON io.orcamento_id = o.id
            WHERE o.usuario_id = current_setting('app.current_user_id')::INTEGER
        )
    );
CREATE POLICY "historico_orcamento_delete_own" ON historico_orcamento
    FOR DELETE USING (
        item_orcamento_id IN (
            SELECT io.id FROM itens_orcamento io
            JOIN orcamentos o ON io.orcamento_id = o.id
            WHERE o.usuario_id = current_setting('app.current_user_id')::INTEGER
        )
    );
