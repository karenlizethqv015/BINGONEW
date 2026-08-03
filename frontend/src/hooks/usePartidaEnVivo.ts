import { useEffect, useRef, useState } from 'react'

import { urlWebSocket } from '@/lib/api'
import type { Balota, EventoPartida } from '@/lib/balotas'
import { CUADRO_VACIO, type CuadroGanadores } from '@/lib/ganadores'
import type { EstadoPartida } from '@/lib/partidas'

export type EstadoConexion = 'conectando' | 'conectado' | 'desconectado'

export interface PartidaEnVivo {
  conexion: EstadoConexion
  estado: EstadoPartida | null
  numeroConsecutivo: number | null
  duracionEntreBalotas: number | null
  /** Todas las balotas cantadas, en el orden en que salieron. */
  balotas: Balota[]
  /** La más reciente, o null si no ha salido ninguna. */
  ultima: Balota | null
  /** Los números ya cantados. Pensado para marcar el tablero de un vistazo. */
  cantadas: Set<number>
  totalCantadas: number
  restantes: number
  /**
   * Quién ha ganado y quién está a una o dos balotas de ganar. Lo calcula el
   * backend y llega ya resuelto: aquí no se decide nada de eso.
   */
  ganadores: CuadroGanadores
}

const ESTADO_INICIAL: PartidaEnVivo = {
  conexion: 'conectando',
  estado: null,
  numeroConsecutivo: null,
  duracionEntreBalotas: null,
  balotas: [],
  ultima: null,
  cantadas: new Set(),
  totalCantadas: 0,
  restantes: 75,
  ganadores: CUADRO_VACIO,
}

/** Espera entre reintentos de reconexión, en milisegundos. */
const ESPERA_INICIAL = 1000
const ESPERA_MAXIMA = 10000

/**
 * Se suscribe al canal en tiempo real de una partida.
 *
 * Es el punto único por el que las vistas reciben las balotas. El tablero de
 * transmisión (tarea #6), el cartón del jugador (#5) y el panel de
 * administración (#7) usan este mismo hook y el mismo endpoint: hay **un
 * WebSocket por partida**, no uno por vista.
 *
 * Al conectarse, el backend manda el estado completo con todas las balotas ya
 * cantadas, así que una pantalla que se abre a mitad de partida —o que se
 * reconecta tras una caída de red— queda al día sola, sin pedir nada más.
 */
export function usePartidaEnVivo(partidaId: number): PartidaEnVivo {
  const [datos, setDatos] = useState<PartidaEnVivo>(ESTADO_INICIAL)

  // Refs y no estado: cambiarlos no debe provocar un re-render ni reabrir el
  // WebSocket.
  const socketRef = useRef<WebSocket | null>(null)
  const temporizadorRef = useRef<number | null>(null)
  const esperaRef = useRef(ESPERA_INICIAL)
  const desmontadoRef = useRef(false)

  useEffect(() => {
    if (!Number.isFinite(partidaId)) return

    desmontadoRef.current = false
    setDatos(ESTADO_INICIAL)

    const conectar = () => {
      if (desmontadoRef.current) return

      const socket = new WebSocket(urlWebSocket(`/ws/partida/${partidaId}`))
      socketRef.current = socket

      socket.onopen = () => {
        // Reconexión conseguida: se vuelve a la espera corta.
        esperaRef.current = ESPERA_INICIAL
        setDatos((previo) => ({ ...previo, conexion: 'conectado' }))
      }

      socket.onmessage = (mensaje) => {
        const evento = JSON.parse(mensaje.data) as EventoPartida
        setDatos((previo) => aplicar(previo, evento))
      }

      socket.onerror = () => {
        setDatos((previo) => ({ ...previo, conexion: 'desconectado' }))
      }

      socket.onclose = () => {
        setDatos((previo) => ({ ...previo, conexion: 'desconectado' }))
        if (desmontadoRef.current) return

        // Espera creciente: si el backend está caído, no se le machaca con
        // reintentos cada segundo.
        temporizadorRef.current = window.setTimeout(conectar, esperaRef.current)
        esperaRef.current = Math.min(esperaRef.current * 2, ESPERA_MAXIMA)
      }
    }

    conectar()

    return () => {
      desmontadoRef.current = true
      if (temporizadorRef.current !== null) {
        window.clearTimeout(temporizadorRef.current)
      }
      socketRef.current?.close()
    }
  }, [partidaId])

  return datos
}

/** Aplica un evento al estado acumulado. */
function aplicar(previo: PartidaEnVivo, evento: EventoPartida): PartidaEnVivo {
  switch (evento.tipo) {
    case 'sincronizacion':
      // Reemplaza todo: es la foto completa que manda el backend al conectar.
      return {
        conexion: 'conectado',
        estado: evento.estado,
        numeroConsecutivo: evento.numero_consecutivo,
        duracionEntreBalotas: evento.duracion_segundos_entre_balota,
        balotas: evento.balotas,
        ultima: evento.balotas.at(-1) ?? null,
        cantadas: new Set(evento.balotas.map((b) => b.numero)),
        totalCantadas: evento.total_cantadas,
        restantes: evento.restantes,
        // El cuadro de ganadores no viaja en este evento: llega en el suyo,
        // justo detrás. Se conserva el anterior para que al reconectarse no
        // parpadee un «nadie ha ganado» que es mentira.
        ganadores: previo.ganadores,
      }

    case 'balota': {
      // Puede llegar repetida si se reconecta justo al cantar: no se duplica.
      if (previo.cantadas.has(evento.balota.numero)) return previo

      const cantadas = new Set(previo.cantadas)
      cantadas.add(evento.balota.numero)

      return {
        ...previo,
        estado: evento.estado,
        balotas: [...previo.balotas, evento.balota],
        ultima: evento.balota,
        cantadas,
        totalCantadas: evento.total_cantadas,
        restantes: evento.restantes,
      }
    }

    case 'estado':
      return {
        ...previo,
        estado: evento.estado,
        totalCantadas: evento.total_cantadas,
        restantes: evento.restantes,
        // Reiniciar el sorteo deja la partida pendiente y sin balotas.
        ...(evento.total_cantadas === 0
          ? {
              balotas: [],
              ultima: null,
              cantadas: new Set<number>(),
              ganadores: CUADRO_VACIO,
            }
          : {}),
      }

    case 'ganadores':
      // Foto completa, igual que la sincronización: reemplaza, no acumula.
      return { ...previo, ganadores: evento }

    default:
      return previo
  }
}
