"""Modelo `carton` — cartón virtual de bingo.

Versión simplificada de la Fase 1: sin `modulo_id`, sin `jugador_id` y sin los
campos de venta (`vendido`, `vendido_por`, `vendido_en`). Los paquetes de
cartones y el módulo de ventas son de la Fase 2 (ver docs/08-modelo-datos.md).
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.dominio.bingo import Carton as MatrizCarton


class Carton(Base):
    """Un cartón virtual perteneciente a una partida."""

    __tablename__ = "carton"
    __table_args__ = (
        # Identificación visible del cartón dentro de la partida.
        UniqueConstraint("partida_id", "serie", "numero_carton", name="uq_carton_numero"),
        # Garantiza a nivel de base de datos que no haya dos cartones iguales en
        # la misma partida, pase lo que pase en el código que los genera.
        UniqueConstraint("partida_id", "firma", name="uq_carton_firma"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    partida_id: Mapped[int] = mapped_column(
        ForeignKey("partida.id", ondelete="CASCADE"), nullable=False, index=True
    )

    #: Serie a la que pertenece el cartón. Agrupa tandas de generación.
    serie: Mapped[str] = mapped_column(String(8), nullable=False, default="A")

    #: Consecutivo dentro de la partida y la serie, empezando en 1.
    numero_carton: Mapped[int] = mapped_column(Integer, nullable=False)

    #: Matriz 5x5 con los números, y `null` en la casilla libre del centro.
    #: Tipo JSON genérico, nunca JSONB, por compatibilidad con PostgreSQL.
    numeros: Mapped[MatrizCarton] = mapped_column(JSON, nullable=False)

    #: Huella del cartón (sha256). Existe solo para poder imponer el índice
    #: único de arriba: comparar la matriz JSON directamente no es portable
    #: entre SQLite y PostgreSQL.
    firma: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Carton partida={self.partida_id} "
            f"{self.serie}-{self.numero_carton}>"
        )
