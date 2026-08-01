"""Pruebas del cuadro de ganadores a través de la API.

Los cartones se insertan a mano con números conocidos: los que genera la API son
aleatorios y no permitirían saber quién debe ganar.

La prueba del sorteo completo **vuelve a calcular los ganadores por su cuenta**, a
partir del orden real en que salieron las balotas, sin usar nada de
`app/dominio/ganadores.py`. Si las dos cuentas coinciden es porque ambas son
correctas, no porque compartan el mismo error.
"""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.dominio.bingo import firma_carton
from app.models.carton import Carton
from app.models.ganador import Ganador

FILA_LIBRE, COLUMNA_LIBRE = 2, 2


def carton_de(numeros: list[int]) -> list[list[int | None]]:
    """Cartón 5x5 con los 24 números dados y la casilla libre en el centro."""
    valores = list(numeros)
    matriz: list[list[int | None]] = []
    for fila in range(5):
        actual: list[int | None] = []
        for columna in range(5):
            if fila == FILA_LIBRE and columna == COLUMNA_LIBRE:
                actual.append(None)
            else:
                actual.append(valores.pop(0))
        matriz.append(actual)
    return matriz


def patron_de(celdas: list[tuple[int, int]]) -> list[list[bool]]:
    patron = [[False] * 5 for _ in range(5)]
    for fila, columna in celdas:
        patron[fila][columna] = True
    return patron


PRIMERA_FILA = patron_de([(0, c) for c in range(5)])
SEGUNDA_FILA = patron_de([(1, c) for c in range(5)])

#: Tres cartones que comparten la primera fila de dos en dos, para poder provocar
#: ganadores simultáneos y ganadores tardíos.
CARTONES = {
    "A-1": carton_de(list(range(1, 25))),
    "A-2": carton_de([1, 2, 3, 4, 5] + list(range(51, 70))),
    "A-3": carton_de(list(range(26, 50))),
}


async def _preparar(
    cliente: AsyncClient, sesion_factory: async_sessionmaker, patrones: dict[str, list]
) -> int:
    """Crea una partida con las formas dadas y los tres cartones conocidos."""
    partida_id = (
        await cliente.post("/api/partidas", json={"precio_carton": 5000})
    ).json()["id"]

    formas = []
    for nombre, patron in patrones.items():
        figura = (
            await cliente.post(
                "/api/figuras", json={"nombre": nombre, "patron": patron}
            )
        ).json()
        formas.append({"figura_id": figura["id"], "valor_premio": 50000})

    respuesta = await cliente.put(
        f"/api/partidas/{partida_id}/formas", json={"formas": formas}
    )
    assert respuesta.status_code == 200, respuesta.text

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

    return partida_id


async def _cantar_numeros(
    sesion_factory: async_sessionmaker, partida_id: int, numeros: list[int]
) -> None:
    """Registra balotas concretas, saltándose el sorteo aleatorio.

    Sirve para comprobar el cuadro en un estado escogido a dedo. El sorteo real
    se prueba aparte, cantando las 75.
    """
    from app.models.balota_cantada import BalotaCantada

    async with sesion_factory() as sesion:
        for orden, numero in enumerate(numeros, start=1):
            sesion.add(
                BalotaCantada(partida_id=partida_id, numero=numero, orden=orden)
            )
        await sesion.commit()


async def _cantar_hasta_el_primer_bingo(
    cliente: AsyncClient, partida_id: int
) -> dict:
    """Canta balotas hasta que alguien gana y devuelve el cuadro en ese momento.

    Deja la partida **en curso**, no finalizada: es el estado en que el
    administrador ve realmente el aviso.
    """
    for _ in range(75):
        await cliente.post(f"/api/partidas/{partida_id}/balotas")
        cuadro = (await cliente.get(f"/api/partidas/{partida_id}/ganadores")).json()
        if cuadro["bingos"]:
            return cuadro

    raise AssertionError("Nadie ganó en 75 balotas.")


# --- Consulta del cuadro -----------------------------------------------------


