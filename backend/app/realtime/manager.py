"""Gestor de conexiones WebSocket en memoria.

Agrupa las conexiones por *canal* (una cadena libre). En la Fase 1 el canal será
el identificador de la partida, de modo que al cantar una balota se emita solo a
los clientes conectados a esa partida.

Se mantiene en memoria del propio proceso FastAPI a propósito: cada sala corre
una sola instancia del backend en su LAN, así que no hace falta Redis para el
pub/sub. Queda anotado como mejora futura si alguna sala llegara a necesitar más
de un servidor (ver docs/06-arquitectura.md).
"""

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class GestorConexiones:
    """Mantiene las conexiones WebSocket activas agrupadas por canal."""

    def __init__(self) -> None:
        self._canales: dict[str, set[WebSocket]] = {}
        # Protege el diccionario: varias corrutinas pueden conectar y
        # desconectar al mismo tiempo.
        self._lock = asyncio.Lock()

    async def conectar(self, canal: str, websocket: WebSocket) -> None:
        """Acepta la conexión y la registra en el canal indicado."""
        await websocket.accept()
        async with self._lock:
            self._canales.setdefault(canal, set()).add(websocket)
        logger.info("WebSocket conectado al canal %s", canal)

    async def desconectar(self, canal: str, websocket: WebSocket) -> None:
        """Quita la conexión del canal y limpia el canal si queda vacío."""
        async with self._lock:
            conexiones = self._canales.get(canal)
            if not conexiones:
                return
            conexiones.discard(websocket)
            if not conexiones:
                del self._canales[canal]
        logger.info("WebSocket desconectado del canal %s", canal)

    async def emitir(self, canal: str, mensaje: dict[str, Any]) -> None:
        """Envía un mensaje JSON a todos los clientes de un canal.

        Las conexiones que fallen al enviar (cliente cerrado de golpe, red caída)
        se descartan en silencio: no deben impedir que el resto de la sala reciba
        la balota.
        """
        async with self._lock:
            destinatarios = list(self._canales.get(canal, ()))

        caidas: list[WebSocket] = []
        for websocket in destinatarios:
            try:
                await websocket.send_json(mensaje)
            except Exception:
                caidas.append(websocket)

        for websocket in caidas:
            await self.desconectar(canal, websocket)

    def total_conexiones(self, canal: str) -> int:
        """Cantidad de clientes conectados a un canal."""
        return len(self._canales.get(canal, ()))


# Instancia única compartida por toda la aplicación.
gestor = GestorConexiones()
