"""Modelo `partida_figura` — qué formas de ganar se juegan en una partida.

Tabla intermedia entre `partida` y `figura`, con el premio de cada forma. Es lo
que en la app anterior era la pantalla "Configurar/Editar Juego": de todo el
catálogo de figuras, cuáles juegan hoy y con qué premio.

La categoría (sencillo/figura/pleno) NO está aquí: es una propiedad de la figura
en el catálogo, ver `app/models/figura.py`.
"""

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.figura import Figura
from app.models.partida import Partida


class PartidaFigura(Base):
    """Una forma de ganar seleccionada para una partida, con su premio."""

    __tablename__ = "partida_figura"
    __table_args__ = (
        # Una misma figura no puede elegirse dos veces en la misma partida: si
        # un cartón la completara, no se sabría qué premio corresponde.
        UniqueConstraint("partida_id", "figura_id", name="uq_partida_figura"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    partida_id: Mapped[int] = mapped_column(
        ForeignKey("partida.id", ondelete="CASCADE"), nullable=False, index=True
    )

    #: RESTRICT, no CASCADE: borrar del catálogo una figura que ya se jugó
    #: destruiría el historial de ganadores. El endpoint de borrado de figuras
    #: lo comprueba antes y responde 409 con un mensaje claro; esta restricción
    #: es la última línea de defensa a nivel de base de datos.
    figura_id: Mapped[int] = mapped_column(
        ForeignKey("figura.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    #: Valor del premio de ESTA forma, en pesos colombianos enteros. Cada forma
    #: tiene el suyo y son independientes entre sí.
    valor_premio: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    #: Orden de **presentación**, no de juego: todas las formas de la partida
    #: juegan a la vez. Solo sirve para que la lista se muestre siempre igual.
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    partida: Mapped[Partida] = relationship(back_populates="figuras")

    #: lazy="joined": la selección casi siempre se lee para mostrar el nombre,
    #: el patrón y el tipo de la figura, así que se trae en la misma consulta.
    figura: Mapped[Figura] = relationship(lazy="joined")

    def __repr__(self) -> str:
        return f"<PartidaFigura partida={self.partida_id} figura={self.figura_id}>"
