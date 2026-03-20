"""Add tipo and cartao_id columns to bancos table.

Revision ID: 003
Revises: 002
Create Date: 2024-01-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tipo column with default 'debito'
    op.add_column(
        "bancos",
        sa.Column("tipo", sa.String(10), nullable=False, server_default="debito"),
    )
    op.create_check_constraint(
        "ck_bancos_tipo",
        "bancos",
        "tipo IN ('debito', 'credito')",
    )

    # Add cartao_id FK column
    op.add_column(
        "bancos",
        sa.Column("cartao_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_bancos_cartao_id",
        "bancos",
        "cartoes",
        ["cartao_id"],
        ["id"],
    )
    op.create_index("idx_bancos_cartao_id", "bancos", ["cartao_id"])


def downgrade() -> None:
    op.drop_index("idx_bancos_cartao_id", table_name="bancos")
    op.drop_constraint("fk_bancos_cartao_id", "bancos", type_="foreignkey")
    op.drop_column("bancos", "cartao_id")
    op.drop_constraint("ck_bancos_tipo", "bancos", type_="check")
    op.drop_column("bancos", "tipo")
