"""Configuração do SQLAlchemy: engine, sessão e Base declarativa."""

import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# Supabase Transaction Pooler (PgBouncer) não suporta prepared statements
# Precisamos desabilitar statement caching para funcionar corretamente
_connect_args: dict = {}
_engine_kwargs: dict = {
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 10,
}

# Se estiver usando o pooler do Supabase (porta 6543), desabilitar prepared statements
if "pooler.supabase.com" in settings.SUPABASE_URL:
    _engine_kwargs["pool_pre_ping"] = True
    _connect_args["options"] = "-c statement_timeout=30000"
    # PgBouncer em modo transaction não suporta prepared statements
    _engine_kwargs["connect_args"] = _connect_args
    _engine_kwargs["execution_options"] = {"prepared_statement_cache_size": 0}

engine = create_engine(
    settings.SUPABASE_URL,
    **_engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos SQLAlchemy."""

    pass
