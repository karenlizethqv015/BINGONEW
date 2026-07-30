import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Combina clases de Tailwind resolviendo los conflictos.
 *
 * Sin esto, `cn('p-2', 'p-4')` dejaría ambas clases y ganaría la que el CSS
 * ordene; con twMerge gana siempre la última, que es lo esperado al pasar
 * `className` desde afuera de un componente.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
