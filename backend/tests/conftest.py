"""Fixtures compartidas por las pruebas del backend.

Las pruebas corren contra una base de datos **propia y desechable**, nunca
contra `bingo.db`: crear y borrar figuras en la base de desarrollo dejaría
basura y haría que las pruebas se pisaran entre sí.
"""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import normalizar_url_de_base_de_datos
from app.db import Base, get_db
from app.dominio.bingo import TOTAL_BALOTAS
from app.main import app
from app.models import Figura  # noqa: F401  (registra la tabla en Base.metadata)
from app.servicios.ganadores import olvidar_precalculo

# Base de datos en memoria. `cache=shared` es necesario para que todas las
# conexiones del pool vean las mismas tablas; sin eso, cada conexión abriría su
# propia base vacía.
SQLITE_EN_MEMORIA = "sqlite+aiosqlite:///file:pruebas?mode=memory&cache=shared&uri=true"

#: Contra qué motor corre la suite.
#:
#: Por defecto SQLite en memoria: tarda segundos y no exige levantar nada, que
#: es lo que hace falta para el trabajo del día a día.
#:
#: Definiendo `TEST_DATABASE_URL` corre contra PostgreSQL de verdad, que es la
#: única forma de saber que la aplicación funciona igual en los dos motores sin
#: descubrirlo en el servidor. Tarda bastante más, porque crea y destruye el
#: esquema entero en cada prueba. Lo más cómodo es con el compose:
#:
#:   docker compose up -d postgres
#:   $env:TEST_DATABASE_URL = "postgresql+asyncpg://bingo:bingo@localhost:5432/bingo"
#:   .\.venv\Scripts\python.exe -m pytest
URL_PRUEBAS = normalizar_url_de_base_de_datos(
    os.environ.get("TEST_DATABASE_URL") or SQLITE_EN_MEMORIA
)

_ES_SQLITE = URL_PRUEBAS.startswith("sqlite")

#: Contra PostgreSQL, el pool de las pruebas se desactiva.
#:
#: Las pruebas de WebSocket usan `TestClient`, que corre la aplicación **en otro
#: hilo con su propio bucle de eventos**. Una conexión de asyncpg pertenece al
#: bucle en el que se abrió, así que si el pool le entrega a ese hilo una
#: conexión creada en el bucle de pytest, falla con «another operation is in
#: progress» y «attached to a different loop».
#:
#: Con `NullPool` cada uso abre y cierra su propia conexión, en su propio bucle,
#: y el problema desaparece. **Es una limitación de las pruebas, no del
#: producto**: uvicorn corre todo en un único bucle de eventos y ahí el pool
#: normal es justo lo que hace falta (ver `_crear_engine` en `app/db.py`).
#:
#: En SQLite NO se aplica: la base vive en memoria con `cache=shared` y solo
#: existe mientras haya una conexión abierta. Con NullPool se borraría entera
#: entre una consulta y la siguiente.
_OPCIONES_DE_POOL: dict = {} if _ES_SQLITE else {"poolclass": NullPool}


@pytest.fixture(autouse=True)
def sin_precalculo_de_partidas_anteriores() -> None:
    """Vacía el precálculo de máscaras antes de cada prueba.

    El precálculo vive en memoria del proceso, y cada prueba arranca con una
    base nueva donde los identificadores de partida vuelven a empezar en 1. Sin
    esto, una prueba podría evaluar los ganadores con los cartones de la
    anterior.
    """
    olvidar_precalculo()


@pytest.fixture
async def sesion_factory() -> AsyncGenerator[async_sessionmaker, None]:
    """Crea el esquema desde cero para cada prueba y lo destruye al terminar.

    Se parte de tablas vacías en cada prueba para que el orden en que corran no
    cambie el resultado.
    """
    engine = create_async_engine(URL_PRUEBAS, **_OPCIONES_DE_POOL)

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
def cantar_todas(cliente: AsyncClient):
    """Canta balotas hasta agotarlas, reanudando cada vez que un bingo pausa.

    Desde que un bingo detiene el sorteo, un `for _ in range(75)` a secas ya no
    saca 75 balotas: en cuanto alguien gana, la partida queda pausada y el resto
    de peticiones responden 409. Este ayudante hace lo mismo que el
    administrador —atender el bingo y reanudar—, así que las pruebas que
    necesitan un sorteo entero siguen expresando lo que quieren comprobar sin
    llenarse de reanudaciones a mano.

    Devuelve cuántas balotas llegaron a salir.
    """

    async def _cantar(partida_id: int, hasta: int = TOTAL_BALOTAS) -> int:
        sacadas = 0
        while sacadas < hasta:
            respuesta = await cliente.post(f"/api/partidas/{partida_id}/balotas")
            if respuesta.status_code == 201:
                sacadas += 1
                continue

            # 409: o se pausó por un bingo, o ya no hay nada que sacar.
            sorteo = (await cliente.get(f"/api/partidas/{partida_id}/sorteo")).json()
            if sorteo["estado"] != "pausada":
                break

            reanudar = await cliente.post(f"/api/partidas/{partida_id}/reanudar")
            if reanudar.status_code != 200:
                break

        return sacadas

    return _cantar


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
