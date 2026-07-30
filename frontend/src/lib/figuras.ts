/**
 * Cliente de la API del catálogo de figuras.
 */

import type { Patron } from '@/lib/bingo'
import { pedir } from '@/lib/http'

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
