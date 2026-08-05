"""Pruebas de los endpoints de cartones."""

from httpx import AsyncClient

from app.dominio.bingo import firma_carton, validar_carton


async def _crear_partida(cliente: AsyncClient) -> int:
    respuesta = await cliente.post("/api/partidas", json={"precio_carton": 5000})
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


async def test_una_partida_nueva_no_tiene_cartones(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    assert (await cliente.get(f"/api/partidas/{partida}/cartones")).json() == []

    resumen = (await cliente.get(f"/api/partidas/{partida}/cartones/resumen")).json()
    assert resumen == {"total": 0, "por_serie": {}}


async def test_generar_cartones(cliente: AsyncClient) -> None:
    """La generación responde con el resumen de la tanda, no con los cartones.

    Con 5000 cartones la lista completa serían varios megabytes que la pantalla
    ni mira: recarga la primera página aparte.
    """
    partida = await _crear_partida(cliente)

    respuesta = await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 10}
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "cantidad": 10,
        "serie": "A",
        "desde": 1,
        "hasta": 10,
        "total_en_partida": 10,
    }

    cartones = (await cliente.get(f"/api/partidas/{partida}/cartones")).json()
    assert [c["numero_carton"] for c in cartones] == list(range(1, 11))
    assert all(c["serie"] == "A" for c in cartones)


async def test_los_cartones_generados_son_validos(cliente: AsyncClient) -> None:
    """Lo que llega por la API debe cumplir las reglas del bingo de 75 bolas."""
    partida = await _crear_partida(cliente)

    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 25})
    cartones = (await cliente.get(f"/api/partidas/{partida}/cartones")).json()

    assert len(cartones) == 25
    for carton in cartones:
        validar_carton(carton["numeros"])


async def test_los_cartones_de_una_partida_no_se_repiten(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 50})
    cartones = (
        await cliente.get(
            f"/api/partidas/{partida}/cartones", params={"limite": 50}
        )
    ).json()

    firmas = {firma_carton(c["numeros"]) for c in cartones}
    assert len(firmas) == 50


async def test_el_consecutivo_continua_entre_tandas(cliente: AsyncClient) -> None:
    """Generar de a poco no debe reiniciar la numeración ni pisar cartones."""
    partida = await _crear_partida(cliente)

    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 5})
    segunda = (
        await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 3})
    ).json()

    assert (segunda["desde"], segunda["hasta"]) == (6, 8)
    assert segunda["total_en_partida"] == 8

    resumen = (await cliente.get(f"/api/partidas/{partida}/cartones/resumen")).json()
    assert resumen["total"] == 8


async def test_las_series_llevan_consecutivos_independientes(
    cliente: AsyncClient,
) -> None:
    partida = await _crear_partida(cliente)

    await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 4, "serie": "A"}
    )
    serie_b = (
        await cliente.post(
            f"/api/partidas/{partida}/cartones", json={"cantidad": 3, "serie": "B"}
        )
    ).json()

    # La serie B empieza en 1 aunque la A ya tenga cuatro.
    assert (serie_b["serie"], serie_b["desde"], serie_b["hasta"]) == ("B", 1, 3)

    resumen = (await cliente.get(f"/api/partidas/{partida}/cartones/resumen")).json()
    assert resumen == {"total": 7, "por_serie": {"A": 4, "B": 3}}


async def test_filtrar_por_serie(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 4, "serie": "A"}
    )
    await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 2, "serie": "B"}
    )

    solo_b = (
        await cliente.get(f"/api/partidas/{partida}/cartones", params={"serie": "B"})
    ).json()

    assert len(solo_b) == 2
    assert all(c["serie"] == "B" for c in solo_b)


async def test_paginacion(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)
    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 12})

    pagina = (
        await cliente.get(
            f"/api/partidas/{partida}/cartones",
            params={"limite": 5, "desplazamiento": 5},
        )
    ).json()

    assert [c["numero_carton"] for c in pagina] == [6, 7, 8, 9, 10]


