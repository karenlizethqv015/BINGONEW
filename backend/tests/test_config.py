"""Pruebas de la normalización de la cadena de conexión.

El objetivo es poder pegar la URL que da el proveedor sin editarla. Los dos
fallos que esto evita no dan mensajes que ayuden:

- sin el driver, SQLAlchemy busca uno síncrono y el arranque muere;
- con `sslmode` dentro, asyncpg lanza un `TypeError` sobre un argumento
  inesperado que no menciona la URL por ninguna parte.
"""

import pytest

from app.config import normalizar_url_de_base_de_datos as normalizar


def test_le_pone_el_driver_asincrono() -> None:
    assert (
        normalizar("postgresql://karen:clave@servidor:5432/bingo")
        == "postgresql+asyncpg://karen:clave@servidor:5432/bingo"
    )


def test_acepta_la_forma_antigua_postgres() -> None:
    """Varios proveedores siguen entregando `postgres://` a secas."""
    assert normalizar("postgres://karen:clave@servidor:5432/bingo").startswith(
        "postgresql+asyncpg://"
    )


@pytest.mark.parametrize(
    "parametro",
    ["sslmode=require", "channel_binding=require", "gssencmode=disable"],
)
def test_quita_los_parametros_que_asyncpg_no_entiende(parametro: str) -> None:
    url = normalizar(f"postgresql://karen:clave@servidor:5432/bingo?{parametro}")

    assert parametro.split("=")[0] not in url
    assert url == "postgresql+asyncpg://karen:clave@servidor:5432/bingo"


def test_conserva_los_parametros_que_si_valen() -> None:
    """Solo se quitan los de libpq; el resto puede hacer falta."""
    url = normalizar(
        "postgresql://karen:clave@servidor:5432/bingo"
        "?sslmode=require&application_name=bingo"
    )

    assert "application_name=bingo" in url
    assert "sslmode" not in url


def test_no_toca_una_cadena_que_ya_trae_driver() -> None:
    url = "postgresql+asyncpg://karen:clave@servidor:5432/bingo"

    assert normalizar(url) == url


def test_no_toca_sqlite() -> None:
    """El caso de todos los días: desarrollo y pruebas."""
    assert normalizar("sqlite+aiosqlite:///./bingo.db") == (
        "sqlite+aiosqlite:///./bingo.db"
    )


def test_conserva_la_clave_con_caracteres_raros() -> None:
    """Las claves que generan los proveedores traen de todo.

    Si la normalización descodificara la URL al reconstruirla, una clave con un
    `%` o un `@` quedaría rota y el fallo aparecería como «contraseña
    incorrecta», sin relación aparente con este código.
    """
    url = normalizar("postgresql://karen:aB3%2Fx%40z@servidor:5432/bingo")

    assert "aB3%2Fx%40z" in url
