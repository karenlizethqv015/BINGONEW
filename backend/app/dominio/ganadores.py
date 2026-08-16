"""Quién ganó y quién está a punto de ganar.

Este módulo no habla con la base de datos ni con el WebSocket: recibe datos
sueltos y devuelve el cuadro completo de la partida. Así se puede probar armando
cartones a mano, que es la única forma de comprobar de verdad estas cuentas.

Guardar los ganadores y emitirlos es cosa de `app/routers/balotas.py`.

Las tres preguntas del aviso al administrador —¿alguien ganó?, ¿quién está a una
balota?, ¿quién a dos?— son **la misma cuenta**: cuántos de los números que la
figura exige sobre ese cartón todavía no han salido. Ver `faltan_para` en
`app/dominio/bingo.py`.
"""

from dataclasses import dataclass, field

from app.dominio.bingo import (
    Patron,
    faltan_para_mascara,
    mascara_de,
    numeros_de_mascara,
    numeros_requeridos,
)
from app.dominio.bingo import Carton as MatrizCarton

#: Hasta cuántas balotas de distancia se avisa. El administrador pidió ver los
#: cartones a una y a dos balotas de ganar.
DISTANCIA_MAXIMA_AVISO = 2

#: Tope de entradas de la lista «cerca de ganar» que se envían por el
#: WebSocket. Con 500 cartones y varias formas, la lista completa serían miles
#: de filas que nadie puede leer. Los CONTEOS que acompañan a la lista sí son
#: los totales reales, sin recortar: el recorte no debe mentir en el número.
MAXIMO_CERCA = 50


@dataclass(frozen=True)
class CartonEnJuego:
    """Un cartón de la partida, con lo mínimo para evaluarlo y nombrarlo."""

    id: int
    codigo: str
    numeros: MatrizCarton


@dataclass(frozen=True)
class FormaEnJuego:
    """Una forma de ganar seleccionada para la partida, con su premio."""

    partida_figura_id: int
    figura_id: int
    nombre: str
    patron: Patron
    valor_premio: int
    orden: int


@dataclass(frozen=True)
class CartonGanador:
    carton_id: int
    codigo: str


@dataclass(frozen=True)
class GanadorRegistrado:
    """Un ganador ya guardado en la base de datos, tal cual está."""

    partida_figura_id: int
    carton_id: int
    orden_balota: int
    numero_balota: int


@dataclass
class FormaGanada:
    """Una forma completada, con todos los cartones que la ganaron."""

    forma: FormaEnJuego
    orden_balota: int
    numero_balota: int
    cartones: list[CartonGanador] = field(default_factory=list)
    #: Se completó justo con la balota que se acaba de cantar. Es lo que permite
    #: que la pantalla haga ruido con un bingo fresco y no en cada balota
    #: posterior, cuando el mismo bingo sigue estando en el cuadro.
    nuevo: bool = False


@dataclass(frozen=True)
class CartonCerca:
    """Un cartón a una o dos balotas de completar una forma."""

    carton_id: int
    codigo: str
    partida_figura_id: int
    figura: str
    faltan: int
    #: Los números que todavía le faltan, ordenados. Con `faltan` de 1 o 2 son
    #: uno o dos números, así que caben en pantalla y el administrador puede
    #: seguirlos con la vista.
    numeros: list[int]


#: Qué balotas exige cada forma sobre cada cartón, como máscara de bits:
#: `partida_figura_id → [máscara por cartón]`, alineado con la lista de cartones.
Mascaras = dict[int, list[int]]


def mascaras_de(
    cartones: list[CartonEnJuego], formas: list[FormaEnJuego]
) -> Mascaras:
    """Precalcula qué balotas exige cada forma sobre cada cartón.

    **No depende del sorteo**, solo del cartón y de la figura, así que se
    calcula una vez por partida y se reutiliza en las 75 balotas. Es lo que
    permite que una sala de 5000 cartones no rehaga 50.000 conjuntos por balota;
    quien la llama se encarga de guardarla (ver `app/servicios/ganadores.py`).
    """
    return {
        forma.partida_figura_id: [
            mascara_de(numeros_requeridos(carton.numeros, forma.patron))
            for carton in cartones
        ]
        for forma in formas
    }


