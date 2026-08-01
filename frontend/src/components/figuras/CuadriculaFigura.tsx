import { useEffect, useRef } from 'react'

import {
  LETRAS,
  alternarCelda,
  esCeldaLibre,
  fijarCelda,
  type Patron,
} from '@/lib/bingo'
import { cn } from '@/lib/utils'

interface Props {
  patron: Patron
  /** Si se pasa, la cuadrícula es editable. Si no, es solo de lectura. */
  onChange?: (patron: Patron) => void
  /** `mini` para las tarjetas del catálogo, `grande` para el editor. */
  tamano?: 'mini' | 'grande'
  /** Texto alternativo cuando es de solo lectura. */
  etiqueta?: string
}

/**
 * Cuadrícula 5x5 de una figura.
 *
 * En modo editable se puede hacer clic en una celda o **arrastrar** para pintar
 * varias de una vez, que es lo cómodo al dibujar líneas y marcos. El arrastre
 * fija todas las celdas al mismo valor que la primera, para que al pasar por
 * encima de una ya marcada no se alterne sin querer.
 *
 * Las celdas son botones de verdad, así que también funciona con teclado.
 */
export function CuadriculaFigura({
  patron,
  onChange,
  tamano = 'grande',
  etiqueta,
}: Props) {
  const editable = Boolean(onChange)
  const esMini = tamano === 'mini'

  // Valor que está aplicando el arrastre actual (true = pintando, false =
  // borrando). null significa que no hay arrastre en curso.
  const pintando = useRef<boolean | null>(null)

  useEffect(() => {
    // El arrastre debe terminar aunque se suelte el botón fuera de la
    // cuadrícula, o se quedaría "pegado".
    const terminar = () => {
      pintando.current = null
    }
    window.addEventListener('mouseup', terminar)
    return () => window.removeEventListener('mouseup', terminar)
  }, [])

  const iniciarArrastre = (fila: number, columna: number) => {
    if (!onChange) return
    pintando.current = !patron[fila][columna]
    onChange(alternarCelda(patron, fila, columna))
  }

  const continuarArrastre = (fila: number, columna: number) => {
    if (!onChange || pintando.current === null) return
    onChange(fijarCelda(patron, fila, columna, pintando.current))
  }

  const cuadricula = (
    <div
      className={cn(
        'grid grid-cols-5',
        esMini ? 'gap-0.5' : 'gap-1.5',
        !editable && 'pointer-events-none',
      )}
      role={editable ? undefined : 'img'}
      aria-label={editable ? undefined : etiqueta}
    >
      {patron.map((fila, f) =>
        fila.map((marcada, c) => {
          const libre = esCeldaLibre(f, c)

          const contenido = (
            <>
              {!esMini && libre && (
                <span
                  className={cn(
                    'text-[9px] font-semibold uppercase tracking-wider',
                    marcada ? 'text-primary-foreground/70' : 'text-muted-foreground',
                  )}
                >
                  Libre
                </span>
              )}
            </>
          )

          const clases = cn(
            'flex items-center justify-center rounded-md border transition-all duration-150',
            esMini ? 'size-3.5 rounded-sm' : 'aspect-square',
            marcada
              ? 'border-primary bg-primary text-primary-foreground'
              : 'border-border bg-surface-2',
            !marcada && libre && 'border-dashed',
            editable &&
              'cursor-pointer hover:border-primary/70 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring',
            editable && marcada && 'shadow-[0_0_12px] shadow-primary/30',
          )

          if (!editable) {
            return <div key={`${f}-${c}`} className={clases} />
          }

          return (
            <button
              key={`${f}-${c}`}
              type="button"
              className={clases}
              aria-pressed={marcada}
              aria-label={`Fila ${f + 1}, columna ${LETRAS[c]}${libre ? ' (casilla libre)' : ''}`}
              onMouseDown={() => iniciarArrastre(f, c)}
              onMouseEnter={() => continuarArrastre(f, c)}
              // El teclado no arrastra: alterna la celda directamente.
              onKeyDown={(evento) => {
                if (evento.key === 'Enter' || evento.key === ' ') {
                  evento.preventDefault()
                  onChange?.(alternarCelda(patron, f, c))
                }
              }}
            >
              {contenido}
            </button>
          )
        }),
      )}
    </div>
  )

  if (esMini) return cuadricula

  return (
    <div className="space-y-1.5 select-none">
      <div className="grid grid-cols-5 gap-1.5">
        {LETRAS.map((letra) => (
          <div
            key={letra}
            className="text-center text-sm font-bold tracking-widest text-primary"
          >
            {letra}
          </div>
        ))}
      </div>
      {cuadricula}
    </div>
  )
}
