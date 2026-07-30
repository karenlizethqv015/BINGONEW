import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

/**
 * Vista del vendedor.
 *
 * Marcador de posición. El módulo de ventas es Fase 2 completa: no debe
 * implementarse mientras la Fase 1 no esté aprobada (ver CLAUDE.md).
 */
export function Vendedor() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Vendedor</h1>
        <p className="text-muted-foreground">
          Módulo de ventas — Fase 2. No se implementa hasta que el cliente
          apruebe el MVP.
        </p>
      </header>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Fuera del alcance actual</CardTitle>
          <CardDescription>
            Registro de compradores, venta de cartones y consulta de ventas.
            La ruta existe solo para dejar fijada la convención de navegación.
          </CardDescription>
        </CardHeader>
        <CardContent />
      </Card>
    </div>
  )
}
