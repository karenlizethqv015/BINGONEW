import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

/**
 * Vista del jugador.
 *
 * Marcador de posición. El cartón con marcado automático es la tarea #5 de la
 * Fase 1; el login por cédula es Fase 2.
 */
export function Jugador() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Jugador</h1>
        <p className="text-muted-foreground">
          El cartón con marcado automático se implementa en la tarea #5 de la
          Fase 1.
        </p>
      </header>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Pendiente</CardTitle>
          <CardDescription>
            Aquí irá el cartón del jugador, que se marca solo a medida que se
            cantan las balotas y avisa cuando se completa una forma de ganar.
          </CardDescription>
        </CardHeader>
        <CardContent />
      </Card>
    </div>
  )
}
