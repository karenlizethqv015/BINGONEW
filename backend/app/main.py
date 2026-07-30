"""Punto de entrada de la API del Bingo.

Levantar en desarrollo desde la carpeta `backend/`:
    .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import engine
from app.realtime.manager import gestor
from app.routers import health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Arranque y apagado ordenado de la aplicación."""
    logger.info("Iniciando %s v%s", settings.app_nombre, settings.app_version)
    yield
    # Cierra el pool de conexiones para que uvicorn no quede colgado al parar.
    await engine.dispose()
    logger.info("Backend detenido")


app = FastAPI(
    title=settings.app_nombre,
    version=settings.app_version,
    description="API de la plataforma web de bingo en vivo.",
    lifespan=lifespan,
)

# En desarrollo el frontend corre en otro puerto (Vite, 5173), así que necesita
# CORS. En la instalación final en LAN ambos se sirven desde el mismo origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)


@app.websocket("/ws/echo")
async def websocket_echo(websocket: WebSocket) -> None:
    """Canal WebSocket de prueba: devuelve lo que recibe.

    Existe solo para verificar de punta a punta que el canal en tiempo real
    funciona (backend, proxy de Vite y cliente). NO es la balotera: en la Fase 1
    se agrega el endpoint real `/ws/partida/{partida_id}`, que reutilizará el
    mismo `GestorConexiones`.
    """
    canal = "echo"
    await gestor.conectar(canal, websocket)

    try:
        await websocket.send_json(
            {
                "tipo": "conectado",
                "mensaje": "Canal en tiempo real activo",
                "conexiones": gestor.total_conexiones(canal),
            }
        )
        while True:
            recibido = await websocket.receive_text()
            await websocket.send_json({"tipo": "eco", "mensaje": recibido})
    except WebSocketDisconnect:
        # Desconexión normal del cliente: no es un error.
        pass
    finally:
        await gestor.desconectar(canal, websocket)
