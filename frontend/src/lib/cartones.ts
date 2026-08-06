/**
 * Cliente de la API de cartones virtuales.
 */

import type { MatrizCarton } from '@/lib/bingo'
import { pedir } from '@/lib/http'

/** Tope por petición que acepta el backend. */
export const MAXIMO_POR_PETICION = 5000

export interface Carton {
  id: number
  partida_id: number
  serie: string
  numero_carton: number
  /** Matriz 5x5; `null` en el centro, que es la casilla libre. */
  numeros: MatrizCarton
  creado_en: string
}

export interface ResumenCartones {
  total: number
  por_serie: Record<string, number>
}

function base(partidaId: number): string {
  return `/api/partidas/${partidaId}/cartones`
}

export function listarCartones(
  partidaId: number,
  opciones: { serie?: string; limite?: number; desplazamiento?: number } = {},
): Promise<Carton[]> {
  const parametros = new URLSearchParams()
  if (opciones.serie) parametros.set('serie', opciones.serie)
  if (opciones.limite != null) parametros.set('limite', String(opciones.limite))
  if (opciones.desplazamiento != null) {
    parametros.set('desplazamiento', String(opciones.desplazamiento))
  }

  const consulta = parametros.toString()
  return pedir<Carton[]>(`${base(partidaId)}${consulta ? `?${consulta}` : ''}`)
}

/** Código visible de un cartón dentro de su partida, ej. "A-7". */
export function codigoDeCarton(carton: Pick<Carton, 'serie' | 'numero_carton'>) {
  return `${carton.serie}-${carton.numero_carton}`
}

/**
 * Separa un código escrito a mano en serie y número.
 *
 * Se parte por el ÚLTIMO guion, no por el primero: una serie podría contener
 * guiones y el número nunca los tiene. Devuelve null si el código no tiene
 * forma de código.
 */
export function partirCodigo(
  codigo: string,
): { serie: string; numero: number } | null {
  const limpio = codigo.trim().toUpperCase()
  const corte = limpio.lastIndexOf('-')
  if (corte <= 0) return null

  const numero = Number(limpio.slice(corte + 1))
  if (!Number.isInteger(numero) || numero <= 0) return null

  return { serie: limpio.slice(0, corte), numero }
}

/** Busca un cartón por su código visible. Es como el jugador llega al suyo. */
export function obtenerCartonPorCodigo(
  partidaId: number,
  serie: string,
  numero: number,
): Promise<Carton> {
  return pedir<Carton>(
    `${base(partidaId)}/${encodeURIComponent(serie)}/${numero}`,
  )
}

export function resumenCartones(partidaId: number): Promise<ResumenCartones> {
  return pedir<ResumenCartones>(`${base(partidaId)}/resumen`)
}

export interface CartonesGenerados {
  cantidad: number
  serie: string
  desde: number
  hasta: number
  total_en_partida: number
}

/**
 * Genera una tanda de cartones.
 *
 * Devuelve el resumen de lo creado, no los cartones: con 5000 serían varios
 * megabytes de JSON. Para verlos se pide la primera página con `listarCartones`.
 */
export function generarCartones(
  partidaId: number,
  datos: { cantidad: number; serie?: string },
): Promise<CartonesGenerados> {
  return pedir<CartonesGenerados>(base(partidaId), {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

export function eliminarCartones(
  partidaId: number,
  serie?: string,
): Promise<void> {
  const consulta = serie ? `?serie=${encodeURIComponent(serie)}` : ''
  return pedir<void>(`${base(partidaId)}${consulta}`, { method: 'DELETE' })
}
