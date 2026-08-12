import { Link } from 'react-router-dom'

import { EstadoDelBackend } from '@/components/EstadoDelBackend'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

/**
 * Panel de administración — reglas básicas del juego, no la operación diaria.
 *
 * Hasta la ronda de ajustes pedida por el cliente, esta pantalla concentraba
 * partidas, balotera y cartones. Eso pasó al rol operador (`/operador`), que es
 * quien de verdad los toca constantemente durante una jornada. Lo que le queda
 * al administrador es el catálogo de figuras: cambia poco y es una decisión de
 * fondo sobre las reglas del juego, no de la partida del día.
 */
export function Admin() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Administración</h1>
        <p className="text-muted-foreground">
          Catálogo de figuras y ajustes básicos del juego. La operación de las
          partidas —balotera, cartones, control del sorteo— vive en el panel
          de operador.
        </p>
      </header>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Catálogo de figuras</CardTitle>
          <CardDescription>
            Las formas de ganar que después se eligen por partida en el panel
            de operador.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button asChild size="sm">
            <Link to="/admin/figuras">Abrir el catálogo</Link>
          </Button>
          <Button asChild size="sm" variant="outline">
            <Link to="/operador">Ir al panel de operador</Link>
          </Button>
        </CardContent>
      </Card>

      <EstadoDelBackend />
    </div>
  )
}
