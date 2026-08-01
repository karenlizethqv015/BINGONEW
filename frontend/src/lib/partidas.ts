/**
 * Cliente de la API de partidas y de su selección de formas de ganar.
 */

import type { Patron } from '@/lib/bingo'
import { pedir } from '@/lib/http'

const BASE = '/api/partidas'

export type EstadoPartida = 'pendiente' | 'en_curso' | 'pausada' | 'finalizada'

/**
 * Categoría con la que se agrupa una forma dentro de la partida.
 *
 * Es puramente organizativa: ayuda al administrador a encontrar las formas al
 * armar la partida. No cambia cómo se gana (eso lo define el patrón de la
 * figura) ni cuánto se paga (eso lo define el premio propio de cada forma).
 *
 * Tampoco son etapas: todas las formas de la partida juegan a la vez.
 */
export type TipoPremio = 'sencillo' | 'figura' | 'pleno'

export const TIPOS_PREMIO: { valor: TipoPremio; etiqueta: string }[] = [
  { valor: 'sencillo', etiqueta: 'Sencillo' },
  { valor: 'figura', etiqueta: 'Figura' },
  { valor: 'pleno', etiqueta: 'Pleno' },
]

export const ETIQUETA_ESTADO: Record<EstadoPartida, string> = {
  pendiente: 'Pendiente',
  en_curso: 'En curso',
  pausada: 'Pausada',
  finalizada: 'Finalizada',
}

/** Una forma de ganar ya seleccionada en una partida. */
export interface FormaSeleccionada {
  id: number
  figura: { id: number; nombre: string; patron: Patron }
  tipo_premio: TipoPremio
  valor_premio: number
  orden: number
}

export interface Partida {
  id: number
  numero_consecutivo: number
  estado: EstadoPartida
  precio_carton: number
  duracion_segundos_entre_balota: number
  creado_en: string
  iniciada_en: string | null
  finalizada_en: string | null
  figuras: FormaSeleccionada[]
  total_formas: number
  premio_total: number
}

/** Una forma de ganar que se quiere incluir. El orden sale de la posición. */
export interface FormaAElegir {
  figura_id: number
  tipo_premio: TipoPremio
  valor_premio: number
}

export function listarPartidas(): Promise<Partida[]> {
  return pedir<Partida[]>(BASE)
}

export function obtenerPartida(id: number): Promise<Partida> {
  return pedir<Partida>(`${BASE}/${id}`)
}

export function crearPartida(datos: {
  precio_carton: number
  duracion_segundos_entre_balota: number
}): Promise<Partida> {
  return pedir<Partida>(BASE, { method: 'POST', body: JSON.stringify(datos) })
}

export function actualizarPartida(
  id: number,
  datos: { precio_carton?: number; duracion_segundos_entre_balota?: number },
): Promise<Partida> {
  return pedir<Partida>(`${BASE}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(datos),
  })
}

export function eliminarPartida(id: number): Promise<void> {
  return pedir<void>(`${BASE}/${id}`, { method: 'DELETE' })
}

/** Reemplaza por completo las formas de ganar de una partida. */
export function definirFormas(
  id: number,
  formas: FormaAElegir[],
): Promise<Partida> {
  return pedir<Partida>(`${BASE}/${id}/formas`, {
    method: 'PUT',
    body: JSON.stringify({ formas }),
  })
}

/** Formatea un valor en pesos colombianos, sin centavos. */
export function formatearPesos(valor: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(valor)
}
