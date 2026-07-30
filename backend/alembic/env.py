"""Entorno de migraciones de Alembic (modo asíncrono).

Dos cosas importantes de esta configuración:

1. La URL de la base de datos NO se lee de alembic.ini, sino de la configuración
   de la aplicación (`app.config.settings`), que a su vez la toma del entorno.
   Así las migraciones apuntan siempre a la misma base que usa el backend, y al
   pasar a PostgreSQL en la Fase 2 no hay que tocar dos archivos.

2. `render_as_batch=True` es obligatorio mientras la demo corra sobre SQLite:
   SQLite no soporta la mayoría de los ALTER TABLE, y el modo batch los emula
   recreando la tabla. En PostgreSQL la opción es inofensiva, así que se deja
   activa en ambos motores.
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Permite importar el paquete `app` cuando Alembic se ejecuta desde backend/.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.db import Base  # noqa: E402
import app.models  # noqa: E402, F401  (registra los modelos en Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# La URL efectiva viene de la configuración de la app, no del .ini.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Alembic compara contra esto para autogenerar migraciones. Todo modelo nuevo
# debe estar importado en `app.models` o no será detectado.
target_metadata = Base.metadata

# Opciones comunes a los modos offline y online.
OPCIONES_CONTEXTO = {
    "target_metadata": target_metadata,
    "render_as_batch": True,  # imprescindible en SQLite, inofensivo en PostgreSQL
    "compare_type": True,  # detecta cambios de tipo de columna
    "compare_server_default": True,
}


def run_migrations_offline() -> None:
    """Genera el SQL de las migraciones sin conectarse a la base de datos."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **OPCIONES_CONTEXTO,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Ejecuta las migraciones sobre una conexión ya establecida."""
    context.configure(connection=connection, **OPCIONES_CONTEXTO)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Crea el engine asíncrono y corre las migraciones sobre él."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Aplica las migraciones contra la base de datos real."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
