import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { CartonCerca } from '@/lib/ganadores'
import { cn } from '@/lib/utils'

interface Props {
  cerca: CartonCerca[]
  /** Totales reales: la lista viene recortada, estos conteos no. */
  aUna: number
  aDos: number
}

/**
 * Los cartones a una y a dos balotas de ganar.
 *
 * Es información **solo del administrador**: al jugador le quitaría la emoción
 * y al tablero de la sala lo convertiría en un delator. Sirve para saber que la
 * partida está a punto de resolverse y prepararse para verificar el cartón.
 */
export function CercaDeGanar({ cerca, aUna, aDos }: Props) {
  const grupos = [
    {
      faltan: 1,
      titulo: 'A una balota',
      total: aUna,
      items: cerca.filter((c) => c.faltan === 1),
      destacado: true,
    },
    {
      faltan: 2,
      titulo: 'A dos balotas',
      total: aDos,
      items: cerca.filter((c) => c.faltan === 2),
      destacado: false,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cerca de ganar</CardTitle>
        <CardDescription>
          Solo lo ves tú: ni el jugador ni el tablero de la sala.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-5">
        {aUna === 0 && aDos === 0 && (
          <p className="text-sm text-muted-foreground">
            Ningún cartón está todavía a dos balotas de completar una forma.
          </p>
        )}

        {grupos.map((grupo) =>
          grupo.total === 0 ? null : (
            <div key={grupo.faltan} className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span
                  className={cn(
                    'grid size-7 shrink-0 place-items-center rounded-full text-sm font-bold tabular',
                    grupo.destacado
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-surface-2 text-muted-foreground',
                  )}
                >
                  {grupo.total}
                </span>
                <h3
                  className={cn(
                    'font-semibold',
                    grupo.destacado ? 'text-primary' : 'text-muted-foreground',
                  )}
                >
                  {grupo.titulo}
                </h3>
              </div>

              <ul className="space-y-1">
                {grupo.items.map((item) => (
                  <li
                    key={`${item.carton_id}-${item.partida_figura_id}`}
                    className={cn(
                      'flex flex-wrap items-center justify-between gap-x-3 gap-y-1 rounded-md px-2.5 py-1.5 text-sm',
                      grupo.destacado
                        ? 'bg-primary/10 ring-1 ring-primary/30'
                        : 'bg-surface-2',
                    )}
                  >
                    <span className="font-bold tabular">{item.codigo}</span>
                    <span className="min-w-0 flex-1 truncate text-muted-foreground">
                      {item.figura}
                    </span>
                    <span className="flex gap-1">
                      {item.numeros.map((numero) => (
                        <span
                          key={numero}
                          className="rounded bg-surface px-1.5 py-0.5 font-bold tabular text-foreground"
                        >
                          {numero}
                        </span>
                      ))}
                    </span>
                  </li>
                ))}
              </ul>

              {grupo.items.length < grupo.total && (
                <p className="text-xs text-muted-foreground">
                  y {grupo.total - grupo.items.length} más
                </p>
              )}
            </div>
          ),
        )}
      </CardContent>
    </Card>
  )
}
