"""Constantes y reglas del bingo de 75 bolas.

Este es el único lugar donde viven estas reglas. No repetirlas escritas a mano
en otros módulos: si alguna cambia, debe cambiar aquí y en ningún otro lado.
"""

import hashlib
import secrets
from collections.abc import Iterable
from typing import TypeAlias

# --- Cuadrícula del cartón y de las figuras ---

#: El cartón y las figuras son matrices de 5x5.
TAMANO_CUADRICULA = 5

#: Casilla libre: el centro de la cuadrícula (fila 2, columna 2, base 0).
#: En el bingo de 75 bolas siempre cuenta como marcada, sin que salga ninguna
#: balota. Una figura PUEDE incluirla o no (por ejemplo, "cuatro esquinas" no la
#: incluye); si la incluye, se da por cumplida automáticamente al validar el
#: cartón ganador.
FILA_LIBRE = 2
COLUMNA_LIBRE = 2

#: Un patrón de figura: matriz de 5x5 de booleanos. True = celda que forma parte
#: de la figura.
Patron: TypeAlias = list[list[bool]]


def es_celda_libre(fila: int, columna: int) -> bool:
    """Indica si una celda es la casilla libre del centro."""
    return fila == FILA_LIBRE and columna == COLUMNA_LIBRE


def contar_celdas(patron: Patron) -> int:
    """Cuenta cuántas celdas están marcadas en un patrón."""
    return sum(1 for fila in patron for celda in fila if celda)


def patron_vacio() -> Patron:
    """Devuelve un patrón de 5x5 sin ninguna celda marcada."""
    return [[False] * TAMANO_CUADRICULA for _ in range(TAMANO_CUADRICULA)]


# --- Balotas y columnas B-I-N-G-O -------------------------------------------

#: Encabezados de las columnas, en orden.
LETRAS = ("B", "I", "N", "G", "O")

#: Rango de números de cada columna, ambos extremos incluidos.
#: B 1–15, I 16–30, N 31–45, G 46–60, O 61–75.
RANGOS_POR_COLUMNA: tuple[tuple[int, int], ...] = (
    (1, 15),
    (16, 30),
    (31, 45),
    (46, 60),
    (61, 75),
)

#: Total de balotas de una partida.
TOTAL_BALOTAS = 75

#: Un cartón: matriz 5x5 de números, con `None` en la casilla libre del centro.
Carton: TypeAlias = list[list[int | None]]


def columna_de_numero(numero: int) -> int:
    """Devuelve el índice de columna (0–4) al que pertenece un número."""
    for indice, (desde, hasta) in enumerate(RANGOS_POR_COLUMNA):
        if desde <= numero <= hasta:
            return indice
    raise ValueError(f"{numero} no está entre 1 y {TOTAL_BALOTAS}.")


def letra_de_numero(numero: int) -> str:
    """Devuelve la letra ('B', 'I', 'N', 'G' u 'O') de un número."""
    return LETRAS[columna_de_numero(numero)]


def _elegir_sin_reemplazo(desde: int, hasta: int, cantidad: int) -> list[int]:
    """Elige `cantidad` números distintos del rango, sin repetir.

    Usa `secrets`, el generador criptográficamente seguro, y NO `random`: es un
    requisito de diseño del proyecto para dejar abierto el camino a una futura
    certificación de GNA ante Coljuegos. Aplica igual aquí que en la balotera.
    """
    disponibles = list(range(desde, hasta + 1))
    elegidos: list[int] = []

    for _ in range(cantidad):
        # randbelow da un entero uniforme en [0, n); sacar el elegido de la
        # lista es lo que garantiza que no se repita.
        elegidos.append(disponibles.pop(secrets.randbelow(len(disponibles))))

    return elegidos


def generar_carton() -> Carton:
    """Genera un cartón 5x5 válido de bingo de 75 bolas.

    Cada columna toma 5 números distintos de su propio rango, y el centro queda
    como casilla libre (`None`).
    """
    columnas = [
        _elegir_sin_reemplazo(desde, hasta, TAMANO_CUADRICULA)
        for desde, hasta in RANGOS_POR_COLUMNA
    ]

    carton: Carton = [
        [columnas[columna][fila] for columna in range(TAMANO_CUADRICULA)]
        for fila in range(TAMANO_CUADRICULA)
    ]
    carton[FILA_LIBRE][COLUMNA_LIBRE] = None

    return carton


class SinBalotasDisponibles(Exception):
    """Se pidió una balota cuando ya salieron las 75."""


def sortear_balota(cantadas: set[int]) -> int:
    """Saca una balota que no haya salido todavía en esta partida.

    Sorteo **sin reemplazo**: se construye la lista de las que quedan y se elige
    una de ahí, así que por definición no puede repetirse. No se sortea "hasta
    que salga una nueva", que además de ser más lento se vuelve casi infinito al
    final de la partida.

    Usa `secrets`, el generador criptográficamente seguro, y NO `random`: es un
    requisito de diseño del proyecto de cara a una futura certificación de GNA
    ante Coljuegos.
    """
    restantes = [
        numero
        for numero in range(1, TOTAL_BALOTAS + 1)
        if numero not in cantadas
    ]

    if not restantes:
        raise SinBalotasDisponibles(
            f"Ya salieron las {TOTAL_BALOTAS} balotas de la partida."
        )

    return restantes[secrets.randbelow(len(restantes))]


