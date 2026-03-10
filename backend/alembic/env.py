from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.db.base import Base
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def normalize_database_url(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    if value.startswith("postgresql://"):
        value = "postgresql+asyncpg://" + value[len("postgresql://") :]
    parts = urlsplit(value)
    query_items = dict(parse_qsl(parts.query, keep_blank_values=True))
    sslmode = query_items.pop("sslmode", None)
    query_items.pop("channel_binding", None)
    if sslmode and "ssl" not in query_items:
        query_items["ssl"] = "require" if sslmode.lower() in {"require", "verify-full"} else sslmode
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query_items), parts.fragment))


def get_database_url() -> str:
    return normalize_database_url(
        os.getenv("DATABASE_URL_DIRECT")
        or os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
    )


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
