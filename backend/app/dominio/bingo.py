"""Constantes y reglas del bingo de 75 bolas.

Este es el único lugar donde viven estas reglas. No repetirlas escritas a mano
en otros módulos: si alguna cambia, debe cambiar aquí y en ningún otro lado.
"""

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