def firma_carton(carton: Carton) -> str:
    """Huella única del cartón, para detectar duplicados dentro de una partida.

    Depende de la posición: dos cartones con los mismos números colocados
    distinto son cartones distintos y deben dar firmas distintas.
    """
    plano = ",".join(
        "L" if valor is None else str(valor) for fila in carton for valor in fila
    )
    return hashlib.sha256(plano.encode()).hexdigest()


def numeros_requeridos(carton: Carton, patron: Patron) -> frozenset[int]:
    """Números que deben salir para que este cartón complete este patrón.

    Son los valores del cartón en las celdas que el patrón marca. **La casilla
    libre no aporta ninguno**: ya cuenta como marcada sin que salga balota, así
    que una figura que la incluya exige una balota menos que celdas tiene.

    No depende del sorteo, solo del cartón y de la figura, así que se puede
    calcular una vez y reutilizar durante toda la partida.

    Ojo con el conjunto vacío: significa que la figura no exige ninguna balota
    (por ejemplo, un patrón formado solo por la casilla libre). Quien use esto
    debe decidir qué hacer con ese caso; ver `app/dominio/ganadores.py`.
    """
    return frozenset(
        valor
        for fila_indice, fila in enumerate(patron)
        for columna, marcada in enumerate(fila)
        if marcada and (valor := carton[fila_indice][columna]) is not None
    )


def faltan_para(requeridos: frozenset[int], cantadas: set[int]) -> int:
    """Cuántas balotas faltan para completar la figura.

    Es la cuenta que responde las tres preguntas del aviso al administrador:
    0 es bingo, 1 es «a una balota», 2 es «a dos balotas».
    """
    return len(requeridos - cantadas)


# --- La misma cuenta, con enteros --------------------------------------------
#
# Una sala grande juega con 5000 cartones y diez formas: son 50.000 cuentas por
# balota, 75 veces. Con conjuntos eso son 50.000 objetos nuevos cada vez y
# bloquea el bucle de eventos durante décimas de segundo, con lo que se atascan
# los WebSockets de todas las pantallas conectadas.
#
# Un número cabe en un bit, y las 75 balotas caben de sobra en un entero de
# Python. Así la cuenta se convierte en un AND y un conteo de bits, que corren
# en C. Las funciones de conjuntos de arriba se conservan: son las que explican
# la regla y las que usan las pruebas del dominio.


def mascara_de(numeros: Iterable[int]) -> int:
    """Los números, como bits de un entero: el número n ocupa el bit n."""
    mascara = 0
    for numero in numeros:
        mascara |= 1 << numero
    return mascara


def faltan_para_mascara(requeridos: int, cantadas: int) -> int:
    """Cuántas balotas faltan. Misma cuenta que `faltan_para`, con máscaras.

    `~cantadas` es negativo (los enteros de Python no tienen ancho fijo), pero
    el AND con `requeridos`, que es positivo y finito, deja siempre un resultado
    positivo: son justo los bits pedidos que todavía no han salido.
    """
    return (requeridos & ~cantadas).bit_count()


def numeros_de_mascara(mascara: int) -> list[int]:
    """Los números que la máscara tiene encendidos, de menor a mayor.

    Hace falta para los avisos de «cerca de ganar», que enseñan al administrador
    qué números concretos le faltan a un cartón: son uno o dos.

    Da una vuelta por cada bit encendido, no una por cada número posible. La
    diferencia importa porque esto se llama una vez por cada cartón que está
    cerca, y en una sala de 5000 pueden ser miles en la misma balota: recorrer
    las 75 posiciones para sacar un solo número costaba más que toda la cuenta
    de ganadores.
    """
    numeros: list[int] = []
    while mascara:
        # `m & -m` deja solo el bit encendido más bajo.
        bit = mascara & -mascara
        numeros.append(bit.bit_length() - 1)
        mascara ^= bit
    return numeros


def validar_carton(carton: Carton) -> None:
    """Comprueba que un cartón cumpla las reglas. Lanza ValueError si no.

    Se usa en las pruebas y como red de seguridad: un cartón mal formado que
    llegue a la base de datos rompería la validación de ganadores más adelante.
    """
    if len(carton) != TAMANO_CUADRICULA:
        raise ValueError(f"El cartón debe tener {TAMANO_CUADRICULA} filas.")

    for indice, fila in enumerate(carton):
        if len(fila) != TAMANO_CUADRICULA:
            raise ValueError(f"La fila {indice} debe tener {TAMANO_CUADRICULA} columnas.")

    if carton[FILA_LIBRE][COLUMNA_LIBRE] is not None:
        raise ValueError("El centro del cartón debe ser la casilla libre.")

    vistos: set[int] = set()
    for fila_indice, fila in enumerate(carton):
        for columna, valor in enumerate(fila):
            if valor is None:
                if not es_celda_libre(fila_indice, columna):
                    raise ValueError(
                        f"Solo el centro puede ir vacío; la celda "
                        f"({fila_indice}, {columna}) no tiene número."
                    )
                continue

            desde, hasta = RANGOS_POR_COLUMNA[columna]
            if not desde <= valor <= hasta:
                raise ValueError(
                    f"{valor} no puede ir en la columna {LETRAS[columna]} "
                    f"({desde}–{hasta})."
                )

            if valor in vistos:
                raise ValueError(f"El número {valor} está repetido en el cartón.")
            vistos.add(valor)
