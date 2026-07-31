"""Mensajes que viajan por el WebSocket de una partida.

Este módulo es el **único** que construye los eventos. Es deliberado: cuando se
integre la balotera física, debe emitir exactamente lo mismo que la virtual, de
modo que el tablero de transmisión, el cartón del jugador y el panel del
administrador no se enteren de cuál es la fuente. Si los eventos se armaran a
mano en cada endpoint, esa promesa se rompería sin que nadie lo note.

Todas las vistas en tiempo real se conectan al mismo canal por partida y
reaccionan a estos tres tipos.
"""

from typing import Any

from app.dominio.bingo import TOTAL_BALOTAS, letra_de_numero
from app.models.balota_cantada import BalotaCantada
from app.models.partida import Partida


def canal_de_partida(partida_id: int) -> str:
    """Nombre del canal de una partida dentro del gestor de conexiones."""
    return f"partida:{partida_id}"


def _balota_a_dict(balota: BalotaCantada) -> dict[str, Any]:
    """Forma de una balota dentro de cualquier evento."""
    return {
        "numero": balota.numero,
        # La letra se calcula aquí y viaja ya resuelta: así ninguna de las tres
        # vistas tiene que reimplementar los rangos B-I-N-G-O por su cuenta.
        "letra": letra_de_numero(balota.numero),
        "orden": balota.orden,
        "cantada_en": balota.cantada_en.isoformat() if balota.cantada_en else None,
    }


def evento_balota(
    partida: Partida, balota: BalotaCantada, total_cantadas: int
) -> dict[str, Any]:
    """Se acaba de cantar una balota.

    Es el evento central del sistema. Debe ser idéntico venga de donde venga la
    balota.
    """
    return {
        "tipo": "balota",
        "partida_id": partida.id,
        "estado": partida.estado.value,
        "balota": _balota_a_dict(balota),
        "total_cantadas": total_cantadas,
        "restantes": TOTAL_BALOTAS - total_cantadas,
    }


def evento_estado(partida: Partida, total_cantadas: int) -> dict[str, Any]:
    """La partida cambió de estado (se inició, se pausó, se reanudó, terminó)."""
    return {
        "tipo": "estado",
        "partida_id": partida.id,
        "estado": partida.estado.value,
        "total_cantadas": total_cantadas,
        "restantes": TOTAL_BALOTAS - total_cantadas,
    }


def evento_sincronizacion(
    partida: Partida, balotas: list[BalotaCantada]
) -> dict[str, Any]:
    """Estado completo de la partida, para quien acaba de conectarse.

    Lleva **todas** las balotas ya cantadas a propósito: una pantalla que se
    abre a mitad de partida, o que se reconecta tras una caída de red, tiene que
    poder reconstruir el tablero entero sin pedir nada más. Sin esto, el tablero
    de la sala arrancaría vacío y solo se iría llenando con las siguientes.
    """
    return {
        "tipo": "sincronizacion",
        "partida_id": partida.id,
        "numero_consecutivo": partida.numero_consecutivo,
        "estado": partida.estado.value,
        "duracion_segundos_entre_balota": partida.duracion_segundos_entre_balota,
        "balotas": [_balota_a_dict(balota) for balota in balotas],
        "total_cantadas": len(balotas),
        "restantes": TOTAL_BALOTAS - len(balotas),
    }
