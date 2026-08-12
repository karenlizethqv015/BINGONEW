"""Trancas de administración y operación para la demo desplegada en internet.

**Esto no es el login de la Fase 2.** No hay usuarios, ni contraseñas por
persona, ni sesiones, ni permisos: son dos claves compartidas que se escriben
una vez en el navegador, una por rol. Existen porque la demo vive en una URL
pública y cualquiera que tenga el enlace podría, si no, reiniciar el sorteo en
mitad de la jugada o borrar el catálogo de figuras. El login real (admin y
vendedor por usuario y contraseña, jugador por cédula) sigue siendo trabajo de
la Fase 2.

Dos claves, dos alcances:

- `ADMIN_CLAVE` protege el catálogo de figuras (lo que rara vez cambia durante
  una jornada).
- `OPERADOR_CLAVE` protege partidas, balotera y cartones (lo que se toca
  constantemente mientras la sala está jugando).

Cada una protege solo lo que **modifica**. Se quedan abiertos a propósito:

- las consultas (`GET`), y
- el WebSocket de la partida,

porque el tablero de transmisión y el cartón del jugador tienen que poder
entrar sin escribir nada: son pantallas de la sala y del público.

Los 401 llevan la cabecera `X-Clave-Requerida` con cuál de las dos hizo falta
(`admin` u `operador`). El frontend manda las dos claves guardadas en cada
petición (`app/lib/http.ts`) porque cada tranca solo mira la suya y no le
importa la otra; con esta cabecera sabe cuál de los dos diálogos abrir sin
tener que adivinarlo a partir del texto del mensaje.
"""

import secrets

from fastapi import Depends, Header, HTTPException, Request, status

from app.config import settings

#: Cabeceras por las que viaja cada clave.
CABECERA_ADMIN = "X-Admin-Clave"
CABECERA_OPERADOR = "X-Operador-Clave"

#: Métodos que solo leen. Se dejan pasar siempre, en las dos trancas.
METODOS_DE_LECTURA = frozenset({"GET", "HEAD", "OPTIONS"})

#: Cabecera de respuesta que dice cuál clave hacía falta, para que el
#: frontend sepa qué diálogo abrir sin adivinarlo del texto del mensaje.
CABECERA_ROL_REQUERIDO = "X-Clave-Requerida"


async def exigir_admin(
    request: Request,
    x_admin_clave: str | None = Header(default=None, alias=CABECERA_ADMIN),
) -> None:
    """Deja pasar las consultas, y exige la clave de administración a lo que
    modifica el catálogo de figuras.

    Mira el método en vez de colgarse de cada ruta a mano. Es a propósito: una
    tranca que hay que acordarse de repetir en cada endpoint nuevo es una
    tranca que tarde o temprano se olvida en uno. Así, un endpoint que se
    añada mañana queda protegido por el mero hecho de no ser una consulta.

    Con `ADMIN_CLAVE` sin definir no exige nada: es el caso de desarrollo y el
    de la instalación en la LAN de la sala, donde el servidor no está
    expuesto.
    """
    if request.method in METODOS_DE_LECTURA:
        return

    esperada = settings.admin_clave
    if not esperada:
        return

    if x_admin_clave is None or not secrets.compare_digest(x_admin_clave, esperada):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hace falta la clave de administración para esta acción.",
            headers={CABECERA_ROL_REQUERIDO: "admin"},
        )


async def exigir_operador(
    request: Request,
    x_operador_clave: str | None = Header(default=None, alias=CABECERA_OPERADOR),
) -> None:
    """Igual que `exigir_admin`, pero para lo que administra el operador de
    sala: partidas, balotera y cartones.
    """
    if request.method in METODOS_DE_LECTURA:
        return

    esperada = settings.operador_clave
    if not esperada:
        return

    if x_operador_clave is None or not secrets.compare_digest(
        x_operador_clave, esperada
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hace falta la clave de operador para esta acción.",
            headers={CABECERA_ROL_REQUERIDO: "operador"},
        )


#: Lo que se le cuelga a los routers que administra el rol administrador
#: (hoy, el catálogo de figuras).
SOLO_ADMIN = [Depends(exigir_admin)]

#: Lo que se le cuelga a los routers que administra el rol operador (partidas,
#: balotera y cartones).
SOLO_OPERADOR = [Depends(exigir_operador)]
