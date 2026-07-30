/**
 * Acceso al backend.
 *
 * Todas las URLs son relativas (`/api/...`, `/ws/...`) a propósito:
 *  - en desarrollo, el proxy de Vite las reenvía a uvicorn (ver vite.config.ts);
 *  - en la instalación final en LAN, frontend y backend se sirven desde el mismo
 *    origen, así que funcionan sin cambiar nada.
 * Por eso no debe aparecer ningún host ni puerto escrito a mano en el código.
 */

/** Respuesta del endpoint GET /api/health. */
export interface EstadoSalud {
  estado: string
  servicio: string
  version: string
  base_datos: boolean
  motor_bd: string
}

export async function obtenerSalud(): Promise<EstadoSalud> {
  const respuesta = await fetch('/api/health')

  if (!respuesta.ok) {
    throw new Error(`El backend respondió ${respuesta.status}`)
  }

  return respuesta.json()
}

/** Construye la URL absoluta de un WebSocket a partir de una ruta relativa. */
export function urlWebSocket(ruta: string): string {
  const protocolo = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocolo}//${window.location.host}${ruta}`
}