@dataclass(frozen=True)
class ResumenPorForma:
    """Cuántos cartones están a una y a dos balotas, para UNA forma en concreto.

    A diferencia de `cerca` (recortada a `MAXIMO_CERCA` entradas totales, de
    todas las formas juntas), estos conteos son siempre los reales: existen
    justamente para que la balotera pueda mostrar «cartones a una balota de
    ganar: N» por forma, sin depender de que la lista detallada alcance a
    traerlos a todos.
    """

    partida_figura_id: int
    figura: str
    a_una: int
    a_dos: int


@dataclass
class CuadroDeGanadores:
    """Foto completa del estado de ganadores de una partida."""

    ganadas: list[FormaGanada]
    cerca: list[CartonCerca]
    a_una: int
    a_dos: int
    #: Una entrada por cada forma todavía vigente (ni ganada ni recién
    #: cerrada en esta misma balota). Las formas ya cerradas no aparecen: no
    #: tiene sentido avisar de «a una» para un premio que ya se entregó.
    por_forma: list[ResumenPorForma] = field(default_factory=list)

    @property
    def total_cartones_ganadores(self) -> int:
        """Cuántos cartones han ganado en total, sumando todas las formas."""
        return sum(len(ganada.cartones) for ganada in self.ganadas)


def evaluar(
    cartones: list[CartonEnJuego],
    formas: list[FormaEnJuego],
    cantadas: set[int],
    *,
    orden_actual: int,
    numero_actual: int | None,
    registrados: list[GanadorRegistrado] | None = None,
    mascaras: Mascaras | None = None,
) -> CuadroDeGanadores:
    """Calcula quién ganó y quién está cerca, con las balotas cantadas hasta hoy.

    `mascaras` es el precálculo de `mascaras_de`. Se puede omitir —y entonces se
    hace aquí mismo—, pero durante un sorteo hay que pasarlo: rehacerlo en cada
    balota es justo el coste que hunde una sala de 5000 cartones.

    `registrados` son los ganadores que ya están guardados en la base de datos.
    Hay dos fuentes distintas y no hay que mezclarlas:

    - **Una forma que ya tiene ganadores está cerrada.** Sus ganadores son los
      registrados, tal cual, y no se recalculan: solo ganan los cartones que la
      completaron en aquella balota, que comparten el premio. Quien la complete
      tres balotas después llegó tarde. Sin esta regla, al final del sorteo
      *todos* los cartones habrían «ganado» todo.
    - **Una forma sin ganadores sí se calcula.** Los cartones que la completan
      ahora son ganadores nuevos, con la balota que se acaba de cantar.

    Esta separación es también lo que hace que reevaluar una partida vieja —al
    reconectarse una pantalla, por ejemplo— devuelva el mismo cuadro y con la
    balota original, no con la que vaya el sorteo en ese momento.
    """
    if mascaras is None:
        mascaras = mascaras_de(cartones, formas)

    cantadas_bits = mascara_de(cantadas)

    por_forma: dict[int, list[GanadorRegistrado]] = {}
    for registro in registrados or []:
        por_forma.setdefault(registro.partida_figura_id, []).append(registro)

    codigos = {carton.id: carton.codigo for carton in cartones}

    ganadas: list[FormaGanada] = []
    cerca: list[CartonCerca] = []
    a_una = 0
    a_dos = 0

    for forma in sorted(formas, key=lambda f: f.orden):
        cerrada = por_forma.get(forma.partida_figura_id)

        if cerrada:
            # Forma ya ganada: se muestra tal como quedó registrada y deja de
            # estar en juego. No se buscan ganadores nuevos ni cartones cerca —
            # avisar de que a alguien «le falta una» para algo que ya se llevó
            # otro sería desinformar.
            ganadas.append(
                FormaGanada(
                    forma=forma,
                    orden_balota=cerrada[0].orden_balota,
                    numero_balota=cerrada[0].numero_balota,
                    # Por id y no por código: los códigos son texto («A-12»
                    # ordena antes que «A-7»), y el id sigue el orden real de
                    # generación de los cartones.
                    cartones=[
                        CartonGanador(r.carton_id, codigos.get(r.carton_id, "?"))
                        for r in sorted(cerrada, key=lambda r: r.carton_id)
                    ],
                    nuevo=False,
                )
            )
            continue

        ganadores: list[CartonGanador] = []
        por_carton = mascaras[forma.partida_figura_id]

        for indice, carton in enumerate(cartones):
            requeridos = por_carton[indice]

            # Una figura formada solo por la casilla libre no exige ninguna
            # balota y daría bingo a todo el mundo antes de empezar. Se ignora:
            # es una configuración sin sentido, y es preferible no avisar de nada
            # a declarar quinientos ganadores.
            if not requeridos:
                continue

            faltan = faltan_para_mascara(requeridos, cantadas_bits)

            if faltan == 0:
                ganadores.append(CartonGanador(carton.id, carton.codigo))
                continue

            if faltan > DISTANCIA_MAXIMA_AVISO:
                continue

            if faltan == 1:
                a_una += 1
            else:
                a_dos += 1

            cerca.append(
                CartonCerca(
                    carton_id=carton.id,
                    codigo=carton.codigo,
                    partida_figura_id=forma.partida_figura_id,
                    figura=forma.nombre,
                    faltan=faltan,
                    numeros=numeros_de_mascara(requeridos & ~cantadas_bits),
                )
            )

        if ganadores:
            # Recién ganada: se lleva la balota que se acaba de cantar. Los
            # cartones que estaban cerca de ESTA forma dejan de estar en juego.
            cerca = [
                c for c in cerca if c.partida_figura_id != forma.partida_figura_id
            ]
            a_una = sum(1 for c in cerca if c.faltan == 1)
            a_dos = sum(1 for c in cerca if c.faltan == 2)

            ganadas.append(
                FormaGanada(
                    forma=forma,
                    orden_balota=orden_actual,
                    numero_balota=numero_actual or 0,
                    cartones=sorted(ganadores, key=lambda g: g.carton_id),
                    nuevo=True,
                )
            )

    # Primero los que están más cerca; dentro de cada grupo, en orden fijo, para
    # que la lista no baile de posición entre balota y balota.
    cerca.sort(key=lambda c: (c.faltan, c.carton_id, c.figura))

    # El desglose por forma sale de `cerca` ya completa (antes del recorte a
    # MAXIMO_CERCA): cada entrada trae su `partida_figura_id`, así que basta
    # con contar, sin otra pasada por los cartones. Las formas cerradas —ya
    # ganadas, incluida la que se acaba de ganar en esta misma balota— quedan
    # fuera a propósito.
    cerradas = {ganada.forma.partida_figura_id for ganada in ganadas}
    conteos: dict[int, list[int]] = {}
    for item in cerca:
        contador = conteos.setdefault(item.partida_figura_id, [0, 0])
        contador[0 if item.faltan == 1 else 1] += 1

    por_forma = [
        ResumenPorForma(
            partida_figura_id=forma.partida_figura_id,
            figura=forma.nombre,
            a_una=conteos.get(forma.partida_figura_id, [0, 0])[0],
            a_dos=conteos.get(forma.partida_figura_id, [0, 0])[1],
        )
        for forma in sorted(formas, key=lambda f: f.orden)
        if forma.partida_figura_id not in cerradas
    ]

    return CuadroDeGanadores(
        ganadas=ganadas,
        cerca=cerca[:MAXIMO_CERCA],
        a_una=a_una,
        a_dos=a_dos,
        por_forma=por_forma,
    )
