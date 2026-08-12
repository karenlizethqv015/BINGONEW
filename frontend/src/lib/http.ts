/**
 * Acceso HTTP al backend, compartido por todos los módulos de la API.
 *
 * Rutas relativas siempre (`/api/...`): en desarrollo las resuelve el proxy de
 * Vite y en la instalación en LAN comparten origen con el backend. No debe
 * aparecer ningún host ni puerto escrito a mano.
 */

import { CABECERA_ADMIN, FaltaClaveAdmin, claveAdmin } from '@/lib/admin'
import { CABECERA_OPERADOR, FaltaClaveOperador, claveOperador } from '@/lib/operador'

/**
 * Se emiten cuando el backend rechaza una acción por falta de clave.
 *
 * Son eventos y no una llamada directa porque `pedir` es una función suelta,
 * sin acceso a los componentes: quien quiera reaccionar se suscribe. Lo hacen
 * `PedirClaveAdmin` y `PedirClaveOperador`, colgados del `Layout`.
 *
 * `pedir` manda las dos claves guardadas en cada petición (cada tranca del
 * backend solo mira la suya), y el backend responde cuál hacía falta en la
 * cabecera `X-Clave-Requerida` — así se sabe cuál de los dos diálogos abrir
 * sin tener que adivinarlo del texto del mensaje.
 */
const EVENTO_FALTA_CLAVE_ADMIN = 'bingo:falta-clave-admin'
const EVENTO_FALTA_CLAVE_OPERADOR = 'bingo:falta-clave-operador'
const CABECERA_ROL_REQUERIDO = 'X-Clave-Requerida'

/** Avisa cuando una petición se rechazó por falta de la clave de administración. */
export function alFaltarClaveAdmin(escuchar: () => void): () => void {
  window.addEventListener(EVENTO_FALTA_CLAVE_ADMIN, escuchar)
  return () => window.removeEventListener(EVENTO_FALTA_CLAVE_ADMIN, escuchar)
}

/** Avisa cuando una petición se rechazó por falta de la clave de operador. */
export function alFaltarClaveOperador(escuchar: () => void): () => void {
  window.addEventListener(EVENTO_FALTA_CLAVE_OPERADOR, escuchar)
  return () => window.removeEventListener(EVENTO_FALTA_CLAVE_OPERADOR, escuchar)
}

/**
 * Convierte una respuesta de error en un mensaje legible.
 *
 * FastAPI devuelve `detail` como texto en los errores propios (404, 409) pero
 * como lista de objetos en los de validación (422); hay que tratar los dos.
 */
async function mensajeDeError(respuesta: Response): Promise<string> {
  try {
    const cuerpo = await respuesta.json()
    const detalle = cuerpo?.detail

    if (typeof detalle === 'string') return detalle

    if (Array.isArray(detalle)) {
      const mensajes = detalle
        .map((e: { msg?: string }) => e.msg)
        .filter(Boolean)
        .join('. ')
      if (mensajes) return mensajes.replace(/^Value error, /, '')
    }
  } catch {
    // El cuerpo no era JSON: se cae al mensaje genérico de abajo.
  }

  return `El servidor respondió ${respuesta.status}.`
}

export async function pedir<T>(
  url: string,
  opciones?: RequestInit,
): Promise<T> {
  // Las dos claves viajan en todas las peticiones si están guardadas. Cada
  // tranca del backend solo mira la suya, así que mandar la que no aplica no
  // hace nada; y las pantallas del público (transmisión y jugador) funcionan
  // igual sin ninguna, porque el backend solo las exige en lo que modifica.
  const admin = claveAdmin()
  const operador = claveOperador()

  let respuesta: Response
  try {
    respuesta = await fetch(url, {
      ...opciones,
      headers: {
        'Content-Type': 'application/json',
        ...(admin ? { [CABECERA_ADMIN]: admin } : {}),
        ...(operador ? { [CABECERA_OPERADOR]: operador } : {}),
        ...opciones?.headers,
      },
    })
  } catch {
    throw new Error('No se pudo contactar el backend. ¿Está corriendo uvicorn?')
  }

  // 401 se distingue del resto para que la pantalla pueda pedir la clave en vez
  // de enseñar un error que el usuario no sabe cómo resolver.
  if (respuesta.status === 401) {
    if (respuesta.headers.get(CABECERA_ROL_REQUERIDO) === 'operador') {
      window.dispatchEvent(new Event(EVENTO_FALTA_CLAVE_OPERADOR))
      throw new FaltaClaveOperador()
    }
    window.dispatchEvent(new Event(EVENTO_FALTA_CLAVE_ADMIN))
    throw new FaltaClaveAdmin()
  }

  if (!respuesta.ok) {
    throw new Error(await mensajeDeError(respuesta))
  }

  // 204 No Content (los borrados) no trae cuerpo que parsear.
  if (respuesta.status === 204) return undefined as T

  return respuesta.json()
}
