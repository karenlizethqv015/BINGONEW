"""Mensajes que viajan por el WebSocket de una partida.

Este módulo es el **único** que construye los eventos. Es deliberado: cuando se
integre la balotera física, debe emitir exactamente lo mismo que la virtual, de
modo que el tablero de transmisión, el cartón del jugador y el panel del
administrador no se enteren de cuál es la fuente. Si los eventos se armaran a
mano en cada endpoint, esa promesa se rompería sin que nadie lo note.

Todas las vistas en tiempo real se conectan al mismo canal por partida y
reaccionan a estos cuatro tipos.
"""

from typing import Any

from app.dominio.bingo import TOTAL_BALOTAS, letra_de_numero
from app.dominio.ganadores import CuadroDeGanadores
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
        "venta_abierta": partida.venta_abierta,
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
        "venta_abierta": partida.venta_abierta,
        "duracion_segundos_entre_balota": partida.duracion_segundos_entre_balota,
        # Para el reloj de la jugada del panel de administración. Va aquí y no
        # en una petición aparte porque este evento es la foto completa de la
        # partida, y porque el panel debe poder ponerlo en hora al reconectarse.
        "iniciada_en": partida.iniciada_en.isoformat() if partida.iniciada_en else None,
        "balotas": [_balota_a_dict(balota) for balota in balotas],
        "total_cantadas": len(balotas),
        "restantes": TOTAL_BALOTAS - len(balotas),
    }


def evento_ganadores(
    partida: Partida, cuadro: CuadroDeGanadores, orden_balota: int
) -> dict[str, Any]:
    """Quién ha ganado y quién está a una o a dos balotas de ganar.

    Lleva la **foto completa**, no lo que cambió: igual que `sincronizacion`, una
    pantalla que se abre o se reconecta a mitad de partida tiene que poder
    reconstruir el cuadro entero sin pedir nada más. Se emite después de cada
    balota y al conectarse un cliente.

    `a_una` y `a_dos` son los totales **reales**, aunque la lista `cerca` venga
    recortada: el recorte existe para que la pantalla no reciba miles de filas
    ilegibles, pero no debe mentir en el número.
    """
    return {
        "tipo": "ganadores",
        "partida_id": partida.id,
        "orden_balota": orden_balota,
        "bingos": [
            {
                "partida_figura_id": ganada.forma.partida_figura_id,
                "figura_id": ganada.forma.figura_id,
                "figura": ganada.forma.nombre,
                "valor_premio": ganada.forma.valor_premio,
                "orden_balota": ganada.orden_balota,
                "numero_balota": ganada.numero_balota,
                "nuevo": ganada.nuevo,
                "cartones": [
                    {"carton_id": carton.carton_id, "codigo": carton.codigo}
                    for carton in ganada.cartones
                ],
            }
            for ganada in cuadro.ganadas
        ],
        "total_cartones_ganadores": cuadro.total_cartones_ganadores,
        "a_una": cuadro.a_una,
        "a_dos": cuadro.a_dos,
        "cerca": [
            {
                "carton_id": item.carton_id,
                "codigo": item.codigo,
                "partida_figura_id": item.partida_figura_id,
                "figura": item.figura,
                "faltan": item.faltan,
                "numeros": item.numeros,
            }
            for item in cuadro.cerca
        ],
        "por_forma": [
            {
                "partida_figura_id": item.partida_figura_id,
                "figura": item.figura,
                "a_una": item.a_una,
                "a_dos": item.a_dos,
            }
            for item in cuadro.por_forma
        ],
    }
