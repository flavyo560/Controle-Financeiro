"""Subscription tables — assinaturas, logs_assinatura, and trial columns.

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── assinaturas ───────────────────────────────────────────────────
    op.create_table(
        "assinaturas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("plano", sa.String(20), nullable=False),
        sa.Column("ciclo", sa.String(10), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="ativa",
        ),
        sa.Column(
            "data_inicio",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("data_renovacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("plano IN ('simples', 'plus')", name="ck_assinaturas_plano"),
        sa.CheckConstraint("ciclo IN ('mensal', 'anual')", name="ck_assinaturas_ciclo"),
        sa.CheckConstraint(
            "status IN ('ativa', 'cancelada', 'expirada', 'inadimplente')",
            name="ck_assinaturas_status",
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", name="uq_assinaturas_usuario"),
    )

    # ── logs_assinatura ───────────────────────────────────────────────
    op.create_table(
        "logs_assinatura",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("evento", sa.String(100), nullable=False),
        sa.Column("status_anterior", sa.String(20), nullable=True),
        sa.Column("status_novo", sa.String(20), nullable=True),
        sa.Column("detalhes", sa.Text(), nullable=True),
        sa.Column("stripe_event_id", sa.String(255), nullable=True),
        sa.Column("admin_id", sa.Integer(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admin_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── Alter usuarios — add trial columns ────────────────────────────
    op.add_column("usuarios", sa.Column("trial_inicio", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "usuarios",
        sa.Column("trial_usado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # ══════════════════════════════════════════════════════════════════
    # Indexes
    # ══════════════════════════════════════════════════════════════════
    op.create_index("idx_assinaturas_usuario", "assinaturas", ["usuario_id"])
    op.create_index("idx_assinaturas_status", "assinaturas", ["status"])
    op.create_index("idx_assinaturas_stripe_customer", "assinaturas", ["stripe_customer_id"])
    op.create_index("idx_logs_assinatura_usuario", "logs_assinatura", ["usuario_id"])
    op.create_index("idx_logs_assinatura_evento", "logs_assinatura", ["stripe_event_id"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_logs_assinatura_evento", table_name="logs_assinatura")
    op.drop_index("idx_logs_assinatura_usuario", table_name="logs_assinatura")
    op.drop_index("idx_assinaturas_stripe_customer", table_name="assinaturas")
    op.drop_index("idx_assinaturas_status", table_name="assinaturas")
    op.drop_index("idx_assinaturas_usuario", table_name="assinaturas")

    # Drop trial columns from usuarios
    op.drop_column("usuarios", "trial_usado")
    op.drop_column("usuarios", "trial_inicio")

    # Drop tables
    op.drop_table("logs_assinatura")
    op.drop_table("assinaturas")
