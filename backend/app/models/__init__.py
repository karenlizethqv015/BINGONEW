"""Modelos del ORM.

Todo modelo nuevo debe importarse aquí. Alembic solo detecta las tablas que
estén registradas en `Base.metadata` al autogenerar migraciones; si un modelo no
aparece en este módulo, su migración saldrá **vacía y sin ningún error**.
"""

from app.db import Base
from app.models.carton import Carton
from app.models.figura import Figura, TipoFigura
from app.models.partida import EstadoPartida, Partida
from app.models.partida_figura import PartidaFigura

__all__ = [
    "Base",
    "Carton",
    "EstadoPartida",
    "Figura",
    "Partida",
    "PartidaFigura",
    "TipoFigura",
]
