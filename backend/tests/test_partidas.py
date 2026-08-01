"""Pruebas de partidas y de la selección de formas de ganar."""

from httpx import AsyncClient

Patron = list[list[bool]]


async def _crear_figura(
    cliente: AsyncClient, nombre: str, patron: Patron, tipo: str = "figura"
) -> int:
    """Crea una figura del catálogo y devuelve su id."""
    respuesta = await cliente.post(
        "/api/figuras", json={"nombre": nombre, "patron": patron, "tipo": tipo}
    )
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


async def _crear_partida(cliente: AsyncClient, precio: int = 5000) -> dict:
    respuesta = await cliente.post("/api/partidas", json={"precio_carton": precio})
    assert respuesta.status_code == 201
    return respuesta.json()


# --- Partidas ---------------------------------------------------------------


async def test_no_hay_partidas_al_inicio(cliente: AsyncClient) -> None:
    assert (await cliente.get("/api/partidas")).json() == []


async def test_crear_partida_con_valores_por_defecto(cliente: AsyncClient) -> None:
    partida = (await cliente.post("/api/partidas", json={})).json()

    assert partida["numero_consecutivo"] == 1
    assert partida["estado"] == "pendiente"
    assert partida["precio_carton"] == 0
    assert partida["duracion_segundos_entre_balota"] == 5
    assert partida["figuras"] == []
    assert partida["total_formas"] == 0
    assert partida["premio_total"] == 0


async def test_el_consecutivo_avanza(cliente: AsyncClient) -> None:
    primera = await _crear_partida(cliente)
    segunda = await _crear_partida(cliente)
    tercera = await _crear_partida(cliente)

    assert [primera["numero_consecutivo"], segunda["numero_consecutivo"],
            tercera["numero_consecutivo"]] == [1, 2, 3]


async def test_el_consecutivo_no_se_reutiliza_tras_borrar(
    cliente: AsyncClient,
) -> None:
    """Borrar la última partida no debe hacer que la siguiente repita su número.

    Dos partidas con el mismo "Juego No." serían indistinguibles en los
    reportes y en el historial de ganadores.
    """
    primera = await _crear_partida(cliente)
    segunda = await _crear_partida(cliente)

    await cliente.delete(f"/api/partidas/{segunda['id']}")
    tercera = await _crear_partida(cliente)

    assert primera["numero_consecutivo"] == 1
    assert segunda["numero_consecutivo"] == 2
    assert tercera["numero_consecutivo"] == 3


async def test_actualizar_precio_y_duracion(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    actualizada = (
        await cliente.put(
            f"/api/partidas/{partida['id']}",
            json={"precio_carton": 12000, "duracion_segundos_entre_balota": 8},
        )
    ).json()

    assert actualizada["precio_carton"] == 12000
    assert actualizada["duracion_segundos_entre_balota"] == 8


async def test_rechaza_precio_negativo(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    respuesta = await cliente.put(
        f"/api/partidas/{partida['id']}", json={"precio_carton": -1}
    )

    assert respuesta.status_code == 422


async def test_partida_inexistente_da_404(cliente: AsyncClient) -> None:
    assert (await cliente.get("/api/partidas/9999")).status_code == 404


# --- Selección de formas de ganar -------------------------------------------


async def test_definir_formas(
    cliente: AsyncClient, patron_linea: Patron, patron_esquinas: Patron
) -> None:
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    esquinas = await _crear_figura(cliente, "Esquinas", patron_esquinas)
    partida = await _crear_partida(cliente)

    respuesta = await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={
            "formas": [
                {"figura_id": linea, "valor_premio": 50000},
                {"figura_id": esquinas, "valor_premio": 150000},
            ]
        },
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()
    assert datos["total_formas"] == 2
    assert datos["premio_total"] == 200000

    # El orden de juego sale de la posición en la lista.
    assert [f["orden"] for f in datos["figuras"]] == [1, 2]
    assert datos["figuras"][0]["figura"]["nombre"] == "Línea"
    # El patrón y la categoría viajan completos: el patrón lo necesita el
    # tablero de transmisión, y la categoría, la pantalla de configuración.
    assert datos["figuras"][0]["figura"]["patron"] == patron_linea
    assert datos["figuras"][0]["figura"]["tipo"] == "figura"


async def test_redefinir_reemplaza_la_seleccion_anterior(
    cliente: AsyncClient, patron_linea: Patron, patron_esquinas: Patron
) -> None:
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    esquinas = await _crear_figura(cliente, "Esquinas", patron_esquinas)
    partida = await _crear_partida(cliente)

    await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={"formas": [{"figura_id": linea, "valor_premio": 1000}]},
    )
    datos = (
        await cliente.put(
            f"/api/partidas/{partida['id']}/formas",
            json={"formas": [{"figura_id": esquinas, "valor_premio": 2000}]},
        )
    ).json()

    assert datos["total_formas"] == 1
    assert datos["figuras"][0]["figura"]["nombre"] == "Esquinas"


async def test_redefinir_conservando_las_mismas_figuras(
    cliente: AsyncClient, patron_linea: Patron, patron_esquinas: Patron
) -> None:
    """Reordenar o cambiar un premio deja las mismas figuras seleccionadas.

    Es el caso normal de la pantalla de configuración, y el que choca contra el
    índice único (partida_id, figura_id) si las filas nuevas se insertan antes
    de borrar las viejas.
    """
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    esquinas = await _crear_figura(cliente, "Esquinas", patron_esquinas)
    partida = await _crear_partida(cliente)

    await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={
            "formas": [
                {"figura_id": linea, "valor_premio": 1000},
                {"figura_id": esquinas, "valor_premio": 2000},
            ]
        },
    )

    # Mismas figuras, orden invertido y premios distintos.
    respuesta = await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={
            "formas": [
                {"figura_id": esquinas, "valor_premio": 5000},
                {"figura_id": linea, "valor_premio": 3000},
            ]
        },
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()
    assert datos["total_formas"] == 2
    assert datos["premio_total"] == 8000
    assert [f["figura"]["nombre"] for f in datos["figuras"]] == ["Esquinas", "Línea"]


