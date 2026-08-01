"""Modelos del ORM.

Todo modelo nuevo debe importarse aquí. Alembic solo detecta las tablas que
estén registradas en `Base.metadata` al autogenerar migraciones; si un modelo no
aparece en este módulo, su migración saldrá **vacía y sin ningún error**.
"""

from app.db import Base
from app.models.figura import Figura
from app.models.partida import EstadoPartida, Partida
from app.models.partida_figura import PartidaFigura, TipoPremio

__all__ = [
    "Base",
    "EstadoPartida",
    "Figura",
    "Partida",
    "PartidaFigura",
    "TipoPremio",
]
