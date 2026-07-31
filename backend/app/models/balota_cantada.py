"""Modelo `balota_cantada` — historial de balotas de una partida.

Toda balota queda registrada aquí con su orden y su timestamp, **venga de la
balotera virtual o de una balotera física**. Es lo que evita duplicar la lógica
cuando más adelante se integre la balotera real: cambia quién saca el número,
no dónde se guarda ni qué se emite.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.dominio.bingo import TOTAL_BALOTAS


class BalotaCantada(Base):
    """Una balota que ya salió en una partida."""

    __tablename__ = "balota_cantada"
    __table_args__ = (
        # El sorteo es SIN REEMPLAZO. El código ya lo garantiza al sortear solo
        # entre las restantes; este índice lo vuelve imposible de romper aunque
        # dos peticiones simultáneas se colaran.
        UniqueConstraint("partida_id", "numero", name="uq_balota_numero"),
        # No puede haber dos balotas en la misma posición de la secuencia.
        UniqueConstraint("partida_id", "orden", name="uq_balota_orden"),
        CheckConstraint(
            f"numero >= 1 AND numero <= {TOTAL_BALOTAS}", name="ck_balota_rango"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    partida_id: Mapped[int] = mapped_column(
        ForeignKey("partida.id", ondelete="CASCADE"), nullable=False, index=True
    )

    #: Número de la balota, de 1 a 75.
    numero: Mapped[int] = mapped_column(Integer, nullable=False)

    #: Posición en la secuencia del sorteo, empezando en 1.
    orden: Mapped[int] = mapped_column(Integer, nullable=False)

    cantada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<BalotaCantada partida={self.partida_id} "
            f"numero={self.numero} orden={self.orden}>"
        )
