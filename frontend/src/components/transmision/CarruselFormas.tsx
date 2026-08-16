import { useEffect, useState } from 'react'

import { CuadriculaFigura } from '@/components/figuras/CuadriculaFigura'
import { formatearPesos, type FormaSeleccionada } from '@/lib/partidas'
import { cn } from '@/lib/utils'

/** Cada cuántos milisegundos cambia la forma que se muestra. */
const INTERVALO_MS = 5000

interface Props {
  formas: FormaSeleccionada[]
  /** ids de `partida_figura` que ya se ganaron. */
  ganadas: Set<number>
}

/**
 * Muestra las formas de ganar de a una, alternando en bucle.
 *
 * Antes la pantalla de transmisión listaba todas las formas apiladas — con
 * varias formas eso ocupaba demasiado espacio vertical para caber sin scroll.
 * El cliente pidió condensarlo a un solo cuadro que va rotando.
 */
export function CarruselFormas({ formas, ganadas }: Props) {
  const [indice, setIndice] = useState(0)

  // Si cambió la lista (se agregó o quitó una forma), no seguir apuntando a
  // una posición que ya no existe.
  useEffect(() => {
    setIndice(0)
  }, [formas.length])

  useEffect(() => {
    if (formas.length <= 1) return
    const id = window.setInterval(
      () => setIndice((i) => (i + 1) % formas.length),
      INTERVALO_MS,
    )
    return () => window.clearInterval(id)
  }, [formas.length])

  const forma = formas[indice] as FormaSeleccionada | undefined
  const ganada = forma !== undefined && ganadas.has(forma.id)

  return (
    <section className="flex min-h-0 flex-col items-center justify-center gap-1 overflow-hidden rounded-xl border border-border bg-surface p-2 text-center xl:gap-2 xl:p-3">
      <h2 className="shrink-0 text-[10px] uppercase tracking-wider text-muted-foreground xl:text-xs">
        Formas de ganar
      </h2>

      {forma === undefined ? (
        <p className="text-xs text-muted-foreground">Sin formas configuradas.</p>
      ) : (
        <>
          <div
            className={cn(
              'w-full max-w-[5.5rem] shrink sm:max-w-[7rem] xl:max-w-[8rem]',
              ganada && 'opacity-50',
            )}
          >
            <CuadriculaFigura
              patron={forma.figura.patron}
              tamano="grande"
              etiqueta={forma.figura.nombre}
            />
          </div>

          <p
            className={cn(
              'w-full truncate text-xs font-semibold xl:text-sm',
              ganada && 'text-muted-foreground line-through',
            )}
          >
            {forma.figura.nombre}
          </p>

          <p
            className={cn(
              'text-sm font-bold tabular xl:text-lg',
              ganada ? 'text-success' : 'text-primary',
            )}
          >
            {formatearPesos(forma.valor_premio)}
          </p>

          <span
            className={cn(
              'shrink-0 rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide xl:text-[10px]',
              ganada
                ? 'bg-success text-success-foreground'
                : 'bg-primary/20 text-primary',
            )}
          >
            {ganada ? 'Ganada' : 'Jugando'}
          </span>

          {formas.length > 1 && (
            <div className="flex shrink-0 gap-1 pt-0.5">
              {formas.map((f, i) => (
                <span
                  key={f.id}
                  className={cn(
                    'size-1.5 rounded-full transition-colors',
                    i === indice ? 'bg-primary' : 'bg-surface-2',
                  )}
                  aria-hidden
                />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}
