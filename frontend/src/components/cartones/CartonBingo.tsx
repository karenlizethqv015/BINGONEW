import { LETRAS, type MatrizCarton } from '@/lib/bingo'
import { cn } from '@/lib/utils'

interface Props {
  numeros: MatrizCarton
  /** Identificación visible del cartón, ej. "A-12". */
  etiqueta?: string
  tamano?: 'normal' | 'compacto'
  className?: string
}

/**
 * Cartón de bingo de 75 bolas, solo lectura.
 *
 * La casilla libre del centro llega como `null` desde el backend y se dibuja
 * como tal: no lleva número y siempre cuenta como marcada.
 *
 * El marcado automático de los números cantados es la tarea #5; este componente
 * es el que se ampliará entonces.
 */
export function CartonBingo({
  numeros,
  etiqueta,
  tamano = 'normal',
  className,
}: Props) {
  const compacto = tamano === 'compacto'

  return (
    <div
      className={cn(
        'rounded-lg border border-border bg-surface p-2.5',
        className,
      )}
    >
      {etiqueta && (
        <p
          className={cn(
            'mb-2 text-center font-semibold tabular text-muted-foreground',
            compacto ? 'text-[10px]' : 'text-xs',
          )}
        >
          {etiqueta}
        </p>
      )}

      <div className="grid grid-cols-5 gap-0.5">
        {LETRAS.map((letra) => (
          <div
            key={letra}
            className={cn(
              'py-0.5 text-center font-bold tracking-wider text-primary',
              compacto ? 'text-[10px]' : 'text-sm',
            )}
          >
            {letra}
          </div>
        ))}

        {numeros.map((fila, f) =>
          fila.map((valor, c) => (
            <div
              key={`${f}-${c}`}
              className={cn(
                'flex aspect-square items-center justify-center rounded font-semibold tabular',
                compacto ? 'text-[10px]' : 'text-sm',
                valor === null
                  ? 'border border-dashed border-primary/50 bg-primary/10 text-primary'
                  : 'bg-surface-2 text-foreground',
              )}
            >
              {valor === null ? (
                <span
                  className={compacto ? 'text-[8px]' : 'text-[9px]'}
                  aria-label="Casilla libre"
                >
                  ★
                </span>
              ) : (
                valor
              )}
            </div>
          )),
        )}
      </div>
    </div>
  )
}
