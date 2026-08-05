"""Evaluar la partida, registrar los ganadores nuevos y armar el aviso.

Es el puente entre la base de datos y las reglas puras de
`app/dominio/ganadores.py`. Lo usan tres sitios —al cantar una balota, al
conectarse una pantalla y al consultar por HTTP—, y los tres tienen que ver
exactamente el mismo cuadro.
"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.ganadores import (
    CartonEnJuego,
    CuadroDeGanadores,
    FormaEnJuego,
    GanadorRegistrado,
    Mascaras,
    evaluar,
    mascaras_de,
)
from app.models.balota_cantada import BalotaCantada
from app.models.carton import Carton
from app.models.ganador import Ganador
from app.models.partida_figura import PartidaFigura


def codigo_de_carton(serie: str, numero_carton: int) -> str:
    """Código visible del cartón dentro de su partida, como «A-7»."""
    return f"{serie}-{numero_carton}"


async def _cartones_de(db: AsyncSession, partida_id: int) -> list[CartonEnJuego]:
    """Los cartones de la partida, con lo justo para evaluarlos.

    Se piden columnas sueltas y no entidades: con 5000 cartones, construir 5000
    objetos del ORM y meterlos en el mapa de identidad de la sesión cuesta más
    que la propia consulta, y aquí no se va a modificar ninguno.
    """
    filas = await db.execute(
        select(Carton.id, Carton.serie, Carton.numero_carton, Carton.numeros)
        .where(Carton.partida_id == partida_id)
        .order_by(Carton.serie, Carton.numero_carton)
    )

    return [
        CartonEnJuego(id=id_, codigo=codigo_de_carton(serie, numero), numeros=numeros)
        for id_, serie, numero, numeros in filas
    ]


async def _formas_de(db: AsyncSession, partida_id: int) -> list[FormaEnJuego]:
    filas = (
        await db.execute(
            select(PartidaFigura)
            .where(PartidaFigura.partida_id == partida_id)
            .order_by(PartidaFigura.orden)
        )
    ).scalars()

    return [
        FormaEnJuego(
            partida_figura_id=pf.id,
            figura_id=pf.figura_id,
            nombre=pf.figura.nombre,
            patron=pf.figura.patron,
            valor_premio=pf.valor_premio,
            orden=pf.orden,
        )
        for pf in filas
    ]


# --- Precálculo de las máscaras, cacheado por partida ------------------------
#
# Qué balotas exige cada forma sobre cada cartón no cambia durante el sorteo, y
# es lo caro de calcular: 5000 cartones por 10 formas son 50.000 cuentas. Sin
# caché se rehacían en CADA balota, 75 veces, y también cada vez que una
# pantalla se conectaba.


@dataclass
class _Preparado:
    """Lo que no cambia entre balotas, con el sello que dice si sigue vigente."""

    sello_cartones: tuple[int, str | None]
    sello_formas: tuple
    cartones: list[CartonEnJuego]
    mascaras: Mascaras


#: Partidas preparadas, de la menos usada a la más reciente.
_preparados: dict[int, _Preparado] = {}

#: Cuántas partidas se guardan a la vez. En una sala se juega de una en una; el
#: tope existe para que un servidor que lleva semanas encendido no acumule las
#: máscaras de todas las partidas de su historia.
MAXIMO_PARTIDAS_PREPARADAS = 8


async def _sello_de_cartones(
    db: AsyncSession, partida_id: int
) -> tuple[int, str | None]:
    """Huella barata del juego de cartones: cuántos hay y la mayor de sus firmas.

    Una consulta agregada sobre el índice, en vez de traerse las 5000 filas solo
    para comprobar si cambiaron.

    Va por la **firma** y no por el `id` a propósito: SQLite reutiliza los
    identificadores borrados, así que borrar cien cartones y generar otros cien
    devolvería exactamente el mismo `(total, max(id))` con cartones distintos, y
    el precálculo viejo seguiría en uso decidiendo quién gana. La firma es un
    sha256 del cartón: si el juego cambia, cambia.
    """
    total, mayor = (
        await db.execute(
            select(func.count(Carton.id), func.max(Carton.firma)).where(
                Carton.partida_id == partida_id
            )
        )
    ).one()
    return total, mayor


def _sello_de_formas(formas: list[FormaEnJuego]) -> tuple:
    """Huella de las formas, incluido el patrón de cada figura.

    El patrón entra a propósito: una figura del catálogo se puede editar con la
    partida en curso, y sin él las máscaras seguirían usando el dibujo viejo sin
    que nada lo delatara. El premio y el nombre NO entran: no afectan a las
    máscaras y se releen enteros en cada evaluación.
    """
    return tuple(
        (
            forma.partida_figura_id,
            forma.figura_id,
            tuple(tuple(fila) for fila in forma.patron),
        )
        for forma in formas
    )


async def _preparar(
    db: AsyncSession, partida_id: int, formas: list[FormaEnJuego]
) -> _Preparado:
    """Devuelve los cartones y las máscaras de la partida, calculándolos si hace falta."""
    sello_cartones = await _sello_de_cartones(db, partida_id)
    sello_formas = _sello_de_formas(formas)

    guardado = _preparados.get(partida_id)
    if (
        guardado is not None
        and guardado.sello_cartones == sello_cartones
        and guardado.sello_formas == sello_formas
    ):
        # Se vuelve a insertar para que cuente como la más reciente.
        _preparados[partida_id] = _preparados.pop(partida_id)
        return guardado

    # Cambiaron los cartones o las formas: el último cuadro emitido se calculó
    # con los de antes, así que ya no vale para quien se conecte ahora.
    _ultimo_cuadro.pop(partida_id, None)

    cartones = await _cartones_de(db, partida_id)
    preparado = _Preparado(
        sello_cartones=sello_cartones,
        sello_formas=sello_formas,
        cartones=cartones,
        mascaras=mascaras_de(cartones, formas),
    )

    _preparados.pop(partida_id, None)
    _preparados[partida_id] = preparado
    while len(_preparados) > MAXIMO_PARTIDAS_PREPARADAS:
        _preparados.pop(next(iter(_preparados)))

    return preparado


# --- El último cuadro emitido, para quien se conecta -------------------------


#: Último evento `ganadores` emitido de cada partida, ya normalizado.
_ultimo_cuadro: dict[int, dict] = {}


def _sin_novedad(evento: dict) -> dict:
    """El mismo cuadro, pero sin ningún bingo marcado como nuevo.

    `nuevo` significa «detectado en esta evaluación», y es lo que hace que la
    pantalla suene una sola vez. Guardado tal cual, un jugador que se conectara
    cinco balotas después del bingo recibiría ese `nuevo` y su cartón anunciaría
    a gritos un bingo ajeno y viejo. Es la misma regla que ya cumple la consulta
    por HTTP.
    """
    return {
        **evento,
        "bingos": [{**bingo, "nuevo": False} for bingo in evento["bingos"]],
    }


def recordar_cuadro(evento: dict) -> None:
    """Guarda el cuadro recién emitido para servírselo a quien se conecte."""
    partida_id = evento["partida_id"]
    _ultimo_cuadro.pop(partida_id, None)
    _ultimo_cuadro[partida_id] = _sin_novedad(evento)

    while len(_ultimo_cuadro) > MAXIMO_PARTIDAS_PREPARADAS:
        _ultimo_cuadro.pop(next(iter(_ultimo_cuadro)))


def cuadro_recordado(partida_id: int) -> dict | None:
    """El último cuadro emitido, o None si esta partida no ha emitido ninguno.

    Existe para que abrir una pantalla no cueste una evaluación completa: en una
    sala llena son cientos de jugadores conectándose a la vez, y el cuadro que
    les corresponde es exactamente el último que se emitió.
    """
    return _ultimo_cuadro.get(partida_id)


def olvidar_precalculo() -> None:
    """Tira el precálculo de todas las partidas. Lo necesitan las pruebas.

    En producción no hace falta llamarlo: el sello se da cuenta solo de que los
    cartones o las formas cambiaron. Existe porque las pruebas comparten el
    proceso y arrancan cada una con una base nueva donde los identificadores de
    partida vuelven a empezar en 1, así que el precálculo de una prueba podría
    darse por bueno en la siguiente.
    """
    _preparados.clear()
    _ultimo_cuadro.clear()


async def _registrados_de(
    db: AsyncSession, partida_id: int
) -> list[GanadorRegistrado]:
    filas = (
        await db.execute(select(Ganador).where(Ganador.partida_id == partida_id))
    ).scalars()

    return [
        GanadorRegistrado(
            partida_figura_id=g.partida_figura_id,
            carton_id=g.carton_id,
            orden_balota=g.orden_balota,
            numero_balota=g.numero_balota,
        )
        for g in filas
    ]


async def evaluar_partida(
    db: AsyncSession, partida_id: int, *, registrar: bool
) -> tuple[CuadroDeGanadores, int]:
    """Devuelve el cuadro de ganadores de la partida y el orden de la última balota.

    Con `registrar=True` guarda además los ganadores nuevos que encuentre. Solo
    debe pedirse desde el sacado de balota, **dentro del cerrojo de la partida**:
    dos evaluaciones simultáneas leerían la misma tabla vacía de ganadores y
    tratarían de insertar los mismos dos veces. Consultar (`registrar=False`) no
    escribe nada, así que puede correr en cualquier momento.
    """
    balotas = list(
        (
            await db.execute(
                select(BalotaCantada)
                .where(BalotaCantada.partida_id == partida_id)
                .order_by(BalotaCantada.orden)
            )
        )
        .scalars()
        .all()
    )

    cantadas = {balota.numero for balota in balotas}
    ultima = balotas[-1] if balotas else None
    orden_actual = ultima.orden if ultima else 0

    # Las formas se releen siempre: son diez filas y llevan el premio y el
    # nombre, que sí pueden cambiar sin que cambien las máscaras.
    formas = await _formas_de(db, partida_id)
    preparado = await _preparar(db, partida_id, formas)

    cuadro = evaluar(
        cartones=preparado.cartones,
        formas=formas,
        cantadas=cantadas,
        orden_actual=orden_actual,
        numero_actual=ultima.numero if ultima else None,
        registrados=await _registrados_de(db, partida_id),
        mascaras=preparado.mascaras,
    )

    if registrar:
        nuevos = [
            Ganador(
                partida_id=partida_id,
                carton_id=carton.carton_id,
                partida_figura_id=ganada.forma.partida_figura_id,
                orden_balota=ganada.orden_balota,
                numero_balota=ganada.numero_balota,
            )
            for ganada in cuadro.ganadas
            if ganada.nuevo
            for carton in ganada.cartones
        ]

        if nuevos:
            db.add_all(nuevos)
            await db.commit()

    return cuadro, orden_actual


async def borrar_ganadores(db: AsyncSession, partida_id: int) -> None:
    """Borra los ganadores de la partida. Acompaña al reinicio del sorteo.

    Sin esto, reiniciar dejaría ganadores de un sorteo que ya no existe: sus
    formas seguirían saliendo como cerradas y nadie podría volver a ganarlas.
    """
    for ganador in (
        (await db.execute(select(Ganador).where(Ganador.partida_id == partida_id)))
        .scalars()
        .all()
    ):
        await db.delete(ganador)
