import { LETRAS, estaMarcada, type MatrizCarton } from '@/lib/bingo'
import { cn } from '@/lib/utils'

interface Props {
  numeros: MatrizCarton
  /** Identificación visible del cartón, ej. "A-12". */
  etiqueta?: string
  tamano?: 'normal' | 'compacto'
  /**
   * Números ya cantados en la partida. Si se pasa, el cartón se marca solo:
   * llega del hook `usePartidaEnVivo`, no hace falta pedirlo al servidor.
   */
  marcados?: ReadonlySet<number>
  /** La balota que acaba de salir, para resaltarla aparte de las anteriores. */
  ultimo?: number | null
  className?: string
}

/**
 * Cartón de bingo de 75 bolas.
 *
 * La casilla libre del centro llega como `null` desde el backend y siempre
 * cuenta como marcada.
 *
 * El marcado se resuelve aquí, en el cliente: el cartón ya está en pantalla y
 * las balotas llegan por WebSocket, así que cruzar ambos es inmediato.
 * Preguntárselo al servidor en cada balota sería tráfico inútil y añadiría
 * retraso justo donde más se nota.
 */
export function CartonBingo({
  numeros,
  etiqueta,
  tamano = 'normal',
  marcados,
  ultimo,
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
          fila.map((valor, c) => {
            const libre = valor === null
            const marcada = marcados ? estaMarcada(valor, marcados) : libre
            const esUltima = ultimo != null && valor === ultimo

            return (
              <div
                key={`${f}-${c}`}
                className={cn(
                  'flex aspect-square items-center justify-center rounded font-semibold tabular transition-colors duration-200',
                  compacto ? 'text-[10px]' : 'text-sm',
                  esUltima
                    ? 'animate-balota bg-success text-success-foreground shadow-[0_0_10px] shadow-success/40'
                    : marcada
                      ? libre
                        ? 'border border-dashed border-primary/50 bg-primary/15 text-primary'
                        : 'bg-primary text-primary-foreground'
                      : 'bg-surface-2 text-foreground',
                )}
                aria-label={
                  libre
                    ? 'Casilla libre'
                    : `${valor}${marcada ? ', marcado' : ''}`
                }
              >
                {libre ? (
                  <span className={compacto ? 'text-[8px]' : 'text-[9px]'}>★</span>
                ) : (
                  valor
                )}
              </div>
            )
          }),
        )}
      </div>
    </div>
  )
}
