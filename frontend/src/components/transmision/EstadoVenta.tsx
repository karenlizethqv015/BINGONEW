import { cn } from '@/lib/utils'

interface Props {
  /** `null` mientras todavía no ha llegado el primer dato del WebSocket. */
  ventaAbierta: boolean | null
}

/**
 * El «bombillo»: verde si se siguen vendiendo cartones, rojo si no.
 *
 * Es de solo lectura aquí — el operador lo enciende y apaga desde su panel
 * (`/operador`). Independiente del estado del sorteo: una partida puede estar
 * `en_curso` con la venta ya cerrada.
 */
export function EstadoVenta({ ventaAbierta }: Props) {
  return (
    <span className="flex items-center gap-1.5 xl:gap-2">
      <span
        className={cn(
          'size-2.5 shrink-0 rounded-full xl:size-3',
          ventaAbierta === null
            ? 'bg-muted-foreground/30'
            : ventaAbierta
              ? 'bg-success shadow-[0_0_8px] shadow-success'
              : 'bg-destructive shadow-[0_0_8px] shadow-destructive',
        )}
        aria-hidden
      />
      <span className="text-xs text-muted-foreground xl:text-sm">
        {ventaAbierta === null
          ? 'Venta —'
          : ventaAbierta
            ? 'Venta abierta'
            : 'Venta cerrada'}
      </span>
    </span>
  )
}
