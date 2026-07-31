import type { Balota } from '@/lib/balotas'
import { cn } from '@/lib/utils'

interface Props {
  balota: Balota
  tamano?: 'grande' | 'normal' | 'mini'
  /** Resalta la balota como la última cantada. */
  destacada?: boolean
  className?: string
}

const TAMANOS = {
  grande: 'size-32 text-5xl',
  normal: 'size-16 text-2xl',
  mini: 'size-11 text-base',
} as const

const TAMANOS_LETRA = {
  grande: 'text-lg',
  normal: 'text-[10px]',
  mini: 'text-[9px]',
} as const

/**
 * Una balota de bingo, dibujada como la bola que sale de la balotera.
 *
 * Se usa en el control del sorteo y la reutilizará el tablero de transmisión
 * (tarea #6).
 */
export function Bola({
  balota,
  tamano = 'normal',
  destacada = false,
  className,
}: Props) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-full font-bold tabular shadow-lg',
        TAMANOS[tamano],
        destacada
          ? 'bg-success text-success-foreground shadow-success/30'
          : 'bg-primary text-primary-foreground shadow-primary/20',
        className,
      )}
      aria-label={`Balota ${balota.letra} ${balota.numero}`}
    >
      <span className={cn('font-semibold tracking-widest', TAMANOS_LETRA[tamano])}>
        {balota.letra}
      </span>
      <span className="leading-none">{balota.numero}</span>
    </div>
  )
}
