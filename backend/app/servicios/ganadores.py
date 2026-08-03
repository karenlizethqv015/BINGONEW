"""Evaluar la partida, registrar los ganadores nuevos y armar el aviso.

Es el puente entre la base de datos y las reglas puras de
`app/dominio/ganadores.py`. Lo usan tres sitios —al cantar una balota, al
conectarse una pantalla y al consultar por HTTP—, y los tres tienen que ver
exactamente el mismo cuadro.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.ganadores import (
    CartonEnJuego,
    CuadroDeGanadores,
    FormaEnJuego,
    GanadorRegistrado,
    evaluar,
)
from app.models.balota_cantada import BalotaCantada
from app.models.carton import Carton
from app.models.ganador import Ganador
from app.models.partida_figura import PartidaFigura


def codigo_de_carton(carton: Carton) -> str:
    """Código visible del cartón dentro de su partida, como «A-7»."""
    return f"{carton.serie}-{carton.numero_carton}"


async def _cartones_de(db: AsyncSession, partida_id: int) -> list[CartonEnJuego]:
    filas = (
        await db.execute(
            select(Carton)
            .where(Carton.partida_id == partida_id)
            .order_by(Carton.serie, Carton.numero_carton)
        )
    ).scalars()

    return [
        CartonEnJuego(id=c.id, codigo=codigo_de_carton(c), numeros=c.numeros)
        for c in filas
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

    cuadro = evaluar(
        cartones=await _cartones_de(db, partida_id),
        formas=await _formas_de(db, partida_id),
        cantadas=cantadas,
        orden_actual=orden_actual,
        numero_actual=ultima.numero if ultima else None,
        registrados=await _registrados_de(db, partida_id),
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
