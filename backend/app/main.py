"""Punto de entrada de la API del Bingo.

Levantar en desarrollo desde la carpeta `backend/`:
    .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
from app.seguridad import CABECERA_ROL_REQUERIDO
from app.servicios.ganadores import cuadro_recordado, evaluar_partida

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
    # Sin esto, el navegador descarta la cabecera `X-Clave-Requerida` de las
    # respuestas 401 en el caso cross-origin (no hace falta con el proxy de
    # Vite, que es same-origin, pero sí si algún día el frontend habla con el
    # backend desde otro puerto sin proxy).
    expose_headers=[CABECERA_ROL_REQUERIDO],
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

        # El cuadro que le toca a quien llega es exactamente el último que se
        # emitió, así que se reutiliza en vez de recalcularlo: en una sala llena
        # son cientos de jugadores conectándose casi a la vez, y evaluar una
        # partida de 5000 cartones para cada uno bloquearía el servidor durante
        # segundos. Solo se calcula si aún no se ha emitido ninguno.
        ganadores = cuadro_recordado(partida_id)
        if ganadores is None:
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


# --- Frontend compilado ------------------------------------------------------
#
# Va al FINAL a propósito: la ruta comodín de abajo captura cualquier dirección,
# así que todo lo de la API tiene que estar registrado antes.

_DIST = Path(settings.frontend_dist).resolve()

if (_DIST / "index.html").is_file():
    logger.info("Sirviendo el frontend compilado desde %s", _DIST)

    # Los recursos con hash en el nombre se pueden cachear para siempre: si
    # cambian, cambia el nombre.
    if (_DIST / "assets").is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=_DIST / "assets"),
            name="assets",
        )

    @app.get("/{ruta:path}", include_in_schema=False)
    async def servir_frontend(ruta: str) -> FileResponse:
        """Entrega el frontend, y su `index.html` para cualquier ruta interna.

        La aplicación es una SPA: `/admin/partidas/3` no es un archivo, lo
        resuelve el router de React en el navegador. Pero al recargar esa
        dirección el navegador la pide al servidor, así que hay que devolver el
        `index.html` y dejar que React haga el resto.
        """
        # Sin esto, una dirección equivocada de la API devolvería el HTML de la
        # aplicación con un 200, que es de lo más confuso al depurar.
        if ruta.startswith(("api/", "ws/")):
            raise HTTPException(status_code=404, detail=f"No existe /{ruta}.")

        # `..` en la ruta permitiría leer archivos de fuera de la carpeta.
        candidato = (_DIST / ruta).resolve()
        dentro = candidato == _DIST or _DIST in candidato.parents

        if ruta and dentro and candidato.is_file():
            return FileResponse(candidato)

        return FileResponse(_DIST / "index.html")

else:
    logger.info(
        "Sin frontend compilado en %s: en desarrollo lo sirve Vite (npm run dev).",
        _DIST,
    )
