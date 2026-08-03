"""Punto de entrada de la API del Bingo.

Levantar en desarrollo desde la carpeta `backend/`:
    .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.db import engine, get_sesion_factory
from app.models.balota_cantada import BalotaCantada
from app.models.partida import Partida
from app.realtime.eventos import (
    canal_de_partida,
    evento_ganadores,
    evento_sincronizacion,
)
from app.realtime.manager import gestor
from app.routers import balotas, cartones, figuras, health, partidas
from app.servicios.ganadores import evaluar_partida

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
app.include_router(figuras.router)
app.include_router(partidas.router)
app.include_router(cartones.router)
app.include_router(balotas.router)


@app.websocket("/ws/partida/{partida_id}")
async def websocket_partida(
    websocket: WebSocket,
    partida_id: int,
    sesion_factory: async_sessionmaker[AsyncSession] = Depends(get_sesion_factory),
) -> None:
    """Canal en tiempo real de una partida.

    **Un endpoint por partida**, como fija CLAUDE.md: el tablero de transmisión,
    el cartón del jugador y el panel del administrador se conectan todos aquí y
    reaccionan al mismo evento de balota.

    Nada más conectarse se envían dos fotos completas: la sincronización con el
    estado y todas las balotas ya cantadas, y el cuadro de ganadores. Con las dos,
    una pantalla que llega tarde o que se reconecta reconstruye todo sin pedir
    nada más. Después el canal es de una sola dirección: el servidor emite y el
    cliente solo escucha.

    La sesión de base de datos se abre y se cierra aquí mismo: la conexión puede
    durar horas y no debe retener una conexión a la base todo ese tiempo.
    """
    async with sesion_factory() as sesion:
        partida = await sesion.get(Partida, partida_id)
        if partida is None:
            # 1008 = "policy violation"; el cliente no debe reintentar con este
            # identificador porque la partida no existe.
            await websocket.close(code=1008, reason="La partida no existe")
            return

        balotas_cantadas = list(
            (
                await sesion.execute(
                    select(BalotaCantada)
                    .where(BalotaCantada.partida_id == partida_id)
                    .order_by(BalotaCantada.orden)
                )
            )
            .scalars()
            .all()
        )
        sincronizacion = evento_sincronizacion(partida, balotas_cantadas)

        # Solo consulta: los ganadores se registran al cantar la balota, no
        # porque alguien abra una pantalla.
        cuadro, orden = await evaluar_partida(sesion, partida_id, registrar=False)
        ganadores = evento_ganadores(partida, cuadro, orden)

    canal = canal_de_partida(partida_id)
    await gestor.conectar(canal, websocket)

    try:
        await websocket.send_json(sincronizacion)
        await websocket.send_json(ganadores)
        while True:
            # No se espera nada del cliente; recibir es la forma de enterarse de
            # que se desconectó.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await gestor.desconectar(canal, websocket)


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
