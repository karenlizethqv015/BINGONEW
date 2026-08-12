"""Modelo `partida` — versión simplificada de la Fase 1.

El modelo completo (docs/08-modelo-datos.md) cuelga la partida de una jornada y
esta de una sala, y guarda quién la creó. Nada de eso existe todavía: jornada,
sala y usuario son de la Fase 2. Aquí la partida es una entidad suelta, con lo
mínimo para que se le puedan asociar formas de ganar, cartones y balotas.

Tampoco se incluyen los indicadores de Progresivo, Loco Bingo ni Reyes: son de
la Fase 3 y están explícitamente fuera de alcance (ver CLAUDE.md).
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class EstadoPartida(str, Enum):
    """Ciclo de vida de una partida."""

    PENDIENTE = "pendiente"
    EN_CURSO = "en_curso"
    PAUSADA = "pausada"
    FINALIZADA = "finalizada"


#: Se guarda como texto (native_enum=False) y no como el tipo ENUM nativo del
#: motor: SQLite no tiene ENUM, y en PostgreSQL cambiar sus valores exige una
#: migración incómoda. Como texto con CHECK funciona igual en los dos.
TipoEstadoPartida = SQLEnum(
    EstadoPartida,
    native_enum=False,
    values_callable=lambda enum: [miembro.value for miembro in enum],
    length=20,
)


class Partida(Base):
    """Una partida de bingo."""

    __tablename__ = "partida"
    #: AUTOINCREMENT hace que SQLite no reutilice el id de una fila borrada
    #: (por defecto sí lo reutiliza). Las secuencias de PostgreSQL ya se
    #: comportan así. Es lo que permite derivar de él un consecutivo que nunca
    #: se repite — ver `numero_consecutivo`.
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    #: Consecutivo visible ("Juego No." en la app anterior). Lo asigna el
    #: backend a partir del id, para que **nunca se reutilice**: si se borra la
    #: última partida, la siguiente no debe repetir su número o el historial de
    #: ganadores quedaría ambiguo.
    #: En la Fase 2, cuando exista `jornada`, pasa a ser un consecutivo diario
    #: por jornada y dejará de coincidir con el id.
    numero_consecutivo: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)

    estado: Mapped[EstadoPartida] = mapped_column(
        TipoEstadoPartida, nullable=False, default=EstadoPartida.PENDIENTE
    )

    #: Precio del cartón, en pesos colombianos enteros (el peso no usa
    #: centavos en la práctica).
    precio_carton: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    #: Segundos entre balota y balota cuando el sorteo corre en automático.
    #: Lo usará la balotera en la tarea #4.
    duracion_segundos_entre_balota: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5
    )

    #: Si todavía se están vendiendo cartones para esta partida.
    #:
    #: Es independiente del `estado` del sorteo: una partida puede seguir
    #: `pendiente` o `en_curso` con la venta ya cerrada. Lo enciende y apaga el
    #: operador desde su panel; el "bombillo" de `/transmision` es de solo
    #: lectura sobre este campo.
    venta_abierta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    iniciada_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finalizada_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    #: Formas de ganar elegidas para esta partida, en su orden de juego.
    #: delete-orphan: al borrar la partida se borran sus selecciones, que no
    #: tienen sentido por separado. Las figuras del catálogo NO se tocan.
    figuras: Mapped[list["PartidaFigura"]] = relationship(  # noqa: F821
        back_populates="partida",
        cascade="all, delete-orphan",
        order_by="PartidaFigura.orden",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Partida id={self.id} numero={self.numero_consecutivo}>"
