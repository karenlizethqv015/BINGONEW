"""Pruebas de las reglas de ganadores, sin base de datos.

Los cartones y los patrones se arman a mano y se comprueba el resultado contra
la cuenta hecha aparte. Es la única forma de comprobar de verdad estas reglas:
con cartones generados al azar habría que reimplementar la misma lógica para
saber qué esperar, y entonces la prueba solo diría que el código está de acuerdo
consigo mismo.
"""

from app.dominio.bingo import (
    FILA_LIBRE,
    COLUMNA_LIBRE,
    faltan_para,
    numeros_requeridos,
    patron_vacio,
)
from app.dominio.ganadores import (
    CartonEnJuego,
    FormaEnJuego,
    GanadorRegistrado,
    MAXIMO_CERCA,
    evaluar,
)


def carton_de(numeros: list[int]) -> list[list[int | None]]:
    """Cartón 5x5 con los 24 números dados, en orden de lectura, y libre al centro."""
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


#: Cartón cómodo de leer: 1..12 arriba de la libre, 13..24 debajo.
CARTON_A = carton_de(list(range(1, 25)))

#: Otro cartón que comparte la primera fila con el A, para probar ganadores
#: simultáneos, y difiere en el resto.
CARTON_B = carton_de([1, 2, 3, 4, 5] + list(range(51, 70)))


def patron_de(celdas: list[tuple[int, int]]) -> list[list[bool]]:
    patron = patron_vacio()
    for fila, columna in celdas:
        patron[fila][columna] = True
    return patron


#: Primera fila: exige los números 1, 2, 3, 4 y 5 en ambos cartones.
PRIMERA_FILA = patron_de([(0, c) for c in range(5)])


def forma(
    id_: int = 1, nombre: str = "Línea", patron=None, premio: int = 10000, orden: int = 1
) -> FormaEnJuego:
    return FormaEnJuego(
        partida_figura_id=id_,
        figura_id=id_ * 10,
        nombre=nombre,
        patron=patron if patron is not None else PRIMERA_FILA,
        valor_premio=premio,
        orden=orden,
    )


def en_juego(id_: int, matriz, codigo: str | None = None) -> CartonEnJuego:
    return CartonEnJuego(id=id_, codigo=codigo or f"A-{id_}", numeros=matriz)


# --- Números que exige una figura sobre un cartón ---------------------------


def test_los_numeros_requeridos_son_los_del_patron() -> None:
    assert numeros_requeridos(CARTON_A, PRIMERA_FILA) == {1, 2, 3, 4, 5}


def test_la_casilla_libre_no_exige_ninguna_balota() -> None:
    """Una figura que incluye el centro exige una balota MENOS que celdas tiene."""
    cruz = patron_de([(2, 0), (2, 1), (2, 2), (2, 3), (2, 4)])

    requeridos = numeros_requeridos(CARTON_A, cruz)

    assert len(requeridos) == 4, "el centro no debe aportar ningún número"
    assert None not in requeridos


def test_una_figura_de_solo_la_casilla_libre_no_exige_nada() -> None:
    solo_libre = patron_de([(FILA_LIBRE, COLUMNA_LIBRE)])

    assert numeros_requeridos(CARTON_A, solo_libre) == frozenset()


def test_cuantas_faltan() -> None:
    requeridos = numeros_requeridos(CARTON_A, PRIMERA_FILA)

    assert faltan_para(requeridos, set()) == 5
    assert faltan_para(requeridos, {1, 2}) == 3
    assert faltan_para(requeridos, {1, 2, 3}) == 2
    assert faltan_para(requeridos, {1, 2, 3, 4}) == 1
    assert faltan_para(requeridos, {1, 2, 3, 4, 5}) == 0
    # Las balotas que no están en el cartón no acercan a nadie.
    assert faltan_para(requeridos, {40, 41, 42}) == 5


# --- Bingo -------------------------------------------------------------------


def _evaluar(cartones, formas, cantadas, orden=10, numero=99, registrados=None):
    return evaluar(
        cartones,
        formas,
        set(cantadas),
        orden_actual=orden,
        numero_actual=numero,
        registrados=registrados,
    )


def test_un_carton_completo_es_bingo() -> None:
    cuadro = _evaluar([en_juego(1, CARTON_A)], [forma()], [1, 2, 3, 4, 5])

    assert len(cuadro.ganadas) == 1
    assert cuadro.total_cartones_ganadores == 1
    assert cuadro.ganadas[0].cartones[0].codigo == "A-1"
    assert cuadro.ganadas[0].nuevo is True
    assert cuadro.ganadas[0].orden_balota == 10
    assert cuadro.ganadas[0].numero_balota == 99


