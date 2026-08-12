/**
 * Cliente de la API de partidas y de su selección de formas de ganar.
 */

import type { Patron } from '@/lib/bingo'
import type { TipoFigura } from '@/lib/figuras'
import { pedir } from '@/lib/http'

const BASE = '/api/partidas'

export type EstadoPartida = 'pendiente' | 'en_curso' | 'pausada' | 'finalizada'

// La categoría (sencillo/figura/pleno) es una propiedad de la figura en el
// catálogo, no de la selección: ver `TipoFigura` en `@/lib/figuras`.

export const ETIQUETA_ESTADO: Record<EstadoPartida, string> = {
  pendiente: 'Pendiente',
  en_curso: 'En curso',
  pausada: 'Pausada',
  finalizada: 'Finalizada',
}

/** Una forma de ganar ya seleccionada en una partida. */
export interface FormaSeleccionada {
  id: number
  figura: { id: number; nombre: string; patron: Patron; tipo: TipoFigura }
  /** Premio de esta forma. Cada una tiene el suyo, independiente del resto. */
  valor_premio: number
  orden: number
}

export interface Partida {
  id: number
  numero_consecutivo: number
  estado: EstadoPartida
  precio_carton: number
  duracion_segundos_entre_balota: number
  /** El «bombillo»: si todavía se están vendiendo cartones. Independiente del sorteo. */
  venta_abierta: boolean
  creado_en: string
  iniciada_en: string | null
  finalizada_en: string | null
  figuras: FormaSeleccionada[]
  total_formas: number
  premio_total: number
}

/**
 * Una forma de ganar que se quiere incluir. No lleva categoría: esa es una
 * propiedad de la figura en el catálogo.
 */
export interface FormaAElegir {
  figura_id: number
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

/** Abre o cierra el «bombillo» de venta de cartones. */
export function cambiarVenta(id: number, ventaAbierta: boolean): Promise<Partida> {
  return pedir<Partida>(`${BASE}/${id}/venta`, {
    method: 'PUT',
    body: JSON.stringify({ venta_abierta: ventaAbierta }),
  })
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
