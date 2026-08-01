"""Modelo `partida_figura` — qué formas de ganar se juegan en una partida.

Tabla intermedia entre `partida` y `figura`, con el premio de cada forma. Es lo
que en la app anterior era la pantalla "Configurar/Editar Juego": de todo el
catálogo de figuras, cuáles juegan hoy, con qué premio y en qué orden.
"""

from enum import Enum

from sqlalchemy import (
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.figura import Figura
from app.models.partida import Partida


class TipoPremio(str, Enum):
    """Categoría con la que se agrupa una forma de ganar dentro de la partida.

    Es **puramente organizativa** (confirmado con la usuaria, 2026-07-30): sirve
    para que el administrador encuentre y ordene las formas al armar la partida.
    NO cambia cómo se gana ni cuánto se paga:

    - **Cómo se gana** lo define el patrón de la figura asociada, y solo eso.
    - **Cuánto se paga** lo define `valor_premio`, propio de cada forma.

    Tampoco son etapas sucesivas: todas las formas de la partida juegan **al
    mismo tiempo**, y gana quien complete cualquiera de ellas.

    Que la categoría se guarde aquí y no en `figura` es intencional: una figura
    no pertenece a una categoría de forma permanente, se clasifica partida por
    partida.
    """

    SENCILLO = "sencillo"
    FIGURA = "figura"
    PLENO = "pleno"


#: Como texto y no como ENUM nativo, por el mismo motivo que en `partida`.
TipoTipoPremio = SQLEnum(
    TipoPremio,
    native_enum=False,
    values_callable=lambda enum: [miembro.value for miembro in enum],
    length=20,
)


class PartidaFigura(Base):
    """Una forma de ganar seleccionada para una partida, con su premio."""

    __tablename__ = "partida_figura"
    __table_args__ = (
        # Una misma figura no puede elegirse dos veces en la misma partida.
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

    tipo_premio: Mapped[TipoPremio] = mapped_column(
        TipoTipoPremio, nullable=False, default=TipoPremio.FIGURA
    )

    #: Valor del premio de ESTA forma, en pesos colombianos enteros. Cada forma
    #: tiene el suyo; la categoría no influye en él.
    valor_premio: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    #: Orden de **presentación**, no de juego: todas las formas de la partida
    #: juegan a la vez. Solo sirve para que la lista se muestre siempre igual.
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    partida: Mapped[Partida] = relationship(back_populates="figuras")

    #: lazy="joined": la selección casi siempre se lee para mostrar el nombre y
    #: el patrón de la figura, así que se trae en la misma consulta.
    figura: Mapped[Figura] = relationship(lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<PartidaFigura partida={self.partida_id} "
            f"figura={self.figura_id} orden={self.orden}>"
        )