async def test_eliminar_todos_los_cartones(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)
    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 5})

    assert (await cliente.delete(f"/api/partidas/{partida}/cartones")).status_code == 204
    assert (await cliente.get(f"/api/partidas/{partida}/cartones")).json() == []


async def test_eliminar_solo_una_serie(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)
    await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 3, "serie": "A"}
    )
    await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 2, "serie": "B"}
    )

    await cliente.delete(
        f"/api/partidas/{partida}/cartones", params={"serie": "B"}
    )

    resumen = (await cliente.get(f"/api/partidas/{partida}/cartones/resumen")).json()
    assert resumen == {"total": 3, "por_serie": {"A": 3}}


async def test_borrar_la_partida_borra_sus_cartones(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)
    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 3})

    assert (await cliente.delete(f"/api/partidas/{partida}")).status_code == 204
    assert (await cliente.get(f"/api/partidas/{partida}/cartones")).status_code == 404


# --- Buscar un cartón por su código -----------------------------------------


async def test_obtener_carton_por_codigo(cliente: AsyncClient) -> None:
    """Es como el jugador llega a su cartón: escribiendo el código que tiene."""
    partida = await _crear_partida(cliente)
    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 5})
    creados = (await cliente.get(f"/api/partidas/{partida}/cartones")).json()
    tercero = creados[2]

    respuesta = await cliente.get(f"/api/partidas/{partida}/cartones/A/3")

    assert respuesta.status_code == 200

    carton = respuesta.json()
    assert carton["numero_carton"] == 3
    assert carton["serie"] == "A"
    assert carton["numeros"] == tercero["numeros"]


async def test_el_codigo_ignora_mayusculas(cliente: AsyncClient) -> None:
    """Escrito desde un celular, «a-7» debe funcionar igual que «A-7»."""
    partida = await _crear_partida(cliente)
    await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 3, "serie": "B"}
    )

    respuesta = await cliente.get(f"/api/partidas/{partida}/cartones/b/2")

    assert respuesta.status_code == 200
    assert respuesta.json()["numero_carton"] == 2


async def test_carton_inexistente_da_404(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)
    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 3})

    assert (await cliente.get(f"/api/partidas/{partida}/cartones/A/99")).status_code == 404
    assert (await cliente.get(f"/api/partidas/{partida}/cartones/Z/1")).status_code == 404


async def test_el_codigo_no_cruza_partidas(cliente: AsyncClient) -> None:
    """El A-1 de una partida no es el A-1 de otra."""
    primera = await _crear_partida(cliente)
    segunda = await _crear_partida(cliente)
    await cliente.post(f"/api/partidas/{primera}/cartones", json={"cantidad": 2})

    assert (await cliente.get(f"/api/partidas/{segunda}/cartones/A/1")).status_code == 404


async def test_resumen_no_choca_con_el_codigo(cliente: AsyncClient) -> None:
    """`/resumen` es una ruta, no una serie llamada «resumen»."""
    partida = await _crear_partida(cliente)
    await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 2})

    respuesta = await cliente.get(f"/api/partidas/{partida}/cartones/resumen")

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 2


# --- Validaciones -----------------------------------------------------------


async def test_rechaza_cantidad_cero(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    respuesta = await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 0}
    )

    assert respuesta.status_code == 422


async def test_rechaza_cantidad_desmedida(cliente: AsyncClient) -> None:
    """Un número absurdo llenaría la base sin querer."""
    partida = await _crear_partida(cliente)

    respuesta = await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 100_000}
    )

    assert respuesta.status_code == 422


async def test_partida_inexistente_da_404(cliente: AsyncClient) -> None:
    respuesta = await cliente.post("/api/partidas/9999/cartones", json={"cantidad": 1})

    assert respuesta.status_code == 404
