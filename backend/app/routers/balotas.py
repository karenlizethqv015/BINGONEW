"""Balotera virtual: sorteo de balotas y control del estado de la partida.

El backend es la autoridad sobre **qué** número sale y cuándo se guarda; el
navegador del administrador solo decide **cuándo** pedir la siguiente (decisión
registrada en PROGRESS.md). Ninguna regla del bingo vive en el frontend.
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dominio.bingo import TOTAL_BALOTAS, SinBalotasDisponibles, sortear_balota
from app.dominio.ganadores import CuadroDeGanadores
from app.models.balota_cantada import BalotaCantada
from app.models.partida import EstadoPartida, Partida
from app.realtime.eventos import (
    canal_de_partida,
    evento_balota,
    evento_estado,
    evento_ganadores,
)
from app.realtime.manager import gestor
from app.schemas.balota import BalotaLeer, EstadoSorteo
from app.seguridad import SOLO_ADMIN
from app.schemas.ganador import CuadroGanadoresLeer
from app.servicios.ganadores import (
    borrar_ganadores,
    evaluar_partida,
    recordar_cuadro,
)

router = APIRouter(
    prefix="/api/partidas/{partida_id}", tags=["balotera"], dependencies=SOLO_ADMIN
)

#: Un cerrojo por partida para serializar el sacado de balota.
#:
#: Sin esto, dos peticiones simultáneas pueden leer el mismo conjunto de balotas
#: cantadas y sortear a partir de él, con lo que podrían sacar el mismo número o
#: pisarse el `orden`. El índice único de la tabla las rechazaría, pero con un
#: error 500 en vez de comportarse bien. Con el cerrojo, la segunda petición
#: simplemente espera y ve el estado ya actualizado.
_cerrojos: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


async def _obtener_partida_o_404(db: AsyncSession, partida_id: int) -> Partida:
    partida = await db.get(Partida, partida_id)
    if partida is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la partida {partida_id}.",
        )
    return partida


async def _contar_balotas(db: AsyncSession, partida_id: int) -> int:
    return (
        await db.execute(
            select(func.count())
            .select_from(BalotaCantada)
            .where(BalotaCantada.partida_id == partida_id)
        )
    ).scalar_one()


async def _balotas_de(db: AsyncSession, partida_id: int) -> list[BalotaCantada]:
    resultado = await db.execute(
        select(BalotaCantada)
        .where(BalotaCantada.partida_id == partida_id)
        .order_by(BalotaCantada.orden)
    )
    return list(resultado.scalars().all())


def _conflicto(mensaje: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=mensaje)


async def _emitir_estado(db: AsyncSession, partida: Partida) -> None:
    """Avisa por WebSocket de que la partida cambió de estado."""
    total = await _contar_balotas(db, partida.id)
    await gestor.emitir(
        canal_de_partida(partida.id), evento_estado(partida, total)
    )


async def _emitir_ganadores(
    db: AsyncSession, partida: Partida, *, registrar: bool
) -> CuadroDeGanadores:
    """Evalúa la partida y emite el cuadro de ganadores. Devuelve el cuadro.

    Devuelve el cuadro y no el evento porque quien canta la balota necesita
    preguntarle si hubo un bingo **nuevo**, para detener el sorteo.
    """
    cuadro, orden = await evaluar_partida(db, partida.id, registrar=registrar)
    evento = evento_ganadores(partida, cuadro, orden)

    # Guardarlo es lo que evita que cada pantalla que se conecte después tenga
    # que reevaluar la partida entera por su cuenta.
    recordar_cuadro(evento)

    await gestor.emitir(canal_de_partida(partida.id), evento)
    return cuadro


# --- Consulta ---------------------------------------------------------------


@router.get("/balotas", response_model=list[BalotaLeer])
async def listar_balotas(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> list[BalotaCantada]:
    """Balotas cantadas de la partida, en el orden en que salieron."""
    await _obtener_partida_o_404(db, partida_id)
    return await _balotas_de(db, partida_id)


@router.get("/sorteo", response_model=EstadoSorteo)
async def estado_del_sorteo(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> EstadoSorteo:
    """Resumen del sorteo: estado, cuántas van, cuántas quedan y la última."""
    partida = await _obtener_partida_o_404(db, partida_id)
    balotas = await _balotas_de(db, partida_id)

    return EstadoSorteo(
        partida_id=partida.id,
        estado=partida.estado,
        total_cantadas=len(balotas),
        restantes=TOTAL_BALOTAS - len(balotas),
        ultima=BalotaLeer.model_validate(balotas[-1]) if balotas else None,
    )


@router.get("/ganadores", response_model=CuadroGanadoresLeer)
async def cuadro_de_ganadores(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> dict:
    """Quién ha ganado y quién está a una o a dos balotas de ganar.

    Es el mismo cuerpo que emite el evento `ganadores` del WebSocket, construido
    con la misma función: HTTP y tiempo real no pueden discrepar. Sirve para la
    carga inicial de una pantalla y para poder comprobarlo desde un script.

    Solo consulta: no registra ganadores nuevos. Los ganadores se registran al
    cantar la balota, que es el único momento en que pueden aparecer.
    """
    partida = await _obtener_partida_o_404(db, partida_id)
    cuadro, orden = await evaluar_partida(db, partida_id, registrar=False)
    return evento_ganadores(partida, cuadro, orden)


# --- Sorteo -----------------------------------------------------------------


@router.post(
    "/balotas", response_model=BalotaLeer, status_code=status.HTTP_201_CREATED
)
async def cantar_balota(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> BalotaCantada:
    """Saca la siguiente balota, la registra y la emite por WebSocket.

    El sorteo se detiene solo en dos casos: al salir la número 75 la partida se
    **finaliza** (se agotaron las balotas), y al aparecer un bingo nuevo se
    **pausa**, para que el encargado pueda atender al ganador.
    """
    async with _cerrojos[partida_id]:
        partida = await _obtener_partida_o_404(db, partida_id)

        if partida.estado is not EstadoPartida.EN_CURSO:
            raise _conflicto(
                f"La partida está «{partida.estado.value}». "
                "Solo se pueden cantar balotas con el sorteo en curso."
            )

        cantadas = {balota.numero for balota in await _balotas_de(db, partida_id)}

        try:
            numero = sortear_balota(cantadas)
        except SinBalotasDisponibles as error:
            raise _conflicto(str(error)) from error

        balota = BalotaCantada(
            partida_id=partida_id, numero=numero, orden=len(cantadas) + 1
        )
        db.add(balota)

        total = len(cantadas) + 1
        # Se agotaron las balotas: el sorteo termina aquí.
        if total == TOTAL_BALOTAS:
            partida.estado = EstadoPartida.FINALIZADA
            partida.finalizada_en = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(balota)

        canal = canal_de_partida(partida_id)
        await gestor.emitir(canal, evento_balota(partida, balota, total))

        # Con la balota ya guardada, mirar quién ganó y quién quedó a una o dos.
        # Va dentro del cerrojo: dos evaluaciones simultáneas leerían la misma
        # tabla de ganadores vacía y registrarían los mismos dos veces.
        cuadro = await _emitir_ganadores(db, partida, registrar=True)

        # Un bingo DETIENE el sorteo: se pausa para que el encargado pueda
        # acercarse al ganador y acordar el premio. Reanudar es decisión suya.
        #
        # Basta con mirar `nuevo` para no volver a pausar en cada balota
        # posterior: una forma ya ganada queda cerrada y sus ganadores dejan de
        # ser nuevos, así que al reanudar el sorteo sigue sin trabarse.
        #
        # La condición `is EN_CURSO` protege el caso de la balota 75, donde la
        # partida ya quedó finalizada arriba: finalizada no se despausa.
        if partida.estado is EstadoPartida.EN_CURSO and any(
            ganada.nuevo for ganada in cuadro.ganadas
        ):
            partida.estado = EstadoPartida.PAUSADA
            await db.commit()

        if partida.estado is not EstadoPartida.EN_CURSO:
            await gestor.emitir(canal, evento_estado(partida, total))

        return balota


@router.delete("/balotas", status_code=status.HTTP_204_NO_CONTENT)
async def reiniciar_sorteo(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    """Borra las balotas cantadas y devuelve la partida a `pendiente`.

    Es una acción destructiva: existe para poder repetir la demo desde cero. La
    pantalla la pide con confirmación.
    """
    async with _cerrojos[partida_id]:
        partida = await _obtener_partida_o_404(db, partida_id)

        for balota in await _balotas_de(db, partida_id):
            await db.delete(balota)

        # Los ganadores se van con las balotas: si quedaran, sus formas
        # seguirían saliendo como cerradas y nadie podría volver a ganarlas.
        await borrar_ganadores(db, partida_id)

        partida.estado = EstadoPartida.PENDIENTE
        partida.iniciada_en = None
        partida.finalizada_en = None

        await db.commit()
        await _emitir_estado(db, partida)
        await _emitir_ganadores(db, partida, registrar=False)


# --- Transiciones de estado -------------------------------------------------
#
# pendiente → en_curso → (pausada ⇄ en_curso) → finalizada


@router.post("/iniciar", response_model=EstadoSorteo)
async def iniciar_sorteo(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> EstadoSorteo:
    """Arranca el sorteo de una partida pendiente."""
    partida = await _obtener_partida_o_404(db, partida_id)

    if partida.estado is not EstadoPartida.PENDIENTE:
        raise _conflicto(
            f"La partida ya está «{partida.estado.value}»; solo se puede "
            "iniciar una partida pendiente."
        )

    partida.estado = EstadoPartida.EN_CURSO
    partida.iniciada_en = datetime.now(timezone.utc)

    await db.commit()
    await _emitir_estado(db, partida)
    return await estado_del_sorteo(partida_id, db)


@router.post("/pausar", response_model=EstadoSorteo)
async def pausar_sorteo(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> EstadoSorteo:
    """Pausa el sorteo. Las balotas cantadas se conservan."""
    partida = await _obtener_partida_o_404(db, partida_id)

    if partida.estado is not EstadoPartida.EN_CURSO:
        raise _conflicto(
            f"La partida está «{partida.estado.value}»; solo se puede pausar "
            "una partida en curso."
        )

    partida.estado = EstadoPartida.PAUSADA

    await db.commit()
    await _emitir_estado(db, partida)
    return await estado_del_sorteo(partida_id, db)


@router.post("/reanudar", response_model=EstadoSorteo)
async def reanudar_sorteo(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> EstadoSorteo:
    """Reanuda un sorteo pausado."""
    partida = await _obtener_partida_o_404(db, partida_id)

    if partida.estado is not EstadoPartida.PAUSADA:
        raise _conflicto(
            f"La partida está «{partida.estado.value}»; solo se puede reanudar "
            "una partida pausada."
        )

    partida.estado = EstadoPartida.EN_CURSO

    await db.commit()
    await _emitir_estado(db, partida)
    return await estado_del_sorteo(partida_id, db)


@router.post("/finalizar", response_model=EstadoSorteo)
async def finalizar_sorteo(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> EstadoSorteo:
    """Da la partida por terminada antes de agotar las 75 balotas."""
    partida = await _obtener_partida_o_404(db, partida_id)

    if partida.estado is EstadoPartida.FINALIZADA:
        raise _conflicto("La partida ya estaba finalizada.")

    if partida.estado is EstadoPartida.PENDIENTE:
        raise _conflicto("La partida todavía no ha empezado.")

    partida.estado = EstadoPartida.FINALIZADA
    partida.finalizada_en = datetime.now(timezone.utc)

    await db.commit()
    await _emitir_estado(db, partida)
    return await estado_del_sorteo(partida_id, db)
