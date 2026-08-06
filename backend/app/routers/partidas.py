"""Partidas y su selección de formas de ganar (tarea #2 de la Fase 1).

La partida es la versión simplificada de la Fase 1: sin jornada, sin sala y sin
usuario creador. Ver `app/models/partida.py`.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.balota_cantada import BalotaCantada
from app.seguridad import SOLO_ADMIN
from app.models.figura import Figura
from app.models.ganador import Ganador
from app.models.partida import EstadoPartida, Partida
from app.models.partida_figura import PartidaFigura
from app.realtime.eventos import canal_de_partida, evento_sincronizacion
from app.realtime.manager import gestor
from app.schemas.partida import (
    PartidaActualizar,
    PartidaCrear,
    PartidaLeer,
    SeleccionDeFormas,
)

router = APIRouter(
    prefix="/api/partidas", tags=["partidas"], dependencies=SOLO_ADMIN
)


async def _balotas_de(db: AsyncSession, partida_id: int) -> list[BalotaCantada]:
    """Balotas cantadas, en orden. La sincronización las lleva todas."""
    resultado = await db.execute(
        select(BalotaCantada)
        .where(BalotaCantada.partida_id == partida_id)
        .order_by(BalotaCantada.orden)
    )
    return list(resultado.scalars().all())


async def _obtener_o_404(db: AsyncSession, partida_id: int) -> Partida:
    partida = await db.get(Partida, partida_id)
    if partida is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la partida {partida_id}.",
        )
    return partida


@router.get("", response_model=list[PartidaLeer])
async def listar_partidas(db: AsyncSession = Depends(get_db)) -> list[Partida]:
    """Devuelve las partidas, de la más reciente a la más antigua."""
    resultado = await db.execute(
        select(Partida).order_by(Partida.numero_consecutivo.desc())
    )
    return list(resultado.scalars().all())


@router.get("/{partida_id}", response_model=PartidaLeer)
async def obtener_partida(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> Partida:
    return await _obtener_o_404(db, partida_id)


@router.post("", response_model=PartidaLeer, status_code=status.HTTP_201_CREATED)
async def crear_partida(
    datos: PartidaCrear, db: AsyncSession = Depends(get_db)
) -> Partida:
    """Crea una partida y le asigna su consecutivo.

    El consecutivo se deriva del id, no de `MAX(numero_consecutivo) + 1`: con el
    máximo, borrar la última partida haría que la siguiente repitiera su número,
    y dos partidas con el mismo "Juego No." serían indistinguibles en el
    historial. El id nunca se reutiliza (ver `Partida.__table_args__`).
    """
    partida = Partida(
        # Valor provisional: el definitivo necesita el id, que solo existe
        # después del flush.
        numero_consecutivo=0,
        precio_carton=datos.precio_carton,
        duracion_segundos_entre_balota=datos.duracion_segundos_entre_balota,
    )
    db.add(partida)
    await db.flush()

    partida.numero_consecutivo = partida.id

    await db.commit()
    await db.refresh(partida)
    return partida


@router.put("/{partida_id}", response_model=PartidaLeer)
async def actualizar_partida(
    partida_id: int, datos: PartidaActualizar, db: AsyncSession = Depends(get_db)
) -> Partida:
    """Edita el precio del cartón y el tiempo entre balotas.

    El tiempo entre balotas se puede cambiar **con el sorteo en curso**: es el
    cronómetro que el administrador ajusta según cómo vaya la sala. Por eso al
    guardarlo se emite la sincronización: el reloj del sorteo automático vive en
    el navegador (ver PROGRESS.md), así que si no se avisa, la balotera seguiría
    cantando al ritmo viejo hasta que alguien recargue la página.
    """
    partida = await _obtener_o_404(db, partida_id)

    if datos.precio_carton is not None:
        partida.precio_carton = datos.precio_carton
    if datos.duracion_segundos_entre_balota is not None:
        partida.duracion_segundos_entre_balota = datos.duracion_segundos_entre_balota

    await db.commit()
    await db.refresh(partida)

    await gestor.emitir(
        canal_de_partida(partida.id),
        evento_sincronizacion(partida, await _balotas_de(db, partida_id)),
    )

    return partida


@router.delete("/{partida_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_partida(
    partida_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    """Borra una partida y, con ella, su selección de formas.

    Las figuras del catálogo no se tocan: solo se borra la asociación.
    """
    partida = await _obtener_o_404(db, partida_id)
    await db.delete(partida)
    await db.commit()


@router.put("/{partida_id}/formas", response_model=PartidaLeer)
async def definir_formas(
    partida_id: int,
    seleccion: SeleccionDeFormas,
    db: AsyncSession = Depends(get_db),
) -> Partida:
    """Reemplaza las formas de ganar de una partida por la lista recibida.

    El `orden` se toma de la posición en la lista y es solo de presentación:
    todas las formas de la partida juegan al mismo tiempo, y gana quien complete
    cualquiera de ellas.
    """
    partida = await _obtener_o_404(db, partida_id)

    if partida.estado is EstadoPartida.FINALIZADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pueden cambiar las formas de ganar de una partida finalizada.",
        )

    # Reemplazar la selección borra las filas de `partida_figura`, y `ganador`
    # apunta a ellas: seguir adelante borraría los ganadores en cascada y en
    # silencio. Es mejor negarse con un mensaje claro que destruir el registro de
    # quién ganó. Para rehacer la selección hay que reiniciar el sorteo.
    ya_hay_ganadores = (
        await db.execute(
            select(func.count())
            .select_from(Ganador)
            .where(Ganador.partida_id == partida_id)
        )
    ).scalar_one()

    if ya_hay_ganadores:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se pueden cambiar las formas de ganar: la partida ya tiene "
                "ganadores registrados. Reinicia el sorteo si necesitas rehacer "
                "la selección."
            ),
        )

    # Se comprueba que todas las figuras existan ANTES de tocar nada, para no
    # dejar la selección a medio reemplazar si una referencia es inválida.
    ids_pedidos = [forma.figura_id for forma in seleccion.formas]
    if ids_pedidos:
        encontrados = (
            await db.execute(select(Figura.id).where(Figura.id.in_(ids_pedidos)))
        ).scalars().all()

        faltantes = sorted(set(ids_pedidos) - set(encontrados))
        if faltantes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No existen estas figuras: "
                    + ", ".join(str(i) for i in faltantes)
                    + "."
                ),
            )

    # delete-orphan se encarga de borrar las selecciones anteriores, pero el
    # flush hace falta ANTES de agregar las nuevas: en un mismo flush,
    # SQLAlchemy emite los INSERT antes que los DELETE, y si una figura estaba
    # ya seleccionada (lo normal al reordenar o cambiar un premio) chocaría
    # contra el índice único (partida_id, figura_id).
    partida.figuras.clear()
    await db.flush()

    for posicion, forma in enumerate(seleccion.formas, start=1):
        partida.figuras.append(
            PartidaFigura(
                figura_id=forma.figura_id,
                valor_premio=forma.valor_premio,
                orden=posicion,
            )
        )

    await db.commit()
    await db.refresh(partida)
    return partida
