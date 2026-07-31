/**
 * Cliente de la API del catálogo de figuras.
 */

import type { Patron } from '@/lib/bingo'
import { pedir } from '@/lib/http'

const BASE = '/api/figuras'

/**
 * Categoría con la que el administrador clasifica una figura del catálogo.
 *
 * Es puramente organizativa: al configurar una partida, cada una de las tres
 * listas ofrece solo las figuras clasificadas en ella. No cambia cómo se gana
 * (eso lo define el patrón) ni cuánto se paga (el premio se fija por partida y
 * es propio de cada forma).
 */
export type TipoFigura = 'sencillo' | 'figura' | 'pleno'

export const TIPOS_FIGURA: { valor: TipoFigura; etiqueta: string }[] = [
  { valor: 'sencillo', etiqueta: 'Sencillo' },
  { valor: 'figura', etiqueta: 'Figura' },
  { valor: 'pleno', etiqueta: 'Pleno' },
]

export const ETIQUETA_TIPO: Record<TipoFigura, string> = {
  sencillo: 'Sencillo',
  figura: 'Figura',
  pleno: 'Pleno',
}

/** Una figura tal como la devuelve la API. */
export interface Figura {
  id: number
  nombre: string
  patron: Patron
  tipo: TipoFigura
  celdas_marcadas: number
  creado_en: string
  actualizado_en: string
}

export interface DatosFigura {
  nombre: string
  patron: Patron
  tipo: TipoFigura
}

export function listarFiguras(tipo?: TipoFigura): Promise<Figura[]> {
  const consulta = tipo ? `?tipo=${tipo}` : ''
  return pedir<Figura[]>(`${BASE}${consulta}`)
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
