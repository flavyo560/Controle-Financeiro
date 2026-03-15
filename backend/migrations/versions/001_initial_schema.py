"""Initial schema — all 20 tables and performance indexes.

Revision ID: 001
Revises: None
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── usuarios ──────────────────────────────────────────────────────
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=True),
        sa.Column("senha_hash_bcrypt", sa.String(255), nullable=True),
        sa.Column("cpf", sa.String(14), nullable=True),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("perfil", sa.String(50), server_default="admin", nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # ── bancos ────────────────────────────────────────────────────────
    op.create_table(
        "bancos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("saldo_inicial", sa.Numeric(15, 2), server_default="0", nullable=True),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "nome", name="uq_bancos_usuario_nome"),
    )

    # ── categorias ────────────────────────────────────────────────────
    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint("tipo IN ('receita', 'despesa')", name="ck_categorias_tipo"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── despesas_parceladas ───────────────────────────────────────────
    op.create_table(
        "despesas_parceladas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("valor_total", sa.Numeric(15, 2), nullable=False),
        sa.Column("numero_parcelas", sa.Integer(), nullable=False),
        sa.Column("data_primeira_parcela", sa.Date(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("banco_id", sa.Integer(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "numero_parcelas > 1 AND numero_parcelas <= 120",
            name="ck_despesas_parceladas_numero_parcelas",
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias.id"]),
        sa.ForeignKeyConstraint(["banco_id"], ["bancos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── despesas_recorrentes ──────────────────────────────────────────
    op.create_table(
        "despesas_recorrentes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("dia_mes", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("banco_id", sa.Integer(), nullable=True),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("ativa", sa.Boolean(), server_default="true", nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("dia_mes >= 1 AND dia_mes <= 31", name="ck_despesas_recorrentes_dia_mes"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias.id"]),
        sa.ForeignKeyConstraint(["banco_id"], ["bancos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── cartoes ───────────────────────────────────────────────────────
    op.create_table(
        "cartoes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("bandeira", sa.String(50), nullable=True),
        sa.Column("limite_total", sa.Numeric(15, 2), nullable=False),
        sa.Column("dia_fechamento", sa.Integer(), nullable=False),
        sa.Column("dia_vencimento", sa.Integer(), nullable=False),
        sa.Column("status", sa.Boolean(), server_default="true", nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("limite_total > 0", name="ck_cartoes_limite_total"),
        sa.CheckConstraint("dia_fechamento >= 1 AND dia_fechamento <= 31", name="ck_cartoes_dia_fechamento"),
        sa.CheckConstraint("dia_vencimento >= 1 AND dia_vencimento <= 31", name="ck_cartoes_dia_vencimento"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "nome", name="uq_cartoes_usuario_nome"),
    )

    # ── receitas ──────────────────────────────────────────────────────
    op.create_table(
        "receitas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("banco_id", sa.Integer(), nullable=True),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias.id"]),
        sa.ForeignKeyConstraint(["banco_id"], ["bancos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── despesas ──────────────────────────────────────────────────────
    op.create_table(
        "despesas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("banco_id", sa.Integer(), nullable=True),
        sa.Column("pago", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("data_vencimento", sa.Date(), nullable=True),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.Column("parcela_numero", sa.Integer(), nullable=True),
        sa.Column("parcela_total", sa.Integer(), nullable=True),
        sa.Column("despesa_parcelada_id", sa.Integer(), nullable=True),
        sa.Column("despesa_recorrente_id", sa.Integer(), nullable=True),
        sa.Column("cartao_id", sa.Integer(), nullable=True),
        sa.Column("mes_fatura", sa.String(7), nullable=True),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias.id"]),
        sa.ForeignKeyConstraint(["banco_id"], ["bancos.id"]),
        sa.ForeignKeyConstraint(["despesa_parcelada_id"], ["despesas_parceladas.id"]),
        sa.ForeignKeyConstraint(["despesa_recorrente_id"], ["despesas_recorrentes.id"]),
        sa.ForeignKeyConstraint(["cartao_id"], ["cartoes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── compras_cartao ────────────────────────────────────────────────
    op.create_table(
        "compras_cartao",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cartao_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("data_compra", sa.Date(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("mes_fatura", sa.String(7), nullable=False),
        sa.Column("parcela_atual", sa.Integer(), nullable=True),
        sa.Column("total_parcelas", sa.Integer(), nullable=True),
        sa.Column("compra_parcelada_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("valor > 0", name="ck_compras_cartao_valor"),
        sa.CheckConstraint(
            "parcela_atual IS NULL OR parcela_atual > 0",
            name="ck_compras_cartao_parcela_atual",
        ),
        sa.CheckConstraint(
            "total_parcelas IS NULL OR total_parcelas >= 1",
            name="ck_compras_cartao_total_parcelas",
        ),
        sa.ForeignKeyConstraint(["cartao_id"], ["cartoes.id"]),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── pagamentos_fatura ─────────────────────────────────────────────
    op.create_table(
        "pagamentos_fatura",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cartao_id", sa.Integer(), nullable=False),
        sa.Column("mes_fatura", sa.String(7), nullable=False),
        sa.Column("valor_pago", sa.Numeric(15, 2), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=False),
        sa.Column("banco_id", sa.Integer(), nullable=False),
        sa.Column("despesa_id", sa.Integer(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("valor_pago > 0", name="ck_pagamentos_fatura_valor_pago"),
        sa.ForeignKeyConstraint(["cartao_id"], ["cartoes.id"]),
        sa.ForeignKeyConstraint(["banco_id"], ["bancos.id"]),
        sa.ForeignKeyConstraint(["despesa_id"], ["despesas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── investimentos ─────────────────────────────────────────────────
    op.create_table(
        "investimentos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(100), nullable=True),
        sa.Column("valor_investido", sa.Numeric(15, 2), nullable=False),
        sa.Column("valor_atual", sa.Numeric(15, 2), nullable=True),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("banco_id", sa.Integer(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias.id"]),
        sa.ForeignKeyConstraint(["banco_id"], ["bancos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── dividendos ────────────────────────────────────────────────────
    op.create_table(
        "dividendos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("investimento_id", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["investimento_id"], ["investimentos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── transferencias ────────────────────────────────────────────────
    op.create_table(
        "transferencias",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("banco_origem_id", sa.Integer(), nullable=True),
        sa.Column("banco_destino_id", sa.Integer(), nullable=True),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["banco_origem_id"], ["bancos.id"]),
        sa.ForeignKeyConstraint(["banco_destino_id"], ["bancos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── veiculos ──────────────────────────────────────────────────────
    op.create_table(
        "veiculos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome_identificador", sa.String(255), nullable=False),
        sa.Column("placa", sa.String(10), nullable=True),
        sa.Column("modelo", sa.String(255), nullable=True),
        sa.Column("status", sa.Boolean(), server_default="true", nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── abastecimentos ────────────────────────────────────────────────
    op.create_table(
        "abastecimentos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("veiculo_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("litros", sa.Numeric(10, 2), nullable=True),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("km", sa.Numeric(10, 1), nullable=True),
        sa.Column("posto", sa.String(255), nullable=True),
        sa.Column("tipo", sa.String(50), nullable=True),
        sa.Column("litros_gasolina", sa.Numeric(10, 2), nullable=True),
        sa.Column("litros_etanol", sa.Numeric(10, 2), nullable=True),
        sa.ForeignKeyConstraint(["veiculo_id"], ["veiculos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── manutencoes ───────────────────────────────────────────────────
    op.create_table(
        "manutencoes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("veiculo_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("servico", sa.Text(), nullable=True),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("km", sa.Numeric(10, 1), nullable=True),
        sa.ForeignKeyConstraint(["veiculo_id"], ["veiculos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── orcamentos ────────────────────────────────────────────────────
    op.create_table(
        "orcamentos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="ativo"),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("ano >= 2000 AND ano <= 2100", name="ck_orcamentos_ano"),
        sa.CheckConstraint("status IN ('ativo', 'inativo')", name="ck_orcamentos_status"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "ano", name="uq_orcamentos_usuario_ano"),
    )

    # ── itens_orcamento ───────────────────────────────────────────────
    op.create_table(
        "itens_orcamento",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("orcamento_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("valor_planejado", sa.Numeric(15, 2), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("mes >= 1 AND mes <= 12", name="ck_itens_orcamento_mes"),
        sa.CheckConstraint("valor_planejado >= 0", name="ck_itens_orcamento_valor_planejado"),
        sa.ForeignKeyConstraint(["orcamento_id"], ["orcamentos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("orcamento_id", "categoria_id", "mes", name="uq_itens_orcamento_composto"),
    )

    # ── historico_orcamento ────────────────────────────────────────────
    op.create_table(
        "historico_orcamento",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_orcamento_id", sa.Integer(), nullable=False),
        sa.Column(
            "data_alteracao",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("valor_anterior", sa.Numeric(15, 2), nullable=False),
        sa.Column("valor_novo", sa.Numeric(15, 2), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["item_orcamento_id"], ["itens_orcamento.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── configuracoes ─────────────────────────────────────────────────
    op.create_table(
        "configuracoes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("chave", sa.String(255), nullable=False),
        sa.Column("valor", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "chave", name="uq_configuracoes_usuario_chave"),
    )

    # ══════════════════════════════════════════════════════════════════
    # Performance indexes
    # ══════════════════════════════════════════════════════════════════

    # -- Despesas indexes --
    op.create_index("idx_despesas_data", "despesas", ["data"])
    op.create_index("idx_despesas_categoria", "despesas", ["categoria_id"])
    op.create_index("idx_despesas_banco", "despesas", ["banco_id"])
    op.create_index("idx_despesas_pago", "despesas", ["pago"])
    op.create_index("idx_despesas_vencimento", "despesas", ["data_vencimento"])
    op.create_index("idx_despesas_parcelada_id", "despesas", ["despesa_parcelada_id"])
    op.create_index("idx_despesas_recorrente_id", "despesas", ["despesa_recorrente_id"])
    op.create_index("idx_despesas_cartao_fatura", "despesas", ["cartao_id", "mes_fatura"])

    # -- Receitas indexes --
    op.create_index("idx_receitas_data", "receitas", ["data"])
    op.create_index("idx_receitas_categoria", "receitas", ["categoria_id"])
    op.create_index("idx_receitas_banco", "receitas", ["banco_id"])

    # -- Compras cartao indexes --
    op.create_index("idx_compras_cartao_cartao_id", "compras_cartao", ["cartao_id"])
    op.create_index("idx_compras_cartao_mes_fatura", "compras_cartao", ["mes_fatura"])
    op.create_index("idx_compras_cartao_parcelada", "compras_cartao", ["compra_parcelada_id"])

    # -- Pagamentos fatura indexes --
    op.create_index("idx_pagamentos_fatura_cartao_id", "pagamentos_fatura", ["cartao_id"])
    op.create_index("idx_pagamentos_fatura_mes", "pagamentos_fatura", ["mes_fatura"])

    # -- Other entity indexes --
    op.create_index("idx_investimentos_data", "investimentos", ["data"])
    op.create_index("idx_abastecimentos_data", "abastecimentos", ["data"])
    op.create_index("idx_abastecimentos_veiculo", "abastecimentos", ["veiculo_id"])
    op.create_index("idx_manutencoes_data", "manutencoes", ["data"])
    op.create_index("idx_manutencoes_veiculo", "manutencoes", ["veiculo_id"])
    op.create_index("idx_transferencias_data", "transferencias", ["data"])

    # -- Orcamento indexes --
    op.create_index(
        "idx_itens_orcamento_composto",
        "itens_orcamento",
        ["orcamento_id", "categoria_id", "mes"],
    )
    op.create_index("idx_historico_item", "historico_orcamento", ["item_orcamento_id"])
    op.create_index("idx_historico_data", "historico_orcamento", ["data_alteracao"])

    # -- RLS / multi-tenancy indexes --
    op.create_index("idx_bancos_usuario", "bancos", ["usuario_id"])
    op.create_index("idx_categorias_usuario", "categorias", ["usuario_id"])
    op.create_index("idx_receitas_usuario", "receitas", ["usuario_id"])
    op.create_index("idx_despesas_usuario", "despesas", ["usuario_id"])
    op.create_index("idx_cartoes_usuario", "cartoes", ["usuario_id"])
    op.create_index("idx_investimentos_usuario", "investimentos", ["usuario_id"])
    op.create_index("idx_transferencias_usuario", "transferencias", ["usuario_id"])
    op.create_index("idx_veiculos_usuario", "veiculos", ["usuario_id"])
    op.create_index("idx_orcamentos_usuario", "orcamentos", ["usuario_id"])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("idx_orcamentos_usuario", table_name="orcamentos")
    op.drop_index("idx_veiculos_usuario", table_name="veiculos")
    op.drop_index("idx_transferencias_usuario", table_name="transferencias")
    op.drop_index("idx_investimentos_usuario", table_name="investimentos")
    op.drop_index("idx_cartoes_usuario", table_name="cartoes")
    op.drop_index("idx_despesas_usuario", table_name="despesas")
    op.drop_index("idx_receitas_usuario", table_name="receitas")
    op.drop_index("idx_categorias_usuario", table_name="categorias")
    op.drop_index("idx_bancos_usuario", table_name="bancos")
    op.drop_index("idx_historico_data", table_name="historico_orcamento")
    op.drop_index("idx_historico_item", table_name="historico_orcamento")
    op.drop_index("idx_itens_orcamento_composto", table_name="itens_orcamento")
    op.drop_index("idx_transferencias_data", table_name="transferencias")
    op.drop_index("idx_manutencoes_veiculo", table_name="manutencoes")
    op.drop_index("idx_manutencoes_data", table_name="manutencoes")
    op.drop_index("idx_abastecimentos_veiculo", table_name="abastecimentos")
    op.drop_index("idx_abastecimentos_data", table_name="abastecimentos")
    op.drop_index("idx_investimentos_data", table_name="investimentos")
    op.drop_index("idx_pagamentos_fatura_mes", table_name="pagamentos_fatura")
    op.drop_index("idx_pagamentos_fatura_cartao_id", table_name="pagamentos_fatura")
    op.drop_index("idx_compras_cartao_parcelada", table_name="compras_cartao")
    op.drop_index("idx_compras_cartao_mes_fatura", table_name="compras_cartao")
    op.drop_index("idx_compras_cartao_cartao_id", table_name="compras_cartao")
    op.drop_index("idx_receitas_banco", table_name="receitas")
    op.drop_index("idx_receitas_categoria", table_name="receitas")
    op.drop_index("idx_receitas_data", table_name="receitas")
    op.drop_index("idx_despesas_cartao_fatura", table_name="despesas")
    op.drop_index("idx_despesas_recorrente_id", table_name="despesas")
    op.drop_index("idx_despesas_parcelada_id", table_name="despesas")
    op.drop_index("idx_despesas_vencimento", table_name="despesas")
    op.drop_index("idx_despesas_pago", table_name="despesas")
    op.drop_index("idx_despesas_banco", table_name="despesas")
    op.drop_index("idx_despesas_categoria", table_name="despesas")
    op.drop_index("idx_despesas_data", table_name="despesas")

    # Drop tables in reverse dependency order
    op.drop_table("configuracoes")
    op.drop_table("historico_orcamento")
    op.drop_table("itens_orcamento")
    op.drop_table("orcamentos")
    op.drop_table("manutencoes")
    op.drop_table("abastecimentos")
    op.drop_table("veiculos")
    op.drop_table("transferencias")
    op.drop_table("dividendos")
    op.drop_table("investimentos")
    op.drop_table("pagamentos_fatura")
    op.drop_table("compras_cartao")
    op.drop_table("despesas")
    op.drop_table("receitas")
    op.drop_table("cartoes")
    op.drop_table("despesas_recorrentes")
    op.drop_table("despesas_parceladas")
    op.drop_table("categorias")
    op.drop_table("bancos")
    op.drop_table("usuarios")
