import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

/**
 * Botón base del sistema de diseño (convención shadcn/ui).
 *
 * Las variantes usan únicamente tokens de la paleta definidos en index.css,
 * nunca colores sueltos de Tailwind.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-semibold transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background cursor-pointer",
  {
    variants: {
      variant: {
        // Acción principal: dorado. Es la que más pesa visualmente, usar una
        // sola por pantalla.
        default:
          'bg-primary text-primary-foreground shadow-sm hover:brightness-110 active:brightness-95',
        // Acción positiva/confirmación. Comparte el verde con el último número
        // cantado, así que no abusar de ella fuera de ese contexto.
        success:
          'bg-success text-success-foreground shadow-sm hover:brightness-110',
        destructive:
          'bg-destructive text-destructive-foreground shadow-sm hover:brightness-110',
        outline:
          'border border-border bg-transparent hover:bg-surface-2 hover:text-foreground',
        secondary: 'bg-surface-2 text-foreground hover:brightness-125',
        ghost: 'hover:bg-surface-2 hover:text-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-12 rounded-lg px-6 text-base',
        icon: 'size-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    /** Renderiza el hijo en lugar de un <button> (ej. para un <Link>). */
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : 'button'

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
