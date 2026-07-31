"""Pruebas del algoritmo de generación de cartones.

Aquí viven las reglas del bingo de 75 bolas que no se negocian, así que se
prueban directamente sobre el dominio, sin pasar por la API ni la base de datos.
"""

import inspect

import pytest

from app.dominio import bingo
from app.dominio.bingo import (
    COLUMNA_LIBRE,
    FILA_LIBRE,
    LETRAS,
    RANGOS_POR_COLUMNA,
    TAMANO_CUADRICULA,
    firma_carton,
    generar_carton,
    letra_de_numero,
    validar_carton,
)

#: Cuántos cartones se generan en las pruebas estadísticas. Suficiente para que
#: cualquier sesgo sistemático del algoritmo salte, sin volver lenta la suite.
MUESTRA = 200


def test_el_carton_es_de_5x5() -> None:
    carton = generar_carton()

    assert len(carton) == TAMANO_CUADRICULA
    assert all(len(fila) == TAMANO_CUADRICULA for fila in carton)


def test_el_centro_es_la_casilla_libre() -> None:
    for _ in range(MUESTRA):
        carton = generar_carton()
        assert carton[FILA_LIBRE][COLUMNA_LIBRE] is None


def test_solo_el_centro_esta_vacio() -> None:
    for _ in range(MUESTRA):
        carton = generar_carton()
        vacias = [
            (f, c)
            for f, fila in enumerate(carton)
            for c, valor in enumerate(fila)
            if valor is None
        ]
        assert vacias == [(FILA_LIBRE, COLUMNA_LIBRE)]


def test_cada_columna_respeta_su_rango() -> None:
    """B 1–15, I 16–30, N 31–45, G 46–60, O 61–75."""
    for _ in range(MUESTRA):
        carton = generar_carton()
        for columna, (desde, hasta) in enumerate(RANGOS_POR_COLUMNA):
            for fila in range(TAMANO_CUADRICULA):
                valor = carton[fila][columna]
                if valor is None:
                    continue
                assert desde <= valor <= hasta, (
                    f"{valor} apareció en la columna {LETRAS[columna]} "
                    f"({desde}–{hasta})"
                )


def test_no_hay_numeros_repetidos_en_un_carton() -> None:
    for _ in range(MUESTRA):
        carton = generar_carton()
        numeros = [v for fila in carton for v in fila if v is not None]

        assert len(numeros) == len(set(numeros))
        # 25 celdas menos la casilla libre.
        assert len(numeros) == TAMANO_CUADRICULA**2 - 1


def test_los_cartones_generados_son_validos() -> None:
    for _ in range(MUESTRA):
        validar_carton(generar_carton())


def test_los_cartones_no_se_repiten_entre_si() -> None:
    """Con más de 5·10^26 combinaciones, dos cartones iguales seguidos serían
    señal de que el generador está roto, no mala suerte."""
    firmas = {firma_carton(generar_carton()) for _ in range(MUESTRA)}

    assert len(firmas) == MUESTRA


def test_se_usan_todos_los_numeros_del_rango_a_la_larga() -> None:
    """Ningún número debe quedar sistemáticamente fuera.

    Detectaría un error clásico de rango: usar `range(desde, hasta)` y perder
    siempre el último número de cada columna (15, 30, 45, 60, 75).
    """
    vistos: set[int] = set()
    for _ in range(MUESTRA):
        vistos.update(v for fila in generar_carton() for v in fila if v is not None)

    assert vistos == set(range(1, 76))


def test_la_firma_depende_de_la_posicion() -> None:
    """Los mismos números colocados distinto son cartones distintos."""
    carton = generar_carton()

    intercambiado = [list(fila) for fila in carton]
    intercambiado[0][0], intercambiado[1][0] = intercambiado[1][0], intercambiado[0][0]

    assert firma_carton(carton) != firma_carton(intercambiado)


def test_la_firma_es_estable() -> None:
    carton = generar_carton()

    assert firma_carton(carton) == firma_carton([list(fila) for fila in carton])


def test_letra_de_numero() -> None:
    assert letra_de_numero(1) == "B"
    assert letra_de_numero(15) == "B"
    assert letra_de_numero(16) == "I"
    assert letra_de_numero(31) == "N"
    assert letra_de_numero(46) == "G"
    assert letra_de_numero(61) == "O"
    assert letra_de_numero(75) == "O"


@pytest.mark.parametrize("fuera", [0, 76, -1, 100])
def test_letra_de_numero_rechaza_fuera_de_rango(fuera: int) -> None:
    with pytest.raises(ValueError):
        letra_de_numero(fuera)


def test_se_usa_secrets_y_no_random() -> None:
    """Requisito de diseño del proyecto, de cara a una futura certificación GNA.

    Se comprueba sobre el código fuente porque un `random` colado no rompería
    ninguna otra prueba: los cartones seguirían pareciendo correctos.
    """
    codigo = inspect.getsource(bingo)

    assert "secrets" in codigo
    assert "import random" not in codigo
    assert "random." not in codigo


# --- validar_carton rechaza cartones mal formados ---------------------------


def test_validar_rechaza_centro_con_numero() -> None:
    carton = generar_carton()
    carton[FILA_LIBRE][COLUMNA_LIBRE] = 33

    with pytest.raises(ValueError, match="casilla libre"):
        validar_carton(carton)


def test_validar_rechaza_numero_en_columna_equivocada() -> None:
    carton = generar_carton()
    carton[0][0] = 70  # un número de la O en la columna B

    with pytest.raises(ValueError, match="columna B"):
        validar_carton(carton)


def test_validar_rechaza_numero_repetido() -> None:
    carton = generar_carton()
    carton[1][0] = carton[0][0]

    with pytest.raises(ValueError, match="repetido"):
        validar_carton(carton)


def test_validar_rechaza_cuadricula_de_otro_tamano() -> None:
    with pytest.raises(ValueError, match="filas"):
        validar_carton([[1] * 5] * 4)
