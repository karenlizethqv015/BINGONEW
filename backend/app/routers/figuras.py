"""CRUD del catálogo de figuras (formas de ganar).

Es un catálogo global, independiente de las partidas: las figuras se crean una
vez y se reutilizan. Elegir cuáles juegan en una partida y con qué premio es la
tarea #2 (tabla `partida_figura`).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.figura import Figura
from app.models.partida_figura import PartidaFigura
from app.schemas.figura import FiguraActualizar, FiguraCrear, FiguraLeer

router = APIRouter(prefix="/api/figuras", tags=["figuras"])


async def _obtener_o_404(db: AsyncSession, figura_id: int) -> Figura:
    """Busca una figura o corta con 404."""
    figura = await db.get(Figura, figura_id)
    if figura is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la figura {figura_id}.",
        )
    return figura


async def _comprobar_nombre_libre(
    db: AsyncSession, nombre: str, excluir_id: int | None = None
) -> None:
    """Corta con 409 si ya hay otra figura con ese nombre.

    La comparación ignora mayúsculas para que el administrador no termine con
    "Línea" y "línea" como dos figuras distintas del catálogo.
    """
    consulta = select(Figura.id).where(func.lower(Figura.nombre) == nombre.lower())
    if excluir_id is not None:
        consulta = consulta.where(Figura.id != excluir_id)

    if (await db.execute(consulta)).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una figura llamada «{nombre}».",
        )


@router.get("", response_model=list[FiguraLeer])
async def listar_figuras(db: AsyncSession = Depends(get_db)) -> list[Figura]:
    """Devuelve el catálogo completo, de la más reciente a la más antigua."""
    resultado = await db.execute(select(Figura).order_by(Figura.creado_en.desc()))
    return list(resultado.scalars().all())


@router.get("/{figura_id}", response_model=FiguraLeer)
async def obtener_figura(
    figura_id: int, db: AsyncSession = Depends(get_db)
) -> Figura:
    """Devuelve una figura por su id."""
    return await _obtener_o_404(db, figura_id)


@router.post("", response_model=FiguraLeer, status_code=status.HTTP_201_CREATED)
async def crear_figura(
    datos: FiguraCrear, db: AsyncSession = Depends(get_db)
) -> Figura:
    """Guarda una figura nueva en el catálogo."""
    await _comprobar_nombre_libre(db, datos.nombre)

    figura = Figura(nombre=datos.nombre, patron=datos.patron)
    db.add(figura)
    await db.commit()
    await db.refresh(figura)
    return figura


@router.put("/{figura_id}", response_model=FiguraLeer)
async def actualizar_figura(
    figura_id: int, datos: FiguraActualizar, db: AsyncSession = Depends(get_db)
) -> Figura:
    """Edita el nombre y/o el patrón de una figura."""
    figura = await _obtener_o_404(db, figura_id)

    if datos.nombre is not None:
        await _comprobar_nombre_libre(db, datos.nombre, excluir_id=figura_id)
        figura.nombre = datos.nombre

    if datos.patron is not None:
        figura.patron = datos.patron

    await db.commit()
    await db.refresh(figura)
    return figura


@router.delete("/{figura_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_figura(figura_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Borra una figura del catálogo, si ninguna partida la está usando.

    Borrar una figura ya seleccionada en una partida dejaría huérfano el
    historial de ganadores, así que se responde 409 en lugar de borrarla. La
    llave foránea de `partida_figura` es RESTRICT como última defensa, pero se
    comprueba aquí para poder dar un mensaje entendible.
    """
    figura = await _obtener_o_404(db, figura_id)

    partidas_que_la_usan = (
        await db.execute(
            select(func.count())
            .select_from(PartidaFigura)
            .where(PartidaFigura.figura_id == figura_id)
        )
    ).scalar_one()

    if partidas_que_la_usan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede eliminar «{figura.nombre}»: está seleccionada en "
                f"{partidas_que_la_usan} "
                f"{'partida' if partidas_que_la_usan == 1 else 'partidas'}. "
                "Quítala de la partida primero."
            ),
        )

    await db.delete(figura)
    await db.commit()
