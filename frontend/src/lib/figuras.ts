/**
 * Cliente de la API del catálogo de figuras.
 *
 * Rutas relativas siempre: en desarrollo las resuelve el proxy de Vite y en la
 * instalación en LAN comparten origen con el backend.
 */

import type { Patron } from '@/lib/bingo'

const BASE = '/api/figuras'

/** Una figura tal como la devuelve la API. */
export interface Figura {
  id: number
  nombre: string
  patron: Patron
  celdas_marcadas: number
  creado_en: string
  actualizado_en: string
}

export interface DatosFigura {
  nombre: string
  patron: Patron
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

async function pedir<T>(url: string, opciones?: RequestInit): Promise<T> {
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

  // 204 No Content (el borrado) no trae cuerpo que parsear.
  if (respuesta.status === 204) return undefined as T

  return respuesta.json()
}

export function listarFiguras(): Promise<Figura[]> {
  return pedir<Figura[]>(BASE)
}

export function crearFigura(datos: DatosFigura): Promise<Figura> {
  return pedir<Figura>(BASE, { method: 'POST', body: JSON.stringify(datos) })
}

export function actualizarFigura(
  id: number,
  datos: DatosFigura,
): Promise<Figura> {
  return pedir<Figura>(`${BASE}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(datos),
  })
}

export function eliminarFigura(id: number): Promise<void> {
  return pedir<void>(`${BASE}/${id}`, { method: 'DELETE' })
}
