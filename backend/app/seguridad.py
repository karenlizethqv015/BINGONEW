"""Tranca de administración para la demo desplegada en internet.

**Esto no es el login de la Fase 2.** No hay usuarios, ni contraseñas por
persona, ni sesiones, ni permisos: es una sola clave compartida que se escribe
una vez en el navegador. Existe porque la demo vive en una URL pública y
cualquiera que tenga el enlace podría, si no, reiniciar el sorteo en mitad de la
jugada. El login real (admin y vendedor por usuario y contraseña, jugador por
cédula) sigue siendo trabajo de la Fase 2.

Protege solo lo que **modifica**. Se quedan abiertos a propósito:

- las consultas (`GET`), y
- el WebSocket de la partida,

porque el tablero de transmisión y el cartón del jugador tienen que poder
entrar sin escribir nada: son pantallas de la sala y del público.
"""

import secrets

from fastapi import Depends, Header, HTTPException, Request, status

from app.config import settings

#: Cabecera por la que viaja la clave.
CABECERA = "X-Admin-Clave"

#: Métodos que solo leen. Se dejan pasar siempre.
METODOS_DE_LECTURA = frozenset({"GET", "HEAD", "OPTIONS"})


async def exigir_admin(
    request: Request,
    x_admin_clave: str | None = Header(default=None, alias=CABECERA),
) -> None:
    """Deja pasar las consultas, y exige la clave a todo lo que modifica.

    Mira el método en vez de colgarse de cada ruta a mano. Es a propósito: una
    tranca que hay que acordarse de repetir en cada endpoint nuevo es una tranca
    que tarde o temprano se olvida en uno. Así, un endpoint que se añada mañana
    queda protegido por el mero hecho de no ser una consulta.

    Con `ADMIN_CLAVE` sin definir no exige nada: es el caso de desarrollo y el
    de la instalación en la LAN de la sala, donde el servidor no está expuesto.
    """
    if request.method in METODOS_DE_LECTURA:
        return

    esperada = settings.admin_clave
    if not esperada:
        return

    # `compare_digest` y no `==`: comparar cadenas con `==` termina en cuanto
    # encuentra el primer carácter distinto, y ese tiempo de más filtra
    # información sobre la clave. Aquí el riesgo es remoto, pero comparar bien
    # no cuesta nada.
    if x_admin_clave is None or not secrets.compare_digest(x_admin_clave, esperada):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hace falta la clave de administración para esta acción.",
        )


#: Lo que se le cuelga a cada router que toca datos de la partida.
SOLO_ADMIN = [Depends(exigir_admin)]
