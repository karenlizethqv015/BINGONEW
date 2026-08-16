import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { ResumenPorForma } from '@/lib/ganadores'

interface Props {
  porForma: ResumenPorForma[]
}

/**
 * Cuántos cartones están a una balota de ganar, una línea por forma vigente.
 *
 * Es información **solo del administrador**: al jugador le quitaría la emoción
 * y al tablero de la sala lo convertiría en un delator. Antes mostraba una
 * lista detallada por cartón (código, figura, números que faltan); el cliente
 * pidió condensarla a un conteo por forma para que quepa en la pantalla sin
 * desplazarse — "cartones a una balota de ganar: N", una forma por línea.
 */
export function CercaDeGanar({ porForma }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Cerca de ganar</CardTitle>
        <CardDescription>
          Solo lo ves tú: ni el jugador ni el tablero de la sala.
        </CardDescription>
      </CardHeader>

      <CardContent>
        {porForma.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Ninguna forma sigue en juego todavía.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {porForma.map((forma) => (
              <li
                key={forma.partida_figura_id}
                className="flex items-center justify-between gap-3 py-2 text-sm"
              >
                <span className="min-w-0 truncate text-muted-foreground">
                  {forma.figura}
                </span>
                <span className="flex shrink-0 items-baseline gap-3">
                  <span>
                    Cartones a una balota de ganar:{' '}
                    <span className="font-bold tabular text-primary">
                      {forma.a_una}
                    </span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    a dos: <span className="font-semibold tabular">{forma.a_dos}</span>
                  </span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
