"""Pruebas del sorteo de balotas.

Las reglas del bingo de 75 bolas se prueban directamente sobre el dominio, sin
pasar por la API ni la base de datos.
"""

import pytest

from app.dominio.bingo import (
    TOTAL_BALOTAS,
    SinBalotasDisponibles,
    letra_de_numero,
    sortear_balota,
)


def test_la_balota_esta_en_rango() -> None:
    for _ in range(200):
        numero = sortear_balota(set())
        assert 1 <= numero <= TOTAL_BALOTAS


def test_nunca_devuelve_una_ya_cantada() -> None:
    """El sorteo es sin reemplazo: la regla central de la balotera."""
    cantadas = set(range(1, 75))  # quedan solo la 75

    for _ in range(50):
        assert sortear_balota(cantadas) == 75


def test_un_sorteo_completo_saca_las_75_sin_repetir() -> None:
    """Simula una partida entera, que es el caso que importa de verdad."""
    cantadas: set[int] = set()
    secuencia: list[int] = []

    for _ in range(TOTAL_BALOTAS):
        numero = sortear_balota(cantadas)
        assert numero not in cantadas
        cantadas.add(numero)
        secuencia.append(numero)

    assert len(secuencia) == TOTAL_BALOTAS
    assert sorted(secuencia) == list(range(1, TOTAL_BALOTAS + 1))


def test_al_agotarse_las_balotas_falla() -> None:
    with pytest.raises(SinBalotasDisponibles):
        sortear_balota(set(range(1, TOTAL_BALOTAS + 1)))


def test_el_orden_de_salida_varia_entre_partidas() -> None:
    """Dos sorteos completos idénticos serían señal de que algo está fijo."""

    def sorteo_completo() -> list[int]:
        cantadas: set[int] = set()
        salida: list[int] = []
        for _ in range(TOTAL_BALOTAS):
            numero = sortear_balota(cantadas)
            cantadas.add(numero)
            salida.append(numero)
        return salida

    assert sorteo_completo() != sorteo_completo()


def test_todas_las_letras_aparecen_en_un_sorteo_completo() -> None:
    cantadas: set[int] = set()
    letras: set[str] = set()

    for _ in range(TOTAL_BALOTAS):
        numero = sortear_balota(cantadas)
        cantadas.add(numero)
        letras.add(letra_de_numero(numero))

    assert letras == {"B", "I", "N", "G", "O"}
