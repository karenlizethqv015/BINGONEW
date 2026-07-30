"""Motor de base de datos, sesiones asíncronas y clase Base del ORM.

IMPORTANTE (compatibilidad con PostgreSQL):
la demo corre sobre SQLite, pero la instalación final en LAN usa PostgreSQL.
Para que ese cambio sea únicamente cambiar DATABASE_URL, los modelos deben
respetar las reglas descritas en el README.md de esta carpeta: tipo JSON
genérico (nunca JSONB), DateTime(timezone=True), y nada de SQL crudo
específico de un motor.
"""

from collections.abc import AsyncGenerator

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


def _crear_engine() -> AsyncEngine:
    """Crea el engine asíncrono a partir de la configuración."""
    opciones: dict = {"echo": settings.db_echo, "future": True}

    # SQLite no admite las opciones de pool de un motor cliente/servidor.
    # Se separan aquí para no tener que tocar nada al migrar a PostgreSQL.
    if not settings.database_url.startswith("sqlite"):
        opciones.update(pool_pre_ping=True, pool_size=5, max_overflow=10)

    return create_async_engine(settings.database_url, **opciones)


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
