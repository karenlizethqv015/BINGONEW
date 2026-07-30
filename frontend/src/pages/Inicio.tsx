import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

const VISTAS = [
  {
    to: '/admin',
    titulo: 'Administración',
    descripcion:
      'Control de la partida: iniciar, pausar y finalizar el sorteo, y ver el estado en tiempo real.',
  },
  {
    to: '/transmision',
    titulo: 'Transmisión',
    descripcion:
      'Vista pública para proyectar en la sala. Tablero de 75 números y últimas balotas cantadas.',
  },
  {
    to: '/jugador',
    titulo: 'Jugador',
    descripcion:
      'Cartón propio con marcado automático de los números cantados y aviso de bingo.',
  },
]

/** Portada del proyecto: atajo a cada vista mientras no hay login. */
export function Inicio() {
  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="text-sm font-medium uppercase tracking-widest text-primary">
          Fase 0 · Scaffolding
        </p>
        <h1 className="text-4xl font-bold tracking-tight">
          Plataforma web de bingo
        </h1>
        <p className="max-w-2xl text-muted-foreground">
          El proyecto está inicializado y conectado de punta a punta. Todavía no
          hay funcionalidad de negocio: eso arranca en la Fase 1 con el módulo de
          creación de figuras.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {VISTAS.map((vista) => (
          <Card key={vista.to} className="flex flex-col">
            <CardHeader>
              <CardTitle>{vista.titulo}</CardTitle>
              <CardDescription>{vista.descripcion}</CardDescription>
            </CardHeader>
            <CardContent className="mt-auto">
              <Button asChild variant="outline" size="sm">
                <Link to={vista.to}>Abrir vista</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  )
}
