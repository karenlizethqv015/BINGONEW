import { Button } from '@/components/ui/button'
import { textoCartones, type Bingo } from '@/lib/ganadores'
import { formatearPesos } from '@/lib/partidas'
import { cn } from '@/lib/utils'

interface Props {
  bingos: Bingo[]
  /** Cuántos cartones ganaron en total, sumando todas las formas. */
  totalCartones: number
  /** Hay un bingo recién cantado que el administrador todavía no ha atendido. */
  sinAtender: boolean
  onCerrar: () => void
  /**
   * Reanudar el sorteo, que se pausó solo al cantarse el bingo.
   *
   * Opcional a propósito: solo lo reciben las pantallas de mando. El tablero de
   * transmisión se proyecta delante de la sala y no lleva controles.
   */
  onReanudar?: () => void
  className?: string
}

/**
 * El aviso de que alguien hizo bingo, para la pantalla del administrador.
 *
 * **No se desvanece solo.** Un aviso que desaparece a los tres segundos es
 * justo lo que no sirve aquí: el administrador tiene que actuar sobre él —
 * comprobar el cartón, pausar, pagar— y bien puede estar mirando hacia la sala
 * cuando salta. Se queda hasta que lo cierre.
 *
 * Mientras no lo atienda late en verde; al cerrarlo se queda quieto pero sigue
 * visible, porque el bingo no deja de ser cierto por haberlo leído.
 *
 * El sorteo se detiene solo al cantarse un bingo, así que reanudarlo es la
 * acción natural sobre este aviso y el botón vive aquí, no perdido entre los
 * controles de más abajo.
 */
export function AvisoBingo({
  bingos,
  totalCartones,
  sinAtender,
  onCerrar,
  onReanudar,
  className,
}: Props) {
  if (bingos.length === 0) return null

  return (
    <section
      // `alert` hace que un lector de pantalla lo anuncie al aparecer.
      role="alert"
      className={cn(
        'overflow-hidden rounded-lg border-2 border-success bg-success/10',
        sinAtender && 'animate-bingo animate-bingo-latido',
        className,
      )}
    >
      <header className="flex flex-wrap items-center justify-between gap-3 bg-success px-5 py-3 text-success-foreground">
        <div className="flex items-baseline gap-3">
          <span className="text-2xl font-black tracking-wide">¡BINGO!</span>
          <span className="text-sm font-semibold tabular">
            {textoCartones(totalCartones)}
            {bingos.length > 1 && ` · ${bingos.length} formas`}
          </span>
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {onReanudar && (
            <span className="text-sm font-semibold">
              El sorteo se detuvo.
            </span>
          )}
          {onReanudar && (
            <Button size="sm" variant="secondary" onClick={onReanudar}>
              Reanudar sorteo
            </Button>
          )}
          {sinAtender && (
            <Button size="sm" variant="ghost" onClick={onCerrar}>
              Entendido
            </Button>
          )}
        </div>
      </header>

      <div className="divide-y divide-success/20">
        {bingos.map((bingo) => (
          <div
            key={bingo.partida_figura_id}
            className="flex flex-wrap items-start justify-between gap-x-6 gap-y-2 px-5 py-3"
          >
            <div className="space-y-1.5">
              <p className="font-semibold">{bingo.figura}</p>
              <div className="flex flex-wrap gap-1.5">
                {bingo.cartones.map((carton) => (
                  <span
                    key={carton.carton_id}
                    className="rounded bg-success px-2 py-0.5 text-sm font-bold tabular text-success-foreground"
                  >
                    {carton.codigo}
                  </span>
                ))}
              </div>
            </div>

            <div className="text-right text-sm">
              <p className="font-bold tabular text-primary">
                {formatearPesos(bingo.valor_premio)}
              </p>
              <p className="text-muted-foreground">
                con la balota{' '}
                <span className="font-semibold tabular text-foreground">
                  {bingo.numero_balota}
                </span>{' '}
                <span className="tabular">(nº {bingo.orden_balota})</span>
              </p>
              {bingo.cartones.length > 1 && (
                <p className="text-muted-foreground">
                  se reparte entre {bingo.cartones.length}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
