"""Modelo `ganador` — quién ganó, con qué cartón y con qué forma.

Última entidad que `docs/08-modelo-datos.md` pide para la Fase 1. Versión
simplificada: sin `validado_por`, que necesita la tabla `usuario` de la Fase 2.

Se registra automáticamente al cantar la balota que completa la forma. Es un
hecho histórico: una vez escrito no se toca, solo se borra si se reinicia el
sorteo entero.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Ganador(Base):
    """Un cartón que completó una de las formas de ganar de la partida."""

    __tablename__ = "ganador"
    __table_args__ = (
        # La evaluación corre en CADA balota, así que sin esto un ganador se
        # volvería a registrar en todas las balotas siguientes. El código ya lo
        # evita comprobando antes; esta restricción es la red de seguridad.
        UniqueConstraint(
            "partida_id", "carton_id", "partida_figura_id", name="uq_ganador"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    partida_id: Mapped[int] = mapped_column(
        ForeignKey("partida.id", ondelete="CASCADE"), nullable=False, index=True
    )

    carton_id: Mapped[int] = mapped_column(
        ForeignKey("carton.id", ondelete="CASCADE"), nullable=False, index=True
    )

    #: Qué forma de la partida se completó (y por tanto, qué premio se paga).
    #:
    #: CASCADE hacia `partida_figura` sería una trampa silenciosa: reemplazar la
    #: selección de formas borraría los ganadores sin avisar. Por eso el endpoint
    #: `PUT /formas` se niega (409) en cuanto la partida tiene ganadores.
    partida_figura_id: Mapped[int] = mapped_column(
        ForeignKey("partida_figura.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    #: Balota con la que se completó la forma: su posición en el sorteo y su
    #: número. Guardar las dos permite reconstruir el momento exacto sin volver
    #: a cruzar tablas, y es lo que haría falta para una auditoría.
    orden_balota: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_balota: Mapped[int] = mapped_column(Integer, nullable=False)

    detectado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Ganador partida={self.partida_id} carton={self.carton_id} "
            f"forma={self.partida_figura_id}>"
        )
