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
    partida = await _crear_partida(cliente)

    respuesta = await cliente.post(
        f"/api/partidas/{partida}/cartones", json={"cantidad": 10}
    )

    assert respuesta.status_code == 201

    cartones = respuesta.json()
    assert len(cartones) == 10
    assert [c["numero_carton"] for c in cartones] == list(range(1, 11))
    assert all(c["serie"] == "A" for c in cartones)


async def test_los_cartones_generados_son_validos(cliente: AsyncClient) -> None:
    """Lo que llega por la API debe cumplir las reglas del bingo de 75 bolas."""
    partida = await _crear_partida(cliente)

    cartones = (
        await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 25})
    ).json()

    for carton in cartones:
        validar_carton(carton["numeros"])


async def test_los_cartones_de_una_partida_no_se_repiten(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    cartones = (
        await cliente.post(f"/api/partidas/{partida}/cartones", json={"cantidad": 50})
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

    assert [c["numero_carton"] for c in segunda] == [6, 7, 8]

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

    assert [c["numero_carton"] for c in serie_b] == [1, 2, 3]

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
