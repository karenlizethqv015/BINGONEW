/**
 * Cliente de la balotera y tipos de los eventos en tiempo real.
 */

import type { CuadroGanadores } from '@/lib/ganadores'
import { pedir } from '@/lib/http'
import type { EstadoPartida } from '@/lib/partidas'

/** Una balota ya cantada. La letra viene resuelta desde el backend. */
export interface Balota {
  numero: number
  letra: string
  orden: number
  cantada_en: string
}

export interface EstadoSorteo {
  partida_id: number
  estado: EstadoPartida
  total_cantadas: number
  restantes: number
  ultima: Balota | null
}

/**
 * Eventos que emite el WebSocket de una partida.
 *
 * Son los mismos que emitirá una balotera física el día que se integre: por eso
 * ninguna vista debe suponer de dónde vino la balota.
 */
export interface EventoBalota {
  tipo: 'balota'
  partida_id: number
  estado: EstadoPartida
  balota: Balota
  total_cantadas: number
  restantes: number
}

export interface EventoEstado {
  tipo: 'estado'
  partida_id: number
  estado: EstadoPartida
  total_cantadas: number
  restantes: number
}

export interface EventoSincronizacion {
  tipo: 'sincronizacion'
  partida_id: number
  numero_consecutivo: number
  estado: EstadoPartida
  duracion_segundos_entre_balota: number
  balotas: Balota[]
  total_cantadas: number
  restantes: number
}

export type EventoPartida =
  | EventoBalota
  | EventoEstado
  | EventoSincronizacion
  | CuadroGanadores

function base(partidaId: number): string {
  return `/api/partidas/${partidaId}`
}

export function estadoDelSorteo(partidaId: number): Promise<EstadoSorteo> {
  return pedir<EstadoSorteo>(`${base(partidaId)}/sorteo`)
}

export function listarBalotas(partidaId: number): Promise<Balota[]> {
  return pedir<Balota[]>(`${base(partidaId)}/balotas`)
}

/** Saca la siguiente balota. El backend decide cuál. */
export function cantarBalota(partidaId: number): Promise<Balota> {
  return pedir<Balota>(`${base(partidaId)}/balotas`, { method: 'POST' })
}

/** Borra las balotas y devuelve la partida a pendiente. Destructivo. */
export function reiniciarSorteo(partidaId: number): Promise<void> {
  return pedir<void>(`${base(partidaId)}/balotas`, { method: 'DELETE' })
}

type Transicion = 'iniciar' | 'pausar' | 'reanudar' | 'finalizar'

export function cambiarEstado(
  partidaId: number,
  transicion: Transicion,
): Promise<EstadoSorteo> {
  return pedir<EstadoSorteo>(`${base(partidaId)}/${transicion}`, {
    method: 'POST',
  })
}
