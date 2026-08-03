/**
 * Cuadro de ganadores: quién ganó y quién está a punto de ganar.
 *
 * Llega por el mismo WebSocket de la partida que las balotas, en un evento
 * `ganadores` que trae la **foto completa** (no lo que cambió). El endpoint HTTP
 * devuelve exactamente lo mismo y sirve para la carga inicial.
 *
 * El cálculo es del backend: decidir quién ganó es una decisión con dinero
 * detrás y no puede depender de lo que crea cada navegador. El frontend solo lo
 * muestra.
 */

import { pedir } from '@/lib/http'

export interface CartonGanador {
  carton_id: number
  codigo: string
}

/** Una forma de ganar completada. */
export interface Bingo {
  partida_figura_id: number
  figura_id: number
  figura: string
  valor_premio: number
  /** Balota con la que se completó: su posición en el sorteo y su número. */
  orden_balota: number
  numero_balota: number
  /**
   * Se completó con la balota que se acaba de cantar. Es lo que permite avisar
   * una sola vez en lugar de repetir el aviso en cada balota posterior.
   */
  nuevo: boolean
  /** Todos los cartones que la ganaron. Si son varios, comparten el premio. */
  cartones: CartonGanador[]
}

/** Un cartón a una o dos balotas de completar una forma. */
export interface CartonCerca {
  carton_id: number
  codigo: string
  partida_figura_id: number
  figura: string
  faltan: number
  /** Los números que todavía le faltan. */
  numeros: number[]
}

export interface CuadroGanadores {
  tipo: 'ganadores'
  partida_id: number
  orden_balota: number
  bingos: Bingo[]
  total_cartones_ganadores: number
  /**
   * Totales reales de cartones a una y a dos balotas. `cerca` viene recortada
   * para no mandar miles de filas, así que para contar hay que usar estos, no
   * el largo de la lista.
   */
  a_una: number
  a_dos: number
  cerca: CartonCerca[]
}

export const CUADRO_VACIO: CuadroGanadores = {
  tipo: 'ganadores',
  partida_id: 0,
  orden_balota: 0,
  bingos: [],
  total_cartones_ganadores: 0,
  a_una: 0,
  a_dos: 0,
  cerca: [],
}

export function obtenerGanadores(partidaId: number): Promise<CuadroGanadores> {
  return pedir<CuadroGanadores>(`/api/partidas/${partidaId}/ganadores`)
}

/** «3 cartones» / «1 cartón», para el encabezado del aviso. */
export function textoCartones(cuantos: number): string {
  return cuantos === 1 ? '1 cartón' : `${cuantos} cartones`
}