def test_dos_cartones_que_ganan_a_la_vez_cuentan_los_dos() -> None:
    """Es el caso de «si hace bingo más de uno, decir la cantidad»."""
    cuadro = _evaluar(
        [en_juego(1, CARTON_A), en_juego(2, CARTON_B)], [forma()], [1, 2, 3, 4, 5]
    )

    assert len(cuadro.ganadas) == 1, "es una sola forma, ganada por dos cartones"
    assert cuadro.total_cartones_ganadores == 2
    assert [c.codigo for c in cuadro.ganadas[0].cartones] == ["A-1", "A-2"]


def test_sin_las_balotas_no_hay_bingo() -> None:
    cuadro = _evaluar([en_juego(1, CARTON_A)], [forma()], [1, 2, 3, 4])

    assert cuadro.ganadas == []


def test_una_figura_de_solo_la_casilla_libre_no_gana_nunca() -> None:
    """Exige cero balotas: sin este cuidado, daría bingo a todos antes de empezar."""
    solo_libre = forma(patron=patron_de([(FILA_LIBRE, COLUMNA_LIBRE)]))

    cuadro = _evaluar([en_juego(1, CARTON_A), en_juego(2, CARTON_B)], [solo_libre], [])

    assert cuadro.ganadas == []
    assert cuadro.cerca == []


# --- Una forma ganada se cierra ---------------------------------------------


def test_quien_completa_una_forma_ya_ganada_no_gana() -> None:
    """Llegó tarde: solo ganan los de la balota en que se completó."""
    ya_gano = GanadorRegistrado(
        partida_figura_id=1, carton_id=1, orden_balota=4, numero_balota=5
    )

    cuadro = _evaluar(
        [en_juego(1, CARTON_A), en_juego(2, CARTON_B)],
        [forma()],
        [1, 2, 3, 4, 5],
        orden=30,
        numero=70,
        registrados=[ya_gano],
    )

    assert cuadro.total_cartones_ganadores == 1, "el segundo cartón llegó tarde"
    assert cuadro.ganadas[0].cartones[0].carton_id == 1


def test_una_forma_ya_ganada_conserva_su_balota() -> None:
    """Reevaluar más tarde debe seguir diciendo con qué balota se ganó."""
    ya_gano = GanadorRegistrado(
        partida_figura_id=1, carton_id=1, orden_balota=4, numero_balota=5
    )

    cuadro = _evaluar(
        [en_juego(1, CARTON_A)],
        [forma()],
        [1, 2, 3, 4, 5],
        orden=30,
        numero=70,
        registrados=[ya_gano],
    )

    assert cuadro.ganadas[0].orden_balota == 4
    assert cuadro.ganadas[0].numero_balota == 5
    assert cuadro.ganadas[0].nuevo is False, "ya no es un bingo fresco"


def test_una_forma_ganada_deja_de_avisar_de_quien_esta_cerca() -> None:
    """Decir que a alguien «le falta una» para algo ya repartido desinforma."""
    ya_gano = GanadorRegistrado(
        partida_figura_id=1, carton_id=1, orden_balota=4, numero_balota=5
    )
    # El cartón B necesita 1..5 y solo tiene 1..4: estaría a una balota.
    cuadro = _evaluar(
        [en_juego(1, CARTON_A), en_juego(2, CARTON_B)],
        [forma()],
        [1, 2, 3, 4],
        registrados=[ya_gano],
    )

    assert cuadro.cerca == []
    assert cuadro.a_una == 0


def test_ganar_una_forma_saca_de_cerca_a_los_demas() -> None:
    """En la balota en que se gana, la forma deja de estar en juego para el resto.

    El cartón A completa «Segunda» (6..10) y el B se queda a una sola balota de
    completarla (le falta el 55). Ese «a una» no debe aparecer: la forma acaba de
    repartirse y el B ya no puede ganarla.
    """
    segunda_fila = patron_de([(1, c) for c in range(5)])

    cuadro = _evaluar(
        [en_juego(1, CARTON_A), en_juego(2, CARTON_B)],
        [forma(nombre="Segunda", patron=segunda_fila)],
        [6, 7, 8, 9, 10, 51, 52, 53, 54],
    )

    assert cuadro.total_cartones_ganadores == 1
    assert cuadro.ganadas[0].cartones[0].codigo == "A-1"
    assert cuadro.cerca == [], "el B ya no está en juego para esa forma"
    assert cuadro.a_una == 0


