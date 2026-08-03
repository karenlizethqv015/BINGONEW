"""El cuadro de ganadores por el WebSocket.

Es la vía que de verdad usa la pantalla del administrador: el aviso de bingo
tiene que llegarle sin pedir nada. Las pruebas del cálculo están en
`test_ganadores.py`; aquí solo se comprueba que el evento sale, cuándo sale y
que dice lo mismo que el endpoint HTTP.
"""

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db import get_db, get_sesion_factory
from app.dominio.bingo import firma_carton
from app.main import app
from app.models.carton import Carton
from tests.test_ganadores_api import CARTONES, PRIMERA_FILA, SEGUNDA_FILA


def _cliente(sesion_factory: async_sessionmaker) -> TestClient:
    async def get_db_pruebas():
        async with sesion_factory() as sesion:
            yield sesion

    app.dependency_overrides[get_db] = get_db_pruebas
    app.dependency_overrides[get_sesion_factory] = lambda: sesion_factory
    return TestClient(app)


def _esperar(ws, tipo: str, intentos: int = 5) -> dict:
    for _ in range(intentos):
        mensaje = ws.receive_json()
        if mensaje["tipo"] == tipo:
            return mensaje
    raise AssertionError(f"No llegó ningún evento «{tipo}» en {intentos} mensajes.")


def _preparar(cliente: TestClient, sesion_factory: async_sessionmaker) -> int:
    """Partida con dos formas y los tres cartones conocidos."""
    partida_id = cliente.post("/api/partidas", json={"precio_carton": 5000}).json()["id"]

    formas = []
    for nombre, patron in (("Línea", PRIMERA_FILA), ("Segunda", SEGUNDA_FILA)):
        figura = cliente.post(
            "/api/figuras", json={"nombre": nombre, "patron": patron}
        ).json()
        formas.append({"figura_id": figura["id"], "valor_premio": 50000})

    cliente.put(f"/api/partidas/{partida_id}/formas", json={"formas": formas})

    import asyncio

    async def insertar():
        async with sesion_factory() as sesion:
            for codigo, matriz in CARTONES.items():
                serie, numero = codigo.split("-")
                sesion.add(
                    Carton(
                        partida_id=partida_id,
                        serie=serie,
                        numero_carton=int(numero),
                        numeros=matriz,
                        firma=firma_carton(matriz),
                    )
                )
            await sesion.commit()

    asyncio.get_event_loop().run_until_complete(insertar())
    return partida_id


def test_al_conectarse_llega_el_cuadro_de_ganadores(
    sesion_factory: async_sessionmaker,
) -> None:
    """Una pantalla que se abre a mitad de partida debe ver el cuadro al día."""
    cliente = _cliente(sesion_factory)
    try:
        partida = _preparar(cliente, sesion_factory)

        with cliente.websocket_connect(f"/ws/partida/{partida}") as ws:
            _esperar(ws, "sincronizacion")
            cuadro = _esperar(ws, "ganadores")

        assert cuadro["partida_id"] == partida
        assert cuadro["bingos"] == []
        assert cuadro["a_una"] == 0 and cuadro["a_dos"] == 0
    finally:
        app.dependency_overrides.clear()


def test_cada_balota_emite_el_cuadro_actualizado(
    sesion_factory: async_sessionmaker,
) -> None:
    cliente = _cliente(sesion_factory)
    try:
        partida = _preparar(cliente, sesion_factory)
        cliente.post(f"/api/partidas/{partida}/iniciar")

        with cliente.websocket_connect(f"/ws/partida/{partida}") as ws:
            _esperar(ws, "sincronizacion")
            _esperar(ws, "ganadores")

            cliente.post(f"/api/partidas/{partida}/balotas")
            _esperar(ws, "balota")
            cuadro = _esperar(ws, "ganadores")

        assert cuadro["orden_balota"] == 1
    finally:
        app.dependency_overrides.clear()


def test_el_aviso_de_bingo_llega_en_vivo_y_marcado_como_nuevo(
    sesion_factory: async_sessionmaker,
) -> None:
    """Es el aviso que tiene que saltarle al administrador en el momento.

    `nuevo` distingue el bingo recién detectado del que ya se avisó: sin él, la
    pantalla volvería a dar el aviso en cada balota posterior.
    """
    cliente = _cliente(sesion_factory)
    try:
        partida = _preparar(cliente, sesion_factory)
        cliente.post(f"/api/partidas/{partida}/iniciar")

        with cliente.websocket_connect(f"/ws/partida/{partida}") as ws:
            _esperar(ws, "sincronizacion")
            _esperar(ws, "ganadores")

            frescos = None
            for _ in range(75):
                cliente.post(f"/api/partidas/{partida}/balotas")
                _esperar(ws, "balota")
                cuadro = _esperar(ws, "ganadores")

                nuevos = [b for b in cuadro["bingos"] if b["nuevo"]]
                if nuevos:
                    frescos = (cuadro, nuevos)
                    break

        assert frescos is not None, "nadie ganó en 75 balotas"
        cuadro, nuevos = frescos

        bingo = nuevos[0]
        assert bingo["cartones"], "un bingo sin cartones no tiene sentido"
        assert bingo["valor_premio"] == 50000
        assert bingo["orden_balota"] == cuadro["orden_balota"]
        assert cuadro["total_cartones_ganadores"] >= 1
    finally:
        app.dependency_overrides.clear()


def test_el_websocket_y_el_endpoint_dicen_lo_mismo(
    sesion_factory: async_sessionmaker,
) -> None:
    """Se construyen con la misma función; esto lo comprueba de verdad."""
    cliente = _cliente(sesion_factory)
    try:
        partida = _preparar(cliente, sesion_factory)
        cliente.post(f"/api/partidas/{partida}/iniciar")
        for _ in range(20):
            cliente.post(f"/api/partidas/{partida}/balotas")

        with cliente.websocket_connect(f"/ws/partida/{partida}") as ws:
            _esperar(ws, "sincronizacion")
            por_ws = _esperar(ws, "ganadores")

        por_http = cliente.get(f"/api/partidas/{partida}/ganadores").json()

        assert por_ws == por_http
    finally:
        app.dependency_overrides.clear()
