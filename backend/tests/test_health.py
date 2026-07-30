"""Pruebas del endpoint de salud y del canal WebSocket de prueba."""

from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


async def test_health_responde_ok(cliente: AsyncClient) -> None:
    """El endpoint de salud responde 200 y reporta el estado del servicio."""
    respuesta = await cliente.get("/api/health")

    assert respuesta.status_code == 200

    datos = respuesta.json()
    assert datos["estado"] == "ok"
    assert datos["version"]
    # No debe filtrar la cadena de conexión completa, solo el motor.
    assert "://" not in datos["motor_bd"]


async def test_health_reporta_base_de_datos_accesible(cliente: AsyncClient) -> None:
    """La consulta de prueba contra la base de datos debe funcionar.

    Si esto falla, casi siempre es que no se corrió `alembic upgrade head`.
    """
    datos = (await cliente.get("/api/health")).json()

    assert datos["base_datos"] is True


def test_websocket_echo_devuelve_lo_recibido() -> None:
    """El canal en tiempo real acepta la conexión y responde.

    Verifica de punta a punta el mismo `GestorConexiones` que en la Fase 1 usará
    la balotera para emitir las balotas.
    """
    with TestClient(app).websocket_connect("/ws/echo") as ws:
        bienvenida = ws.receive_json()
        assert bienvenida["tipo"] == "conectado"
        assert bienvenida["conexiones"] >= 1

        ws.send_text("balota-de-prueba")
        eco = ws.receive_json()

        assert eco == {"tipo": "eco", "mensaje": "balota-de-prueba"}
