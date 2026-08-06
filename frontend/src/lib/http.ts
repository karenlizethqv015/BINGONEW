/**
 * Acceso HTTP al backend, compartido por todos los módulos de la API.
 *
 * Rutas relativas siempre (`/api/...`): en desarrollo las resuelve el proxy de
 * Vite y en la instalación en LAN comparten origen con el backend. No debe
 * aparecer ningún host ni puerto escrito a mano.
 */

import { CABECERA_ADMIN, FaltaClaveAdmin, claveAdmin } from '@/lib/admin'

/**
 * Se emite cuando el backend rechaza una acción por falta de clave.
 *
 * Es un evento y no una llamada directa porque `pedir` es una función suelta,
 * sin acceso a los componentes: quien quiera reaccionar se suscribe. Lo hace
 * `PedirClaveAdmin`, una sola vez, colgado del `Layout`.
 */
const EVENTO_FALTA_CLAVE = 'bingo:falta-clave-admin'

/** Avisa cuando una petición se rechazó por falta de clave. */
export function alFaltarClaveAdmin(escuchar: () => void): () => void {
  window.addEventListener(EVENTO_FALTA_CLAVE, escuchar)
  return () => window.removeEventListener(EVENTO_FALTA_CLAVE, escuchar)
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
  // La clave de administración viaja en todas las peticiones si está guardada.
  // El backend solo la exige en las que modifican, así que las pantallas del
  // público (transmisión y jugador) funcionan igual sin ella.
  const clave = claveAdmin()

  let respuesta: Response
  try {
    respuesta = await fetch(url, {
      ...opciones,
      headers: {
        'Content-Type': 'application/json',
        ...(clave ? { [CABECERA_ADMIN]: clave } : {}),
        ...opciones?.headers,
      },
    })
  } catch {
    throw new Error('No se pudo contactar el backend. ¿Está corriendo uvicorn?')
  }

  // 401 se distingue del resto para que la pantalla pueda pedir la clave en vez
  // de enseñar un error que el usuario no sabe cómo resolver.
  if (respuesta.status === 401) {
    window.dispatchEvent(new Event(EVENTO_FALTA_CLAVE))
    throw new FaltaClaveAdmin()
  }

  if (!respuesta.ok) {
    throw new Error(await mensajeDeError(respuesta))
  }

  // 204 No Content (los borrados) no trae cuerpo que parsear.
  if (respuesta.status === 204) return undefined as T

  return respuesta.json()
}
