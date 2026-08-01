"""Generación y consulta de cartones virtuales (tarea #3 de la Fase 1).

Los cartones cuelgan de una partida. Se generan antes de que empiece el sorteo:
una vez la partida arranca, su juego de cartones no debe cambiar.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dominio.bingo import firma_carton, generar_carton
from app.models.carton import Carton
from app.models.partida import EstadoPartida, Partida
from app.schemas.carton import CartonLeer, GenerarCartones, ResumenCartones

router = APIRouter(prefix="/api/partidas/{partida_id}/cartones", tags=["cartones"])

#: Cuántas veces se reintenta si un cartón generado ya existía en la partida.
#: Con más de 5·10^26 cartones posibles, una colisión es prácticamente
#: imposible; el reintento está por rigor, no porque se espere que ocurra.
MAXIMO_REINTENTOS = 50


async def _obtener_partida_o_404(db: AsyncSession, partida_id: int) -> Partida:
    partida = await db.get(Partida, partida_id)
    if partida is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la partida {partida_id}.",
        )
    return partida


def _exigir_partida_pendiente(partida: Partida, accion: str) -> None:
    """Solo se pueden tocar los cartones antes de que arranque el sorteo.

    Cambiar los cartones con la partida en curso invalidaría los que ya tienen
    los jugadores en la mano.
    """
    if partida.estado is not EstadoPartida.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se pueden {accion} cartones: la partida está "
                f"«{partida.estado.value}». Solo se puede antes de iniciar el sorteo."
            ),
        )


@router.get("", response_model=list[CartonLeer])
async def listar_cartones(
    partida_id: int,
    serie: str | None = None,
    limite: int = Query(default=60, ge=1, le=500),
    desplazamiento: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[Carton]:
    """Devuelve los cartones de la partida, paginados por número."""
    await _obtener_partida_o_404(db, partida_id)

    consulta = select(Carton).where(Carton.partida_id == partida_id)
    if serie is not None:
        consulta = consulta.where(Carton.serie == serie)

    consulta = (
        consulta.order_by(Carton.serie, Carton.numero_carton)
        .offset(desplazamiento)
        .limit(limite)
    )

    return list((await db.execute(consulta)).scalars().all())


@router.get("/resumen", response_model=ResumenCartones)
async def resumen_cartones(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> ResumenCartones:
    """Cuántos cartones hay y cómo se reparten por serie."""
    await _obtener_partida_o_404(db, partida_id)

    filas = (
        await db.execute(
            select(Carton.serie, func.count())
            .where(Carton.partida_id == partida_id)
            .group_by(Carton.serie)
            .order_by(Carton.serie)
        )
    ).all()

    por_serie = {serie: total for serie, total in filas}
    return ResumenCartones(total=sum(por_serie.values()), por_serie=por_serie)


@router.get("/{serie}/{numero_carton}", response_model=CartonLeer)
async def obtener_carton_por_codigo(
    partida_id: int,
    serie: str,
    numero_carton: int,
    db: AsyncSession = Depends(get_db),
) -> Carton:
    """Busca un cartón por su código visible dentro de la partida (ej. A-7).

    Es como llega el jugador a su cartón en la Fase 1: escribiendo el código que
    tiene a mano, sin login. La búsqueda de la serie ignora mayúsculas para que
    «a-7» funcione igual que «A-7» al teclearlo desde un celular.
    """
    await _obtener_partida_o_404(db, partida_id)

    carton = (
        await db.execute(
            select(Carton).where(
                Carton.partida_id == partida_id,
                func.lower(Carton.serie) == serie.lower(),
                Carton.numero_carton == numero_carton,
            )
        )
    ).scalar_one_or_none()

    if carton is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el cartón {serie.upper()}-{numero_carton} en esta partida.",
        )

    return carton


@router.post("", response_model=list[CartonLeer], status_code=status.HTTP_201_CREATED)
async def generar_cartones(
    partida_id: int,
    datos: GenerarCartones,
    db: AsyncSession = Depends(get_db),
) -> list[Carton]:
    """Genera cartones nuevos para la partida y los devuelve.

    Los cartones son únicos dentro de la partida: se compara la firma de cada
    uno contra las que ya existen y contra las de esta misma tanda.
    """
    partida = await _obtener_partida_o_404(db, partida_id)
    _exigir_partida_pendiente(partida, "generar")

    # Firmas ya usadas en la partida, para no repetir un cartón.
    firmas: set[str] = set(
        (
            await db.execute(
                select(Carton.firma).where(Carton.partida_id == partida_id)
            )
        )
        .scalars()
        .all()
    )

    # El consecutivo sigue donde quedó la serie, no se reinicia.
    ultimo = (
        await db.execute(
            select(func.max(Carton.numero_carton)).where(
                Carton.partida_id == partida_id, Carton.serie == datos.serie
            )
        )
    ).scalar() or 0

    nuevos: list[Carton] = []
    for posicion in range(datos.cantidad):
        for intento in range(MAXIMO_REINTENTOS):
            matriz = generar_carton()
            firma = firma_carton(matriz)
            if firma not in firmas:
                break
        else:
            # Inalcanzable en la práctica; si pasara, es preferible fallar
            # ruidosamente a guardar un cartón repetido.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"No se pudo generar un cartón único tras "
                    f"{MAXIMO_REINTENTOS} intentos."
                ),
            )

        firmas.add(firma)
        nuevos.append(
            Carton(
                partida_id=partida_id,
                serie=datos.serie,
                numero_carton=ultimo + posicion + 1,
                numeros=matriz,
                firma=firma,
            )
        )

    db.add_all(nuevos)
    await db.commit()

    for carton in nuevos:
        await db.refresh(carton)

    return nuevos


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_cartones(
    partida_id: int,
    serie: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Borra los cartones de la partida (todos, o solo los de una serie)."""
    partida = await _obtener_partida_o_404(db, partida_id)
    _exigir_partida_pendiente(partida, "eliminar")

    consulta = select(Carton).where(Carton.partida_id == partida_id)
    if serie is not None:
        consulta = consulta.where(Carton.serie == serie)

    for carton in (await db.execute(consulta)).scalars().all():
        await db.delete(carton)

    await db.commit()
