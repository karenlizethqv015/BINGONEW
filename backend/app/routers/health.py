"""Endpoint de salud: sirve para verificar que la API y la base de datos responden."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db

router = APIRouter(prefix="/api", tags=["sistema"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Devuelve el estado de la API y si la base de datos está accesible.

    El frontend lo consume en la vista de administración para confirmar que el
    proxy de Vite y el backend están bien conectados.
    """
    try:
        await db.execute(text("SELECT 1"))
        base_datos_ok = True
    except Exception:
        # No se propaga el error: el objetivo de este endpoint es reportar el
        # estado, no fallar. Un 200 con base_datos=False es información útil.
        base_datos_ok = False

    return {
        "estado": "ok",
        "servicio": settings.app_nombre,
        "version": settings.app_version,
        "base_datos": base_datos_ok,
        # Se reporta solo el motor, nunca la cadena completa: puede llevar
        # credenciales cuando se use PostgreSQL.
        "motor_bd": settings.database_url.split("://", 1)[0],
    }