# --- Cerca de ganar ----------------------------------------------------------


def test_a_una_y_a_dos_balotas() -> None:
    """Los dos avisos que pidió el administrador, en la misma evaluación.

    Con las balotas 1,2,3,4 y 6,7,8 fuera:
      · A y B están a UNA de «Línea» (les falta el 5).
      · A está a DOS de «Segunda» (le faltan el 9 y el 10).
      · B está a cinco de «Segunda» (51..55), demasiado lejos para avisar.
    """
    segunda_fila = patron_de([(1, c) for c in range(5)])

    cuadro = _evaluar(
        [en_juego(1, CARTON_A), en_juego(2, CARTON_B)],
        [
            forma(patron=PRIMERA_FILA),
            forma(id_=2, nombre="Segunda", patron=segunda_fila, orden=2),
        ],
        [1, 2, 3, 4, 6, 7, 8],
    )

    assert cuadro.a_una == 2
    assert cuadro.a_dos == 1
    assert len(cuadro.cerca) == 3

    a_una = [c for c in cuadro.cerca if c.faltan == 1]
    assert {c.codigo for c in a_una} == {"A-1", "A-2"}
    assert all(c.numeros == [5] for c in a_una)

    a_dos = next(c for c in cuadro.cerca if c.faltan == 2)
    assert a_dos.codigo == "A-1" and a_dos.numeros == [9, 10]


def test_a_tres_balotas_no_se_avisa() -> None:
    cuadro = _evaluar([en_juego(1, CARTON_A)], [forma()], [1, 2])

    assert cuadro.cerca == []
    assert cuadro.a_una == 0 and cuadro.a_dos == 0


def test_cerca_dice_que_numeros_faltan() -> None:
    cuadro = _evaluar([en_juego(1, CARTON_A)], [forma()], [1, 2, 3, 5])

    assert cuadro.a_una == 1
    assert cuadro.cerca[0].numeros == [4]
    assert cuadro.cerca[0].figura == "Línea"


def test_los_mas_cerca_van_primero() -> None:
    # A necesita 1..5 (tiene 4 → falta 1); B necesita 51..55 (tiene 3 → faltan 2).
    segunda_fila = patron_de([(1, c) for c in range(5)])
    cuadro = _evaluar(
        [en_juego(1, CARTON_A), en_juego(2, CARTON_B)],
        [
            forma(patron=PRIMERA_FILA),
            forma(id_=2, nombre="Segunda", patron=segunda_fila, orden=2),
        ],
        [1, 2, 3, 4, 51, 52, 53],
    )

    assert [c.faltan for c in cuadro.cerca] == sorted(c.faltan for c in cuadro.cerca)
    assert cuadro.cerca[0].faltan == 1


def test_la_lista_se_recorta_pero_los_conteos_no_mienten() -> None:
    """Con muchos cartones la lista sería ilegible; el número debe seguir siendo real."""
    cartones = [
        en_juego(i, carton_de([1, 2, 3, 4, 5] + list(range(6 + i * 30, 25 + i * 30))))
        for i in range(1, MAXIMO_CERCA + 21)
    ]

    cuadro = _evaluar(cartones, [forma()], [1, 2, 3])

    assert len(cuadro.cerca) == MAXIMO_CERCA, "la lista va recortada"
    assert cuadro.a_dos == len(cartones), "el conteo es el total real"


# --- Varias formas a la vez --------------------------------------------------


def test_varias_formas_se_evaluan_todas() -> None:
    """Todas las formas de una partida juegan al mismo tiempo."""
    segunda_fila = patron_de([(1, c) for c in range(5)])

    cuadro = _evaluar(
        [en_juego(1, CARTON_A)],
        [
            forma(patron=PRIMERA_FILA),
            forma(id_=2, nombre="Segunda", patron=segunda_fila, orden=2),
        ],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    )

    assert len(cuadro.ganadas) == 2, "el cartón completó las dos"
    assert {g.forma.nombre for g in cuadro.ganadas} == {"Línea", "Segunda"}


def test_sin_formas_no_hay_nada_que_ganar() -> None:
    cuadro = _evaluar([en_juego(1, CARTON_A)], [], list(range(1, 76)))

    assert cuadro.ganadas == []
    assert cuadro.cerca == []
