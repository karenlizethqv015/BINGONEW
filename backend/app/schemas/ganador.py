"""Esquemas del cuadro de ganadores.

Describen exactamente el mismo cuerpo que emite el evento `ganadores` del
WebSocket. El endpoint HTTP construye su respuesta con `evento_ganadores` y la
valida contra estos modelos, así que las dos vías **no pueden desincronizarse**:
si alguien cambia el evento y olvida el esquema, las pruebas fallan.
"""

from pydantic import BaseModel


class CartonGanadorLeer(BaseModel):
    carton_id: int
    codigo: str


class BingoLeer(BaseModel):
    """Una forma de ganar completada."""

    partida_figura_id: int
    figura_id: int
    figura: str
    valor_premio: int
    #: Balota con la que se completó: su posición en el sorteo y su número.
    orden_balota: int
    numero_balota: int
    #: Se completó con la balota que se acaba de cantar.
    nuevo: bool
    cartones: list[CartonGanadorLeer]


class CercaLeer(BaseModel):
    """Un cartón a una o dos balotas de completar una forma."""

    carton_id: int
    codigo: str
    partida_figura_id: int
    figura: str
    faltan: int
    #: Los números que todavía le faltan.
    numeros: list[int]


class CuadroGanadoresLeer(BaseModel):
    """Foto completa: quién ganó y quién está a punto."""

    tipo: str
    partida_id: int
    orden_balota: int
    bingos: list[BingoLeer]
    total_cartones_ganadores: int
    #: Totales REALES de cartones a una y a dos balotas, aunque `cerca` venga
    #: recortada para no mandar miles de filas ilegibles.
    a_una: int
    a_dos: int
    cerca: list[CercaLeer]
