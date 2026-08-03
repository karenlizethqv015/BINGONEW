import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { actualizarPartida } from '@/lib/partidas'
import { cn } from '@/lib/utils'

/** Límites razonables para el ritmo del sorteo, en segundos. */
const MINIMO = 2
const MAXIMO = 60
const PASO = 1

interface Props {
  partidaId: number
  /** Valor actual, tal como llega por el WebSocket. */
  segundos: number
  className?: string
}

/**
 * Control del tiempo entre balotas, ajustable **con el sorteo en marcha**.
 *
 * Es el cronómetro que el administrador toca según cómo vaya la sala: más
 * despacio si la gente no alcanza a marcar, más rápido si la partida se está
 * alargando. Guardarlo emite la sincronización a todas las pantallas, lo que
 * importa porque el reloj del sorteo automático vive en el navegador: sin ese
 * aviso la balotera seguiría cantando al ritmo viejo.
 *
 * El valor que se muestra es siempre el que llega por el WebSocket, no un
 * estado propio: así dos pestañas abiertas nunca muestran cadencias distintas.
 */
export function Cronometro({ partidaId, segundos, className }: Props) {
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Mientras se guarda se muestra el valor pedido, para que el botón responda
  // al instante en vez de esperar a que dé la vuelta por el servidor.
  const [pendiente, setPendiente] = useState<number | null>(null)

  useEffect(() => {
    // Llegó el valor confirmado: se deja de mostrar el provisional.
    setPendiente(null)
  }, [segundos])

  const mostrado = pendiente ?? segundos

  const ajustar = async (delta: number) => {
    const nuevo = Math.min(MAXIMO, Math.max(MINIMO, mostrado + delta))
    if (nuevo === mostrado) return

    setPendiente(nuevo)
    setGuardando(true)
    setError(null)
    try {
      await actualizarPartida(partidaId, {
        duracion_segundos_entre_balota: nuevo,
      })
    } catch (e) {
      setPendiente(null)
      setError(e instanceof Error ? e.message : 'No se pudo guardar el ritmo.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm text-muted-foreground">Ritmo del sorteo</span>

        <div className="flex items-center gap-1.5">
          <Button
            size="sm"
            variant="outline"
            aria-label="Más rápido (un segundo menos)"
            disabled={guardando || mostrado <= MINIMO}
            onClick={() => void ajustar(-PASO)}
          >
            −
          </Button>

          <span className="w-16 text-center text-lg font-bold tabular">
            {mostrado}s
          </span>

          <Button
            size="sm"
            variant="outline"
            aria-label="Más despacio (un segundo más)"
            disabled={guardando || mostrado >= MAXIMO}
            onClick={() => void ajustar(PASO)}
          >
            +
          </Button>
        </div>
      </div>

      {error ? (
        <p className="text-xs text-destructive">{error}</p>
      ) : (
        <p className="text-xs text-muted-foreground">
          Se puede cambiar con el sorteo en marcha; se aplica en todas las
          pantallas.
        </p>
      )}
    </div>
  )
}
