"""Pruebas del catálogo de figuras (formas de ganar)."""

from httpx import AsyncClient

Patron = list[list[bool]]


async def test_catalogo_arranca_vacio(cliente: AsyncClient) -> None:
    respuesta = await cliente.get("/api/figuras")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


async def test_crear_figura(cliente: AsyncClient, patron_linea: Patron) -> None:
    respuesta = await cliente.post(
        "/api/figuras", json={"nombre": "Línea horizontal", "patron": patron_linea}
    )

    assert respuesta.status_code == 201

    figura = respuesta.json()
    assert figura["id"] > 0
    assert figura["nombre"] == "Línea horizontal"
    assert figura["patron"] == patron_linea
    assert figura["celdas_marcadas"] == 5


async def test_crear_recorta_espacios_del_nombre(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    respuesta = await cliente.post(
        "/api/figuras", json={"nombre": "  Equis  ", "patron": patron_linea}
    )

    assert respuesta.json()["nombre"] == "Equis"


async def test_listar_devuelve_las_creadas(
    cliente: AsyncClient, patron_linea: Patron, patron_esquinas: Patron
) -> None:
    await cliente.post("/api/figuras", json={"nombre": "Línea", "patron": patron_linea})
    await cliente.post(
        "/api/figuras", json={"nombre": "Esquinas", "patron": patron_esquinas}
    )

    figuras = (await cliente.get("/api/figuras")).json()

    assert len(figuras) == 2
    assert {f["nombre"] for f in figuras} == {"Línea", "Esquinas"}


async def test_obtener_por_id(cliente: AsyncClient, patron_esquinas: Patron) -> None:
    creada = (
        await cliente.post(
            "/api/figuras", json={"nombre": "Esquinas", "patron": patron_esquinas}
        )
    ).json()

    respuesta = await cliente.get(f"/api/figuras/{creada['id']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["celdas_marcadas"] == 4


async def test_actualizar_nombre_y_patron(
    cliente: AsyncClient, patron_linea: Patron, patron_esquinas: Patron
) -> None:
    creada = (
        await cliente.post(
            "/api/figuras", json={"nombre": "Provisional", "patron": patron_linea}
        )
    ).json()

    respuesta = await cliente.put(
        f"/api/figuras/{creada['id']}",
        json={"nombre": "Cuatro esquinas", "patron": patron_esquinas},
    )

    assert respuesta.status_code == 200

    actualizada = respuesta.json()
    assert actualizada["nombre"] == "Cuatro esquinas"
    assert actualizada["patron"] == patron_esquinas
    assert actualizada["celdas_marcadas"] == 4


async def test_actualizar_solo_el_nombre_conserva_el_patron(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    creada = (
        await cliente.post(
            "/api/figuras", json={"nombre": "Línea", "patron": patron_linea}
        )
    ).json()

    actualizada = (
        await cliente.put(f"/api/figuras/{creada['id']}", json={"nombre": "Línea arriba"})
    ).json()

    assert actualizada["nombre"] == "Línea arriba"
    assert actualizada["patron"] == patron_linea


async def test_eliminar_figura(cliente: AsyncClient, patron_linea: Patron) -> None:
    creada = (
        await cliente.post(
            "/api/figuras", json={"nombre": "Desechable", "patron": patron_linea}
        )
    ).json()

    assert (await cliente.delete(f"/api/figuras/{creada['id']}")).status_code == 204
    assert (await cliente.get(f"/api/figuras/{creada['id']}")).status_code == 404
    assert (await cliente.get("/api/figuras")).json() == []


# --- Reglas de validación ---------------------------------------------------


async def test_rechaza_nombre_duplicado(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    await cliente.post("/api/figuras", json={"nombre": "Línea", "patron": patron_linea})

    respuesta = await cliente.post(
        "/api/figuras", json={"nombre": "Línea", "patron": patron_linea}
    )

    assert respuesta.status_code == 409


async def test_el_duplicado_ignora_mayusculas(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    """"Línea" y "LÍNEA" son la misma figura: el catálogo no debe duplicarse."""
    await cliente.post("/api/figuras", json={"nombre": "Línea", "patron": patron_linea})

    respuesta = await cliente.post(
        "/api/figuras", json={"nombre": "LÍNEA", "patron": patron_linea}
    )

    assert respuesta.status_code == 409


async def test_renombrar_a_si_misma_no_es_conflicto(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    """Guardar sin cambiar el nombre no debe chocar contra su propio registro."""
    creada = (
        await cliente.post(
            "/api/figuras", json={"nombre": "Línea", "patron": patron_linea}
        )
    ).json()

    respuesta = await cliente.put(
        f"/api/figuras/{creada['id']}", json={"nombre": "Línea"}
    )

    assert respuesta.status_code == 200


async def test_rechaza_patron_con_filas_de_mas(cliente: AsyncClient) -> None:
    patron_6_filas = [[False] * 5 for _ in range(6)]
    patron_6_filas[0][0] = True

    respuesta = await cliente.post(
        "/api/figuras", json={"nombre": "Torcida", "patron": patron_6_filas}
    )

    assert respuesta.status_code == 422


async def test_rechaza_patron_con_columnas_de_menos(cliente: AsyncClient) -> None:
    patron = [[False] * 5 for _ in range(5)]
    patron[2] = [True, False, False]  # fila de 3 columnas

    respuesta = await cliente.post(
        "/api/figuras", json={"nombre": "Torcida", "patron": patron}
    )

    assert respuesta.status_code == 422


async def test_rechaza_figura_sin_celdas(cliente: AsyncClient) -> None:
    """Una figura vacía no es una forma de ganar: nadie podría cumplirla."""
    respuesta = await cliente.post(
        "/api/figuras",
        json={"nombre": "Vacía", "patron": [[False] * 5 for _ in range(5)]},
    )

    assert respuesta.status_code == 422


async def test_rechaza_nombre_en_blanco(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    respuesta = await cliente.post(
        "/api/figuras", json={"nombre": "   ", "patron": patron_linea}
    )

    assert respuesta.status_code == 422


async def test_actualizar_inexistente_da_404(
    cliente: AsyncClient, patron_linea: Patron
) -> None:
    respuesta = await cliente.put("/api/figuras/9999", json={"nombre": "Fantasma"})

    assert respuesta.status_code == 404


async def test_eliminar_inexistente_da_404(cliente: AsyncClient) -> None:
    assert (await cliente.delete("/api/figuras/9999")).status_code == 404
