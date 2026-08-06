import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ETIQUETA_ESTADO, listarPartidas, type Partida } from '@/lib/partidas'
import { cn } from '@/lib/utils'

interface Vista {
  to: string
  titulo: string
  quien: string
  descripcion: string
  /** Enlace directo a la partida en curso, si hay una. */
  conPartida?: (id: number) => string
  /** Se abre en otra pestaña: es la que se proyecta. */
  nuevaPestana?: boolean
  destacada?: boolean
}

const VISTAS: Vista[] = [
  {
    to: '/admin',
    titulo: 'Administración',
    quien: 'Para quien dirige la jornada',
    descripcion:
      'Arma la partida, canta las balotas y sigue en vivo el recaudo, los premios y quién va ganando.',
    destacada: true,
  },
  {
    to: '/transmision',
    titulo: 'Tablero de sala',
    quien: 'Para proyectar en el televisor',
    descripcion:
      'Los 75 números con el último cantado en verde, las balotas recientes y los premios en juego.',
    conPartida: (id) => `/transmision?partida=${id}`,
    nuevaPestana: true,
  },
  {
    to: '/jugador',
    titulo: 'Cartón del jugador',
    quien: 'Para el celular de cada asistente',
    descripcion:
      'El cartón se marca solo con cada balota que sale, y avisa en cuanto hace bingo.',
    conPartida: (id) => `/jugador?partida=${id}`,
  },
]

/**
 * Portada: la puerta de entrada mientras no hay login (el login es de la Fase 2).
 *
 * Además de explicar para qué sirve cada vista, busca la partida que está viva y
 * enlaza directamente a ella. Sin eso, enseñar la plataforma obliga a ir
 * copiando identificadores de una pantalla a otra.
 */
export function Inicio() {
  const [enJuego, setEnJuego] = useState<Partida | null>(null)

  useEffect(() => {
    let vigente = true

    void listarPartidas()
      .then((lista) => {
        if (!vigente) return
        setEnJuego(lista.find((p) => p.estado !== 'finalizada') ?? null)
      })
      .catch(() => {
        // Sin backend no hay partida que enseñar, pero los enlaces siguen
        // sirviendo: cada vista avisa por su cuenta si no hay conexión.
      })

    return () => {
      vigente = false
    }
  }, [])

  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <p className="text-sm font-medium uppercase tracking-widest text-primary">
          Bingo de 75 bolas
        </p>
        <h1 className="max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
          Toda la jornada de bingo,{' '}
          <span className="text-primary">en tiempo real</span>
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          Una sola partida alimenta las tres pantallas a la vez: el control del
          sorteo, el tablero que se proyecta en la sala y el cartón que cada
          jugador lleva en el celular. La balota sale una vez y aparece en todas.
        </p>

        {enJuego && (
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <span className="flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-1.5 text-sm">
              <span
                className={cn(
                  'size-2 rounded-full',
                  enJuego.estado === 'en_curso'
                    ? 'bg-success shadow-[0_0_8px] shadow-success'
                    : 'bg-primary',
                )}
                aria-hidden
              />
              Juego{' '}
              <span className="font-semibold tabular">
                {enJuego.numero_consecutivo}
              </span>{' '}
              · {ETIQUETA_ESTADO[enJuego.estado]}
            </span>
          </div>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {VISTAS.map((vista) => {
          const destino =
            enJuego && vista.conPartida ? vista.conPartida(enJuego.id) : vista.to

          return (
            <Card
              key={vista.to}
              className={cn(
                'flex flex-col transition-colors',
                vista.destacada && 'border-primary/40',
              )}
            >
              <CardHeader>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">
                  {vista.quien}
                </p>
                <CardTitle className="text-xl">{vista.titulo}</CardTitle>
                <CardDescription>{vista.descripcion}</CardDescription>
              </CardHeader>
              <CardContent className="mt-auto">
                <Button
                  asChild
                  size="sm"
                  variant={vista.destacada ? 'default' : 'outline'}
                >
                  {vista.nuevaPestana ? (
                    <a href={destino} target="_blank" rel="noreferrer">
                      Abrir ↗
                    </a>
                  ) : (
                    <Link to={destino}>Abrir</Link>
                  )}
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </section>

      <section className="rounded-lg border border-border bg-surface px-5 py-4">
        <h2 className="font-semibold">¿Primera vez?</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          El orden es: dibujar las formas de ganar en el{' '}
          <Link
            to="/admin/figuras"
            className="text-primary underline-offset-4 hover:underline"
          >
            catálogo de figuras
          </Link>
          , crear una{' '}
          <Link
            to="/admin/partidas"
            className="text-primary underline-offset-4 hover:underline"
          >
            partida
          </Link>{' '}
          eligiendo cuáles se juegan y con qué premio, generar sus cartones, y
          empezar a cantar desde la balotera.
        </p>
      </section>
    </div>
  )
}