async def test_redefinir_con_una_sola_figura_repetida(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    """Guardar dos veces seguidas sin cambiar nada no debe fallar."""
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    partida = await _crear_partida(cliente)

    cuerpo = {"formas": [{"figura_id": linea, "valor_premio": 1000}]}
    await cliente.put(f"/api/partidas/{partida['id']}/formas", json=cuerpo)
    respuesta = await cliente.put(f"/api/partidas/{partida['id']}/formas", json=cuerpo)

    assert respuesta.status_code == 200
    assert respuesta.json()["total_formas"] == 1


async def test_el_orden_sigue_la_posicion_en_la_lista(
    cliente: AsyncClient, patron_linea: Patron, patron_esquinas: Patron
) -> None:
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    esquinas = await _crear_figura(cliente, "Esquinas", patron_esquinas)
    partida = await _crear_partida(cliente)

    datos = (
        await cliente.put(
            f"/api/partidas/{partida['id']}/formas",
            json={
                "formas": [
                    {"figura_id": esquinas, "valor_premio": 0},
                    {"figura_id": linea, "valor_premio": 0},
                ]
            },
        )
    ).json()

    assert [f["figura"]["nombre"] for f in datos["figuras"]] == ["Esquinas", "Línea"]
    assert [f["orden"] for f in datos["figuras"]] == [1, 2]


async def test_vaciar_la_seleccion(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    partida = await _crear_partida(cliente)

    await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={"formas": [{"figura_id": linea, "valor_premio": 1000}]},
    )
    datos = (
        await cliente.put(f"/api/partidas/{partida['id']}/formas", json={"formas": []})
    ).json()

    assert datos["total_formas"] == 0


async def test_rechaza_la_misma_figura_dos_veces(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    partida = await _crear_partida(cliente)

    respuesta = await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={
            "formas": [
                {"figura_id": linea, "valor_premio": 1000},
                {"figura_id": linea, "valor_premio": 2000},
            ]
        },
    )

    assert respuesta.status_code == 422


async def test_rechaza_figura_inexistente(cliente: AsyncClient) -> None:
    partida = await _crear_partida(cliente)

    respuesta = await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={"formas": [{"figura_id": 9999, "valor_premio": 0}]},
    )

    assert respuesta.status_code == 404


async def test_una_figura_invalida_no_altera_la_seleccion_previa(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    """Si una figura de la lista no existe, no debe quedar nada a medio guardar."""
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    partida = await _crear_partida(cliente)

    await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={"formas": [{"figura_id": linea, "valor_premio": 7000}]},
    )

    await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={"formas": [{"figura_id": 9999, "valor_premio": 0}]},
    )

    datos = (await cliente.get(f"/api/partidas/{partida['id']}")).json()
    assert datos["total_formas"] == 1
    assert datos["figuras"][0]["valor_premio"] == 7000


async def test_rechaza_premio_negativo(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    partida = await _crear_partida(cliente)

    respuesta = await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={"formas": [{"figura_id": linea, "valor_premio": -100}]},
    )

    assert respuesta.status_code == 422


async def test_la_seleccion_ignora_cualquier_categoria_que_le_manden(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    """La categoría es de la figura, no de la selección.

    Si un cliente viejo enviara `tipo_premio`, debe descartarse en silencio y
    seguir mandando la categoría de la figura del catálogo.
    """
    linea = await _crear_figura(cliente, "Línea", patron_linea, tipo="pleno")
    partida = await _crear_partida(cliente)

    respuesta = await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={
            "formas": [
                {"figura_id": linea, "tipo_premio": "sencillo", "valor_premio": 0}
            ]
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["figuras"][0]["figura"]["tipo"] == "pleno"


# --- Protección del catálogo ------------------------------------------------


async def test_no_se_puede_borrar_una_figura_en_uso(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    """Borrarla dejaría huérfano el historial de ganadores."""
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    partida = await _crear_partida(cliente)

    await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={"formas": [{"figura_id": linea, "valor_premio": 1000}]},
    )

    respuesta = await cliente.delete(f"/api/figuras/{linea}")

    assert respuesta.status_code == 409
    assert "partida" in respuesta.json()["detail"]
    # Y sigue en el catálogo.
    assert (await cliente.get(f"/api/figuras/{linea}")).status_code == 200


async def test_se_puede_borrar_una_figura_tras_quitarla_de_la_partida(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    partida = await _crear_partida(cliente)

    await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={"formas": [{"figura_id": linea, "valor_premio": 1000}]},
    )
    await cliente.put(f"/api/partidas/{partida['id']}/formas", json={"formas": []})

    assert (await cliente.delete(f"/api/figuras/{linea}")).status_code == 204


async def test_borrar_la_partida_no_borra_las_figuras_del_catalogo(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    """El catálogo es global: sobrevive a las partidas que lo usaron."""
    linea = await _crear_figura(cliente, "Línea", patron_linea)
    partida = await _crear_partida(cliente)

    await cliente.put(
        f"/api/partidas/{partida['id']}/formas",
        json={"formas": [{"figura_id": linea, "valor_premio": 1000}]},
    )

    assert (await cliente.delete(f"/api/partidas/{partida['id']}")).status_code == 204
    assert (await cliente.get(f"/api/figuras/{linea}")).status_code == 200
