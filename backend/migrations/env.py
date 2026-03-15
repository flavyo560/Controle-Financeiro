"""Alembic environment configuration.

Imports Base and all models so autogenerate can detect schema changes.
Reads the database URL from app.config.settings.SUPABASE_URL.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

# Import all models so they are registered on Base.metadata
from app.models import (  # noqa: F401
    Usuario,
    Banco,
    Categoria,
    Receita,
    Despesa,
    DespesaParcelada,
    DespesaRecorrente,
    Cartao,
    CompraCartao,
    PagamentoFatura,
    Investimento,
    Dividendo,
    Transferencia,
    Veiculo,
    Abastecimento,
    Manutencao,
    Orcamento,
    ItemOrcamento,
    HistoricoOrcamento,
    Configuracao,
)

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """Return database URL from application settings."""
    return settings.SUPABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
