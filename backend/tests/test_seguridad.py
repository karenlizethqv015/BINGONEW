"""Pruebas de la tranca de administración.

Lo que hay que garantizar son dos cosas de la demo pública, y tirar de cualquiera
de las dos la rompe:

1. quien no traiga la clave no puede tocar la partida, y
2. **el tablero de la sala y el cartón del jugador siguen entrando sin nada**,
   porque son pantallas del público y no hay a quién pedirle una clave.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.seguridad import CABECERA

CLAVE = "clave-de-la-demo"


@pytest.fixture
def con_clave():
    """Enciende la clave de administración durante la prueba.

    Se cambia el objeto de configuración ya construido, no la variable de
    entorno: `get_settings` está cacheada y no volvería a leer el entorno.
    """
    anterior = settings.admin_clave
    settings.admin_clave = CLAVE
    yield
    settings.admin_clave = anterior


async def _partida_y_carton(cliente: AsyncClient) -> tuple[int, str]:
    """Crea una partida con un cartón, con la clave todavía apagada."""
    partida = (await cliente.post("/api/partidas", json={})).json()["id"]
    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 1})
    return partida, "A"


# --- Sin clave configurada: todo abierto -------------------------------------


async def test_sin_clave_configurada_no_se_exige_nada(cliente: AsyncClient) -> None:
    """Es el caso de desarrollo y el de la LAN de la sala."""
    assert (await cliente.post("/api/partidas", json={})).status_code == 201


# --- Con clave configurada ---------------------------------------------------


async def test_modificar_sin_la_clave_da_401(
    cliente: AsyncClient, con_clave: None
) -> None:
    respuesta = await cliente.post("/api/partidas", json={})

    assert respuesta.status_code == 401
    assert "clave" in respuesta.json()["detail"].lower()


async def test_modificar_con_la_clave_equivocada_da_401(
    cliente: AsyncClient, con_clave: None
) -> None:
    respuesta = await cliente.post(
        "/api/partidas", json={}, headers={CABECERA: "otra-cosa"}
    )

    assert respuesta.status_code == 401


async def test_modificar_con_la_clave_correcta_funciona(
    cliente: AsyncClient, con_clave: None
) -> None:
    respuesta = await cliente.post(
        "/api/partidas", json={}, headers={CABECERA: CLAVE}
    )

    assert respuesta.status_code == 201


async def test_el_sorteo_esta_protegido(cliente: AsyncClient, con_clave: None) -> None:
    """Lo que de verdad hay que proteger: que nadie reinicie la jugada."""
    partida = (
        await cliente.post("/api/partidas", json={}, headers={CABECERA: CLAVE})
    ).json()["id"]

    sin_clave = {"iniciar": None, "pausar": None, "finalizar": None}
    for accion in sin_clave:
        assert (
            await cliente.post(f"/api/partidas/{partida}/{accion}")
        ).status_code == 401, accion

    assert (
        await cliente.post(f"/api/partidas/{partida}/balotas")
    ).status_code == 401
    assert (
        await cliente.delete(f"/api/partidas/{partida}/balotas")
    ).status_code == 401


# --- Lo que NO se puede cerrar -----------------------------------------------


async def test_las_pantallas_del_publico_siguen_entrando_sin_clave(
    cliente: AsyncClient, con_clave: None
) -> None:
    """El tablero de la sala y el cartón del jugador solo consultan.

    Si esto se rompe, la demo deja de funcionar para todo el mundo menos para
    quien tenga la clave, que es justo lo contrario de lo que se busca.
    """
    partida = (
        await cliente.post("/api/partidas", json={}, headers={CABECERA: CLAVE})
    ).json()["id"]
    await cliente.post(
        f"/api/partidas/{partida}/cartones",
        json={"cantidad": 1},
        headers={CABECERA: CLAVE},
    )

    # Lo que piden /transmision y /jugador al cargar.
    for url in (
        f"/api/partidas/{partida}",
        f"/api/partidas/{partida}/sorteo",
        f"/api/partidas/{partida}/balotas",
        f"/api/partidas/{partida}/ganadores",
        f"/api/partidas/{partida}/cartones/A/1",
        "/api/figuras",
    ):
        assert (await cliente.get(url)).status_code == 200, url


async def test_el_websocket_de_la_partida_no_pide_clave(
    cliente: AsyncClient, sesion_factory: async_sessionmaker, con_clave: None
) -> None:
    """El canal en tiempo real alimenta al público; cerrarlo apaga la sala.

    Va por `TestClient` porque `AsyncClient` no habla WebSocket, y hay que
    redirigirle también `get_sesion_factory`: el endpoint del WebSocket abre su
    propia sesión y no usa `get_db`.
    """
    from fastapi.testclient import TestClient

    from app.db import get_sesion_factory
    from app.main import app

    partida = (
        await cliente.post("/api/partidas", json={}, headers={CABECERA: CLAVE})
    ).json()["id"]

    app.dependency_overrides[get_sesion_factory] = lambda: sesion_factory
    try:
        with TestClient(app).websocket_connect(f"/ws/partida/{partida}") as ws:
            assert ws.receive_json()["tipo"] == "sincronizacion"
    finally:
        app.dependency_overrides.pop(get_sesion_factory, None)
