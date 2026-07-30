"""Fixtures compartidas por las pruebas del backend.

Las pruebas corren contra una base de datos **propia y desechable**, nunca
contra `bingo.db`: crear y borrar figuras en la base de desarrollo dejaría
basura y haría que las pruebas se pisaran entre sí.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base, get_db
from app.main import app
from app.models import Figura  # noqa: F401  (registra la tabla en Base.metadata)

# Base de datos en memoria. `cache=shared` es necesario para que todas las
# conexiones del pool vean las mismas tablas; sin eso, cada conexión abriría su
# propia base vacía.
URL_PRUEBAS = "sqlite+aiosqlite:///file:pruebas?mode=memory&cache=shared&uri=true"


@pytest.fixture
async def sesion_factory() -> AsyncGenerator[async_sessionmaker, None]:
    """Crea el esquema desde cero para cada prueba y lo destruye al terminar.

    Se parte de tablas vacías en cada prueba para que el orden en que corran no
    cambie el resultado.
    """
    engine = create_async_engine(URL_PRUEBAS)

    async with engine.begin() as conexion:
        await conexion.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as conexion:
        await conexion.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def cliente(sesion_factory: async_sessionmaker) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP que habla con la app usando la base de datos de pruebas.

    ASGITransport ejecuta la aplicación en el mismo proceso, así que no hace
    falta levantar un servidor ni buscar un puerto libre.
    """

    async def get_db_pruebas() -> AsyncGenerator:
        async with sesion_factory() as sesion:
            yield sesion

    app.dependency_overrides[get_db] = get_db_pruebas

    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def patron_linea() -> list[list[bool]]:
    """Patrón de ejemplo: la primera fila completa (5 celdas)."""
    return [
        [True, True, True, True, True],
        [False] * 5,
        [False] * 5,
        [False] * 5,
        [False] * 5,
    ]


@pytest.fixture
def patron_esquinas() -> list[list[bool]]:
    """Patrón de ejemplo: las cuatro esquinas (4 celdas, sin la casilla libre)."""
    patron = [[False] * 5 for _ in range(5)]
    for fila in (0, 4):
        for columna in (0, 4):
            patron[fila][columna] = True
    return patron
