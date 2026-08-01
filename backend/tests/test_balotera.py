"""Pruebas de la balotera: sorteo, estados y emisión por WebSocket."""

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db import get_db, get_sesion_factory
from app.dominio.bingo import TOTAL_BALOTAS
from app.main import app


async def _crear_partida(cliente: AsyncClient) -> int:
    respuesta = await cliente.post("/api/partidas", json={"precio_carton": 5000})
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


async def _partida_en_curso(cliente: AsyncClient) -> int:
    partida = await _crear_partida(cliente)
    assert (await cliente.post(f"/api/partidas/{partida}/iniciar")).status_code == 200
    return partida


# --- Estados ----------------------------------------------------------------


async def test_una_partida_nueva_esta_pendiente(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    sorteo = (await cliente.get(f"/api/partidas/{partida}/sorteo")).json()

    assert sorteo["estado"] == "pendiente"
    assert sorteo["total_cantadas"] == 0
    assert sorteo["restantes"] == TOTAL_BALOTAS
    assert sorteo["ultima"] is None


async def test_ciclo_completo_de_estados(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    assert (await cliente.post(f"/api/partidas/{partida}/iniciar")).json()["estado"] == "en_curso"
    assert (await cliente.post(f"/api/partidas/{partida}/pausar")).json()["estado"] == "pausada"
    assert (await cliente.post(f"/api/partidas/{partida}/reanudar")).json()["estado"] == "en_curso"
    assert (await cliente.post(f"/api/partidas/{partida}/finalizar")).json()["estado"] == "finalizada"


async def test_no_se_puede_iniciar_dos_veces(cliente: AsyncClient) -> None:
    partida = await _partida_en_curso(cliente)

    assert (await cliente.post(f"/api/partidas/{partida}/iniciar")).status_code == 409


async def test_no_se_puede_pausar_lo_que_no_esta_en_curso(
    cliente: AsyncClient,
) -> None:
    partida = await _crear_partida(cliente)

    assert (await cliente.post(f"/api/partidas/{partida}/pausar")).status_code == 409


async def test_no_se_puede_reanudar_lo_que_no_esta_pausado(
    cliente: AsyncClient,
) -> None:
    partida = await _partida_en_curso(cliente)

    assert (await cliente.post(f"/api/partidas/{partida}/reanudar")).status_code == 409


async def test_no_se_puede_finalizar_una_partida_sin_empezar(
    cliente: AsyncClient,
) -> None:
    partida = await _crear_partida(cliente)

    assert (await cliente.post(f"/api/partidas/{partida}/finalizar")).status_code == 409


# --- Sorteo -----------------------------------------------------------------


async def test_no_se_canta_con_la_partida_pendiente(cliente: AsyncClient) -> None:
    """El sorteo solo corre con la partida en curso."""
    partida = await _crear_partida(cliente)

    respuesta = await cliente.post(f"/api/partidas/{partida}/balotas")

    assert respuesta.status_code == 409


async def test_no_se_canta_con_la_partida_pausada(cliente: AsyncClient) -> None:
    partida = await _partida_en_curso(cliente)
    await cliente.post(f"/api/partidas/{partida}/pausar")

    assert (await cliente.post(f"/api/partidas/{partida}/balotas")).status_code == 409


async def test_cantar_una_balota(cliente: AsyncClient) -> None:
    partida = await _partida_en_curso(cliente)

    respuesta = await cliente.post(f"/api/partidas/{partida}/balotas")

    assert respuesta.status_code == 201

    balota = respuesta.json()
    assert 1 <= balota["numero"] <= TOTAL_BALOTAS
    assert balota["orden"] == 1
    assert balota["letra"] in {"B", "I", "N", "G", "O"}


async def test_el_orden_es_consecutivo(cliente: AsyncClient) -> None:
    partida = await _partida_en_curso(cliente)

    for _ in range(10):
        await cliente.post(f"/api/partidas/{partida}/balotas")

    balotas = (await cliente.get(f"/api/partidas/{partida}/balotas")).json()

    assert [b["orden"] for b in balotas] == list(range(1, 11))


async def test_un_sorteo_completo_saca_las_75_sin_repetir(
    cliente: AsyncClient,
) -> None:
    """La prueba que de verdad importa: una partida entera de punta a punta."""
    partida = await _partida_en_curso(cliente)

    for _ in range(TOTAL_BALOTAS):
        assert (await cliente.post(f"/api/partidas/{partida}/balotas")).status_code == 201

    balotas = (await cliente.get(f"/api/partidas/{partida}/balotas")).json()
    numeros = [b["numero"] for b in balotas]

    assert len(numeros) == TOTAL_BALOTAS
    assert sorted(numeros) == list(range(1, TOTAL_BALOTAS + 1))
    assert [b["orden"] for b in balotas] == list(range(1, TOTAL_BALOTAS + 1))


async def test_la_partida_se_finaliza_sola_al_agotar_las_balotas(
    cliente: AsyncClient,
) -> None:
    partida = await _partida_en_curso(cliente)

    for _ in range(TOTAL_BALOTAS):
        await cliente.post(f"/api/partidas/{partida}/balotas")

    sorteo = (await cliente.get(f"/api/partidas/{partida}/sorteo")).json()

    assert sorteo["estado"] == "finalizada"
    assert sorteo["restantes"] == 0


async def test_no_se_puede_cantar_la_76(cliente: AsyncClient) -> None:
    partida = await _partida_en_curso(cliente)
    for _ in range(TOTAL_BALOTAS):
        await cliente.post(f"/api/partidas/{partida}/balotas")

    respuesta = await cliente.post(f"/api/partidas/{partida}/balotas")

    assert respuesta.status_code == 409


async def test_reiniciar_el_sorteo(cliente: AsyncClient) -> None:
    partida = await _partida_en_curso(cliente)
    for _ in range(5):
        await cliente.post(f"/api/partidas/{partida}/balotas")

    assert (await cliente.delete(f"/api/partidas/{partida}/balotas")).status_code == 204

    sorteo = (await cliente.get(f"/api/partidas/{partida}/sorteo")).json()
    assert sorteo["estado"] == "pendiente"
    assert sorteo["total_cantadas"] == 0
    assert (await cliente.get(f"/api/partidas/{partida}/balotas")).json() == []


async def test_tras_reiniciar_se_puede_volver_a_jugar(cliente: AsyncClient) -> None:
    partida = await _partida_en_curso(cliente)
    for _ in range(5):
        await cliente.post(f"/api/partidas/{partida}/balotas")
    await cliente.delete(f"/api/partidas/{partida}/balotas")

    await cliente.post(f"/api/partidas/{partida}/iniciar")
    respuesta = await cliente.post(f"/api/partidas/{partida}/balotas")

    assert respuesta.status_code == 201
    assert respuesta.json()["orden"] == 1


async def test_borrar_la_partida_borra_sus_balotas(cliente: AsyncClient) -> None:
    partida = await _partida_en_curso(cliente)
    await cliente.post(f"/api/partidas/{partida}/balotas")

    assert (await cliente.delete(f"/api/partidas/{partida}")).status_code == 204
    assert (await cliente.get(f"/api/partidas/{partida}/balotas")).status_code == 404


async def test_partida_inexistente_da_404(cliente: AsyncClient) -> None:
    assert (await cliente.post("/api/partidas/9999/balotas")).status_code == 404
    assert (await cliente.post("/api/partidas/9999/iniciar")).status_code == 404


# --- WebSocket --------------------------------------------------------------
#
# Usan TestClient (síncrono) porque es el único que sabe hablar WebSocket contra
# la app. Comparten la base de datos de pruebas mediante el override de get_db.


def _con_base_de_pruebas(sesion_factory: async_sessionmaker) -> TestClient:
    """Apunta a la base de pruebas tanto los endpoints HTTP como los WebSocket.

    Son dos dependencias distintas a propósito: los endpoints HTTP reciben una
    sesión (`get_db`) y los WebSocket la fábrica (`get_sesion_factory`), porque
    estos últimos no deben retener una conexión mientras el cliente esté
    conectado.
    """

    async def get_db_pruebas():
        async with sesion_factory() as sesion:
            yield sesion

    app.dependency_overrides[get_db] = get_db_pruebas
    app.dependency_overrides[get_sesion_factory] = lambda: sesion_factory
    return TestClient(app)


def _esperar(ws, tipo: str, intentos: int = 5) -> dict:
    """Recibe eventos hasta encontrar uno del tipo pedido.

    Cada balota emite dos eventos —la balota y el cuadro de ganadores— y al
    conectarse llegan otros dos. Esperar por tipo, en vez de contar mensajes,
    evita que agregar un evento más rompa cada prueba que escucha el canal.
    """
    for _ in range(intentos):
        mensaje = ws.receive_json()
        if mensaje["tipo"] == tipo:
            return mensaje
    raise AssertionError(f"No llegó ningún evento «{tipo}» en {intentos} mensajes.")


def test_al_conectarse_llega_la_sincronizacion(
    sesion_factory: async_sessionmaker,
) -> None:
    cliente_ws = _con_base_de_pruebas(sesion_factory)
    try:
        partida = cliente_ws.post("/api/partidas", json={}).json()

        with cliente_ws.websocket_connect(f"/ws/partida/{partida['id']}") as ws:
            mensaje = ws.receive_json()

        assert mensaje["tipo"] == "sincronizacion"
        assert mensaje["partida_id"] == partida["id"]
        assert mensaje["estado"] == "pendiente"
        assert mensaje["balotas"] == []
        assert mensaje["restantes"] == TOTAL_BALOTAS
    finally:
        app.dependency_overrides.clear()


def test_la_sincronizacion_trae_las_balotas_ya_cantadas(
    sesion_factory: async_sessionmaker,
) -> None:
    """Quien llega tarde debe poder reconstruir el tablero completo."""
    cliente_ws = _con_base_de_pruebas(sesion_factory)
    try:
        partida = cliente_ws.post("/api/partidas", json={}).json()
        cliente_ws.post(f"/api/partidas/{partida['id']}/iniciar")
        for _ in range(7):
            cliente_ws.post(f"/api/partidas/{partida['id']}/balotas")

        with cliente_ws.websocket_connect(f"/ws/partida/{partida['id']}") as ws:
            mensaje = ws.receive_json()

        assert mensaje["total_cantadas"] == 7
        assert len(mensaje["balotas"]) == 7
        assert [b["orden"] for b in mensaje["balotas"]] == list(range(1, 8))
        assert all(b["letra"] for b in mensaje["balotas"])
    finally:
        app.dependency_overrides.clear()


def test_cantar_emite_el_evento_a_los_conectados(
    sesion_factory: async_sessionmaker,
) -> None:
    """El evento central: es lo que mueve tablero, cartón y panel."""
    cliente_ws = _con_base_de_pruebas(sesion_factory)
    try:
        partida = cliente_ws.post("/api/partidas", json={}).json()
        cliente_ws.post(f"/api/partidas/{partida['id']}/iniciar")

        with cliente_ws.websocket_connect(f"/ws/partida/{partida['id']}") as ws:
            _esperar(ws, "sincronizacion")
            _esperar(ws, "ganadores")

            respuesta = cliente_ws.post(f"/api/partidas/{partida['id']}/balotas")
            evento = _esperar(ws, "balota")

        assert evento["tipo"] == "balota"
        assert evento["balota"]["numero"] == respuesta.json()["numero"]
        assert evento["balota"]["letra"] == respuesta.json()["letra"]
        assert evento["balota"]["orden"] == 1
        assert evento["total_cantadas"] == 1
        assert evento["restantes"] == TOTAL_BALOTAS - 1
    finally:
        app.dependency_overrides.clear()


def test_cambiar_de_estado_emite_evento(
    sesion_factory: async_sessionmaker,
) -> None:
    cliente_ws = _con_base_de_pruebas(sesion_factory)
    try:
        partida = cliente_ws.post("/api/partidas", json={}).json()

        with cliente_ws.websocket_connect(f"/ws/partida/{partida['id']}") as ws:
            _esperar(ws, "sincronizacion")
            _esperar(ws, "ganadores")

            cliente_ws.post(f"/api/partidas/{partida['id']}/iniciar")
            evento = _esperar(ws, "estado")

        assert evento["tipo"] == "estado"
        assert evento["estado"] == "en_curso"
    finally:
        app.dependency_overrides.clear()


def test_el_websocket_de_una_partida_inexistente_se_cierra(
    sesion_factory: async_sessionmaker,
) -> None:
    from starlette.websockets import WebSocketDisconnect as WSDisconnect

    cliente_ws = _con_base_de_pruebas(sesion_factory)
    try:
        import pytest

        with pytest.raises(WSDisconnect):
            with cliente_ws.websocket_connect("/ws/partida/9999") as ws:
                ws.receive_json()
    finally:
        app.dependency_overrides.clear()
