"""Modelos del ORM.

Vacío a propósito en la Fase 0: el scaffolding no implementa nada de negocio.

Cuando se creen los modelos de la Fase 1 (`figura`, `partida`, `partida_figura`,
`carton`, `balota_cantada`, `ganador` — ver docs/08-modelo-datos.md), cada uno
debe importarse aquí. Alembic solo detecta las tablas que estén importadas en
este módulo al autogenerar migraciones; si un modelo no aparece, su migración
saldrá vacía sin avisar.

Ejemplo cuando existan:
    from app.models.figura import Figura  # noqa: F401
"""

from app.db import Base  # noqa: F401  (reexportado para que Alembic lo encuentre)

__all__ = ["Base"]
