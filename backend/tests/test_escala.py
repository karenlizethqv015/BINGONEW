"""Prueba de carga: una sala grande, con 5000 cartones y diez formas.

Algunas salas juegan con 5000 cartones o más. La validación de ganadores mira
cada cartón contra cada forma, así que es la pieza que se hunde primero: son
50.000 comprobaciones por balota, 75 veces por partida, y corren en el mismo
hilo que atiende los WebSockets de todas las pantallas conectadas.

**No corre con la suite normal.** Genera 5000 cartones y canta las 75 balotas,
así que tarda bastante más que todo lo demás junto. Se pide a propósito:

    .venv\\Scripts\\python.exe -m pytest -m lento -s

El `-s` es lo interesante: imprime los tiempos reales. La prueba en sí solo
falla si algo se sale de un margen muy holgado —está para que un cambio que
multiplique el coste por diez se note, no para medir el rendimiento de la
máquina en la que corra.
"""

import time

import pytest
from httpx import AsyncClient

from app.dominio.bingo import TOTAL_BALOTAS

pytestmark = pytest.mark.lento

#: El tamaño que pidió la usuaria: «algunas salas manejan incluso hasta 5000».
CARTONES = 5000

#: Una partida real no lleva diez formas, pero es el peor caso razonable y el
#: coste crece con el producto de las dos cifras.
FORMAS = 10

#: Techo por balota. Es deliberadamente holgado —unas cinco veces lo medido— y
#: no una medida de rendimiento: sirve para que una regresión gorda salte.
MAXIMO_MS_POR_BALOTA = 400


def _patrones() -> list[list[list[bool]]]:
    """Diez figuras de tamaños variados: cinco filas, cuatro columnas y esquinas."""
    patrones = []

    for fila in range(5):
        patron = [[False] * 5 for _ in range(5)]
        for columna in range(5):
            patron[fila][columna] = True
        patrones.append(patron)

    for columna in range(4):
        patron = [[False] * 5 for _ in range(5)]
        for fila in range(5):
            patron[fila][columna] = True
        patrones.append(patron)

    esquinas = [[False] * 5 for _ in range(5)]
    for fila in (0, 4):
        for columna in (0, 4):
            esquinas[fila][columna] = True
    patrones.append(esquinas)

    return patrones


async def test_una_sala_de_5000_cartones_aguanta_un_sorteo_completo(
    cliente: AsyncClient, cantar_todas
) -> None:
    partida = (
        await cliente.post("/api/partidas", json={"precio_carton": 5000})
    ).json()["id"]

    formas = []
    for indice, patron in enumerate(_patrones(), start=1):
        figura = (
            await cliente.post(
                "/api/figuras", json={"nombre": f"Forma {indice}", "patron": patron}
            )
        ).json()
        formas.append({"figura_id": figura["id"], "valor_premio": 50000})

    respuesta = await cliente.put(
        f"/api/partidas/{partida}/formas", json={"formas": formas}
    )
    assert respuesta.status_code == 200, respuesta.text

    # --- Generar los cartones ---
    inicio = time.perf_counter()
    generados = await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": CARTONES}
    )
    segundos_generar = time.perf_counter() - inicio

    assert generados.status_code == 201, generados.text
    assert generados.json()["cantidad"] == CARTONES

    # --- Cantar las 75 ---
    await cliente.post(f"/api/partidas/{partida}/iniciar")

    inicio = time.perf_counter()
    sacadas = await cantar_todas(partida)
    segundos_sorteo = time.perf_counter() - inicio

    assert sacadas == TOTAL_BALOTAS

    ms_por_balota = segundos_sorteo * 1000 / TOTAL_BALOTAS
    print(
        f"\n{CARTONES} cartones x {FORMAS} formas"
        f"\n  generar:  {segundos_generar:.1f} s"
        f"\n  sorteo:   {segundos_sorteo:.1f} s"
        f"  ({ms_por_balota:.0f} ms por balota, con base de datos incluida)"
    )

    assert ms_por_balota < MAXIMO_MS_POR_BALOTA, (
        f"{ms_por_balota:.0f} ms por balota con {CARTONES} cartones. "
        "Algo hizo que la validación de ganadores vuelva a ser cara; mira el "
        "precálculo de máscaras de app/servicios/ganadores.py."
    )


async def test_abrir_una_pantalla_no_reevalua_la_partida(
    cliente: AsyncClient,
) -> None:
    """Consultar el cuadro con 5000 cartones tiene que ser barato.

    En una sala llena son cientos de jugadores abriendo su cartón casi a la vez.
    Lo que lo hace barato es que las máscaras están precalculadas: la segunda
    consulta no vuelve a leer los 5000 cartones ni a rehacer las 50.000 cuentas.
    """
    partida = (await cliente.post("/api/partidas", json={})).json()["id"]

    patron = [[False] * 5 for _ in range(5)]
    for columna in range(5):
        patron[0][columna] = True

    figura = (
        await cliente.post("/api/figuras", json={"nombre": "Línea", "patron": patron})
    ).json()
    await cliente.put(
        f"/api/partidas/{partida}/formas",
        json={"formas": [{"figura_id": figura["id"], "valor_premio": 10000}]},
    )
    await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": CARTONES}
    )

    # La primera paga el precálculo; las siguientes lo reutilizan.
    await cliente.get(f"/api/partidas/{partida}/ganadores")

    inicio = time.perf_counter()
    for _ in range(20):
        respuesta = await cliente.get(f"/api/partidas/{partida}/ganadores")
        assert respuesta.status_code == 200
    ms = (time.perf_counter() - inicio) * 1000 / 20

    print(f"\n  consultar el cuadro con {CARTONES} cartones: {ms:.0f} ms")

    assert ms < MAXIMO_MS_POR_BALOTA
