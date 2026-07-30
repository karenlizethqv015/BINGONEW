/**
 * Acceso HTTP al backend, compartido por todos los módulos de la API.
 *
 * Rutas relativas siempre (`/api/...`): en desarrollo las resuelve el proxy de
 * Vite y en la instalación en LAN comparten origen con el backend. No debe
 * aparecer ningún host ni puerto escrito a mano.
 */

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
  let respuesta: Response
  try {
    respuesta = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...opciones,
    })
  } catch {
    throw new Error('No se pudo contactar el backend. ¿Está corriendo uvicorn?')
  }

  if (!respuesta.ok) {
    throw new Error(await mensajeDeError(respuesta))
  }

  // 204 No Content (los borrados) no trae cuerpo que parsear.
  if (respuesta.status === 204) return undefined as T

  return respuesta.json()
}
