"""Modelo `figura`: catálogo global de formas de ganar.

Una figura es un patrón de 5x5 (por ejemplo "línea horizontal", "X", "cuatro
esquinas") que el administrador diseña una vez y reutiliza en cualquier partida.
Es un catálogo global: no pertenece a ninguna partida en particular. La
asociación figura ↔ partida, con su premio, es la tabla `partida_figura` de la
tarea #2 (ver docs/08-modelo-datos.md).
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.dominio.bingo import Patron


class TipoFigura(str, Enum):
    """Categoría con la que el administrador clasifica una figura del catálogo.

    Es **puramente organizativa**: sirve para encontrar las figuras al armar una
    partida. No cambia cómo se gana (eso lo define el patrón) ni cuánto se paga
    (eso lo define el premio, que se fija por partida y es propio de cada forma).

    Vive en la figura y no en `partida_figura` porque la clasificación es una
    propiedad estable del catálogo: el administrador la define una vez, y al
    configurar una partida cada categoría le ofrece solo las figuras que él
    mismo clasificó ahí.
    """

    SENCILLO = "sencillo"
    FIGURA = "figura"
    PLENO = "pleno"


#: Se guarda como texto y no como el ENUM nativo del motor: SQLite no lo tiene y
#: en PostgreSQL cambiar sus valores obliga a una migración incómoda.
TipoTipoFigura = SQLEnum(
    TipoFigura,
    native_enum=False,
    values_callable=lambda enum: [miembro.value for miembro in enum],
    length=20,
)


class Figura(Base):
    """Una forma de ganar del catálogo."""

    __tablename__ = "figura"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    #: Nombre visible. Único para evitar catálogos con figuras duplicadas.
    #: El router además compara sin distinguir mayúsculas ni acentos de más,
    #: porque el índice único de la base sí distingue.
    nombre: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)

    #: Matriz 5x5 de booleanos. Se usa el tipo JSON genérico de SQLAlchemy —
    #: NUNCA JSONB — para que el modelo siga funcionando igual en SQLite (demo)
    #: y en PostgreSQL (producción en LAN). Ver backend/README.md.
    patron: Mapped[Patron] = mapped_column(JSON, nullable=False)

    #: Categoría del catálogo. Determina en cuál de las tres listas aparece la
    #: figura al configurar una partida.
    #: `server_default` además del `default` de Python: mantiene el modelo y la
    #: base sincronizados (si no, Alembic propone quitarlo en cada migración) y
    #: deja la columna a salvo de un INSERT que no pase por el ORM.
    tipo: Mapped[TipoFigura] = mapped_column(
        TipoTipoFigura,
        nullable=False,
        default=TipoFigura.FIGURA,
        server_default=TipoFigura.FIGURA.value,
        index=True,
    )

    #: Usuario que la creó. Queda nullable y SIN llave foránea a propósito: la
    #: tabla `usuario` es de la Fase 2 y todavía no existe. Al implementar el
    #: login habrá que agregar la FK en una migración.
    creado_por_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Figura id={self.id} nombre={self.nombre!r}>"