async def test_partida_recien_creada_no_tiene_nada(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    partida = await _preparar(cliente, sesion_factory, {"Línea": PRIMERA_FILA})

    cuadro = (await cliente.get(f"/api/partidas/{partida}/ganadores")).json()

    assert cuadro["tipo"] == "ganadores"
    assert cuadro["bingos"] == []
    assert cuadro["cerca"] == []
    assert cuadro["a_una"] == 0 and cuadro["a_dos"] == 0
    assert cuadro["orden_balota"] == 0


async def test_el_cuadro_avisa_de_quien_esta_a_una_y_a_dos(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    partida = await _preparar(
        cliente, sesion_factory, {"Línea": PRIMERA_FILA, "Segunda": SEGUNDA_FILA}
    )
    # A-1 y A-2 necesitan 1..5 para «Línea»: les falta el 5.
    # A-1 necesita 6..10 para «Segunda»: le faltan el 9 y el 10.
    await _cantar_numeros(sesion_factory, partida, [1, 2, 3, 4, 6, 7, 8])

    cuadro = (await cliente.get(f"/api/partidas/{partida}/ganadores")).json()

    assert cuadro["a_una"] == 2
    assert cuadro["a_dos"] == 1
    assert cuadro["bingos"] == []

    a_una = [c for c in cuadro["cerca"] if c["faltan"] == 1]
    assert {c["codigo"] for c in a_una} == {"A-1", "A-2"}
    assert all(c["numeros"] == [5] for c in a_una)


async def test_consultar_el_cuadro_no_registra_ganadores(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    """Abrir una pantalla no puede declarar ganadores; eso pasa al cantar."""
    partida = await _preparar(cliente, sesion_factory, {"Línea": PRIMERA_FILA})
    await _cantar_numeros(sesion_factory, partida, [1, 2, 3, 4, 5])

    cuadro = (await cliente.get(f"/api/partidas/{partida}/ganadores")).json()
    assert cuadro["total_cartones_ganadores"] == 2, "sí los muestra"

    async with sesion_factory() as sesion:
        guardados = (await sesion.execute(select(Ganador))).scalars().all()
    assert guardados == [], "pero no los guarda"


async def test_el_cuadro_de_una_partida_inexistente_da_404(
    cliente: AsyncClient,
) -> None:
    assert (await cliente.get("/api/partidas/9999/ganadores")).status_code == 404


# --- Registro durante el sorteo ----------------------------------------------


def _ganadores_esperados(
    orden_balotas: list[int], patron: list[list[bool]]
) -> tuple[int, list[str]]:
    """Recalcula, sin usar el dominio, en qué balota se gana una forma y quién gana.

    Recorre el sorteo balota a balota y se detiene en la primera en que algún
    cartón tiene todos los números que la figura le exige. Devuelve esa posición
    y los códigos de todos los cartones que la completaron en ella —que son los
    que comparten premio.
    """
    exigidos = {
        codigo: {
            matriz[f][c]
            for f in range(5)
            for c in range(5)
            if patron[f][c] and matriz[f][c] is not None
        }
        for codigo, matriz in CARTONES.items()
    }

    salidas: set[int] = set()
    for posicion, numero in enumerate(orden_balotas, start=1):
        salidas.add(numero)
        completos = sorted(c for c, nums in exigidos.items() if nums <= salidas)
        if completos:
            return posicion, completos

    return 0, []


async def test_un_sorteo_completo_registra_exactamente_los_ganadores_correctos(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    partida = await _preparar(
        cliente, sesion_factory, {"Línea": PRIMERA_FILA, "Segunda": SEGUNDA_FILA}
    )
    await cliente.post(f"/api/partidas/{partida}/iniciar")

    for _ in range(75):
        await cliente.post(f"/api/partidas/{partida}/balotas")

    balotas = (await cliente.get(f"/api/partidas/{partida}/balotas")).json()
    orden_balotas = [b["numero"] for b in balotas]

    cuadro = (await cliente.get(f"/api/partidas/{partida}/ganadores")).json()
    por_figura = {b["figura"]: b for b in cuadro["bingos"]}

    for nombre, patron in (("Línea", PRIMERA_FILA), ("Segunda", SEGUNDA_FILA)):
        posicion, codigos = _ganadores_esperados(orden_balotas, patron)

        bingo = por_figura[nombre]
        assert sorted(c["codigo"] for c in bingo["cartones"]) == codigos, nombre
        assert bingo["orden_balota"] == posicion, nombre
        assert bingo["numero_balota"] == orden_balotas[posicion - 1], nombre

    # Con las 75 fuera ya no queda nadie «cerca»: todo está ganado.
    assert cuadro["cerca"] == []


async def test_cantar_no_registra_dos_veces_al_mismo_ganador(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    """La evaluación corre en CADA balota; sin cuidado, un ganador se repetiría."""
    partida = await _preparar(cliente, sesion_factory, {"Línea": PRIMERA_FILA})
    await cliente.post(f"/api/partidas/{partida}/iniciar")

    for _ in range(75):
        await cliente.post(f"/api/partidas/{partida}/balotas")

    async with sesion_factory() as sesion:
        guardados = (await sesion.execute(select(Ganador))).scalars().all()

    claves = [(g.carton_id, g.partida_figura_id) for g in guardados]
    assert len(claves) == len(set(claves)), "hay ganadores repetidos"


async def test_quien_completa_una_forma_mas_tarde_no_se_registra(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    """A-3 tiene una primera fila distinta, así que gana «Línea» después que A-1 y A-2."""
    partida = await _preparar(cliente, sesion_factory, {"Línea": PRIMERA_FILA})
    await cliente.post(f"/api/partidas/{partida}/iniciar")

    for _ in range(75):
        await cliente.post(f"/api/partidas/{partida}/balotas")

    balotas = (await cliente.get(f"/api/partidas/{partida}/balotas")).json()
    posicion, codigos = _ganadores_esperados(
        [b["numero"] for b in balotas], PRIMERA_FILA
    )

    cuadro = (await cliente.get(f"/api/partidas/{partida}/ganadores")).json()
    registrados = sorted(c["codigo"] for c in cuadro["bingos"][0]["cartones"])

    assert registrados == codigos
    assert len(registrados) < 3, (
        "los tres cartones completan la línea antes de la balota 75; "
        "solo deben quedar los de la primera"
    )


async def test_un_bingo_no_detiene_el_sorteo(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    """Decisión del proyecto: se avisa y la partida sigue.

    Todas las formas juegan a la vez, así que un bingo de «línea» no debe frenar
    una partida en la que «cartón lleno» sigue en juego. Finalizar es decisión
    del administrador.
    """
    partida = await _preparar(
        cliente, sesion_factory, {"Línea": PRIMERA_FILA, "Segunda": SEGUNDA_FILA}
    )
    await cliente.post(f"/api/partidas/{partida}/iniciar")
    await _cantar_hasta_el_primer_bingo(cliente, partida)

    sorteo = (await cliente.get(f"/api/partidas/{partida}/sorteo")).json()
    assert sorteo["estado"] == "en_curso"

    # Y se puede seguir cantando con normalidad.
    assert (await cliente.post(f"/api/partidas/{partida}/balotas")).status_code == 201


async def test_consultar_el_cuadro_nunca_dice_que_un_bingo_es_nuevo(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    """`nuevo` significa «detectado en esta evaluación», no «reciente».

    Es lo que hace que la pantalla haga ruido una sola vez. Una consulta llega
    siempre después de que el ganador quedó registrado, así que para ella el
    bingo nunca es nuevo — el aviso fresco viaja por el WebSocket, y eso se
    comprueba en `test_ganadores_ws.py`.
    """
    partida = await _preparar(cliente, sesion_factory, {"Línea": PRIMERA_FILA})
    await cliente.post(f"/api/partidas/{partida}/iniciar")

    cuadro = await _cantar_hasta_el_primer_bingo(cliente, partida)
    assert cuadro["bingos"][0]["nuevo"] is False

    orden = cuadro["bingos"][0]["orden_balota"]
    await cliente.post(f"/api/partidas/{partida}/balotas")
    despues = (await cliente.get(f"/api/partidas/{partida}/ganadores")).json()

    assert despues["bingos"][0]["orden_balota"] == orden, (
        "la balota con la que se ganó no debe moverse al avanzar el sorteo"
    )


async def test_reiniciar_el_sorteo_borra_los_ganadores(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    """Si quedaran, sus formas seguirían cerradas y nadie podría volver a ganarlas."""
    partida = await _preparar(cliente, sesion_factory, {"Línea": PRIMERA_FILA})
    await cliente.post(f"/api/partidas/{partida}/iniciar")
    for _ in range(75):
        await cliente.post(f"/api/partidas/{partida}/balotas")

    assert (await cliente.get(f"/api/partidas/{partida}/ganadores")).json()["bingos"]

    await cliente.delete(f"/api/partidas/{partida}/balotas")

    cuadro = (await cliente.get(f"/api/partidas/{partida}/ganadores")).json()
    assert cuadro["bingos"] == []

    async with sesion_factory() as sesion:
        assert (await sesion.execute(select(Ganador))).scalars().all() == []


# --- Protección de la selección de formas ------------------------------------


async def test_no_se_pueden_cambiar_las_formas_con_ganadores_registrados(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    """Reemplazarlas borraría los ganadores en cascada y en silencio."""
    partida = await _preparar(cliente, sesion_factory, {"Línea": PRIMERA_FILA})
    await cliente.post(f"/api/partidas/{partida}/iniciar")
    await _cantar_hasta_el_primer_bingo(cliente, partida)

    figura = (
        await cliente.post(
            "/api/figuras", json={"nombre": "Otra", "patron": SEGUNDA_FILA}
        )
    ).json()

    respuesta = await cliente.put(
        f"/api/partidas/{partida}/formas",
        json={"formas": [{"figura_id": figura["id"], "valor_premio": 1000}]},
    )

    assert respuesta.status_code == 409
    assert "ganadores" in respuesta.json()["detail"]

    # Y los ganadores siguen ahí.
    async with sesion_factory() as sesion:
        assert (await sesion.execute(select(Ganador))).scalars().all()


async def test_sin_ganadores_las_formas_se_pueden_cambiar(
    cliente: AsyncClient, sesion_factory: async_sessionmaker
) -> None:
    """La protección no debe estorbar mientras no haya nada que proteger."""
    partida = await _preparar(cliente, sesion_factory, {"Línea": PRIMERA_FILA})

    figura = (
        await cliente.post(
            "/api/figuras", json={"nombre": "Otra", "patron": SEGUNDA_FILA}
        )
    ).json()

    respuesta = await cliente.put(
        f"/api/partidas/{partida}/formas",
        json={"formas": [{"figura_id": figura["id"], "valor_premio": 1000}]},
    )

    assert respuesta.status_code == 200
