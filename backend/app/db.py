"""Motor de base de datos, sesiones asíncronas y clase Base del ORM.

IMPORTANTE (compatibilidad con PostgreSQL):
la demo corre sobre SQLite, pero la instalación final en LAN usa PostgreSQL.
Para que ese cambio sea únicamente cambiar DATABASE_URL, los modelos deben
respetar las reglas descritas en el README.md de esta carpeta: tipo JSON
genérico (nunca JSONB), DateTime(timezone=True), y nada de SQL crudo
específico de un motor.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos del ORM.

    Alembic lee `Base.metadata` para autogenerar las migraciones, así que todo
    modelo nuevo debe heredar de aquí y quedar importado en `app.models`.
    """


def activar_llaves_foraneas_en_sqlite(engine: AsyncEngine) -> None:
    """Hace que SQLite respete las llaves foráneas.

    SQLite las ignora por defecto: sin este PRAGMA, un ON DELETE RESTRICT no
    impide nada y se podría borrar una figura que una partida está usando,
    dejando huérfano el historial. PostgreSQL las aplica siempre, así que esto
    solo hace falta en la demo.

    Se registra por conexión porque el PRAGMA no es global, sino de cada
    conexión del pool.
    """

    @event.listens_for(engine.sync_engine, "connect")
    def _activar(conexion_dbapi: Any, _registro: Any) -> None:
        cursor = conexion_dbapi.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _crear_engine() -> AsyncEngine:
    """Crea el engine asíncrono a partir de la configuración."""
    opciones: dict = {"echo": settings.db_echo, "future": True}
    es_sqlite = settings.database_url.startswith("sqlite")

    # SQLite no admite las opciones de pool de un motor cliente/servidor.
    # Se separan aquí para no tener que tocar nada al migrar a PostgreSQL.
    if not es_sqlite:
        opciones.update(pool_pre_ping=True, pool_size=5, max_overflow=10)

    nuevo_engine = create_async_engine(settings.database_url, **opciones)

    if es_sqlite:
        activar_llaves_foraneas_en_sqlite(nuevo_engine)

    return nuevo_engine


engine: AsyncEngine = _crear_engine()

# expire_on_commit=False evita que los objetos queden inutilizables después de
# un commit, algo incómodo al devolverlos como respuesta de un endpoint.
SesionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI que entrega una sesión por petición.

    Uso en un endpoint:
        async def endpoint(db: AsyncSession = Depends(get_db)): ...
    """
    async with SesionLocal() as sesion:
        try:
            yield sesion
        except Exception:
            await sesion.rollback()
            raise
