"""El backend sirve el frontend compilado (tarea #9 de la Fase 1).

Frontend y backend comparten origen a propósito: es lo que permite que el
frontend llame a `/api` y `/ws` con rutas relativas, sin escribir nunca un host
ni un puerto. Vale igual para la demo en la web y para la instalación en la LAN
de la sala.

Estas pruebas fabrican una carpeta `dist` de mentira y montan la aplicación
contra ella, así que no dependen de que alguien haya corrido `npm run build`.
"""

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_con_frontend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Aplicación montada sobre un `dist` de mentira."""
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html>MARCA-INDEX", encoding="utf-8")
    (dist / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")

    # Un archivo fuera de dist, para comprobar que no se puede alcanzar.
    (tmp_path / "secreto.txt").write_text("no debe salir", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST", str(dist))

    # La configuración está cacheada y el montaje ocurre al importar el módulo:
    # hay que rehacer los dos para que vean la carpeta nueva.
    from app import config

    config.get_settings.cache_clear()
    importlib.reload(config)

    from app import main

    importlib.reload(main)

    yield main.app

    # Se deja el módulo como estaba para no afectar al resto de la suite.
    config.get_settings.cache_clear()
    importlib.reload(config)
    importlib.reload(main)


def test_la_raiz_devuelve_el_index(app_con_frontend) -> None:
    respuesta = TestClient(app_con_frontend).get("/")

    assert respuesta.status_code == 200
    assert "MARCA-INDEX" in respuesta.text


def test_una_ruta_interna_devuelve_el_index(app_con_frontend) -> None:
    """Recargar `/admin/partidas/3` debe funcionar: lo resuelve React."""
    respuesta = TestClient(app_con_frontend).get("/admin/partidas/3/balotera")

    assert respuesta.status_code == 200
    assert "MARCA-INDEX" in respuesta.text


def test_los_archivos_reales_se_sirven_tal_cual(app_con_frontend) -> None:
    cliente = TestClient(app_con_frontend)

    assert cliente.get("/favicon.svg").text == "<svg/>"
    assert cliente.get("/assets/app.js").text == "console.log(1)"


def test_una_ruta_de_api_inexistente_da_404_y_no_el_index(
    app_con_frontend,
) -> None:
    """Devolver el HTML con un 200 sería de lo más confuso al depurar."""
    respuesta = TestClient(app_con_frontend).get("/api/no-existe")

    assert respuesta.status_code == 404
    assert "MARCA-INDEX" not in respuesta.text


def test_la_api_sigue_funcionando(app_con_frontend) -> None:
    """El comodín va al final; no debe tapar los endpoints de verdad."""
    respuesta = TestClient(app_con_frontend).get("/api/health")

    assert respuesta.status_code == 200
    assert respuesta.json()["servicio"]


def test_no_se_pueden_leer_archivos_de_fuera_de_dist(app_con_frontend) -> None:
    """Un `..` en la ruta no puede sacar archivos del servidor."""
    cliente = TestClient(app_con_frontend)

    for intento in ("/../secreto.txt", "/assets/../../secreto.txt", "/%2e%2e/secreto.txt"):
        respuesta = cliente.get(intento)
        assert "no debe salir" not in respuesta.text, intento


def test_sin_dist_la_api_funciona_igual() -> None:
    """En desarrollo no hay `dist` y del frontend se encarga Vite."""
    from app.main import app

    respuesta = TestClient(app).get("/api/health")

    assert respuesta.status_code == 200
