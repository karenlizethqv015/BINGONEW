import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  ETIQUETA_ESTADO,
  crearPartida,
  eliminarPartida,
  formatearPesos,
  listarPartidas,
  type Partida,
} from '@/lib/partidas'

/**
 * Lista de partidas y creación de una nueva.
 *
 * Es la versión simplificada de la Fase 1: la partida no cuelga de una jornada
 * ni de una sala, eso llega en la Fase 2. Los controles de sorteo
 * (iniciar/pausar/finalizar) son la tarea #7.
 */
export function Partidas() {
  const [partidas, setPartidas] = useState<Partida[]>([])
  const [precio, setPrecio] = useState('5000')
  const [duracion, setDuracion] = useState('5')
  const [porEliminar, setPorEliminar] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)
  const [creando, setCreando] = useState(false)

  const recargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      setPartidas(await listarPartidas())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron cargar las partidas.')
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    void recargar()
  }, [recargar])

  const crear = async () => {
    setCreando(true)
    setError(null)
    try {
      const partida = await crearPartida({
        precio_carton: Number(precio) || 0,
        duracion_segundos_entre_balota: Number(duracion) || 5,
      })
      setPartidas((previas) => [partida, ...previas])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo crear la partida.')
    } finally {
      setCreando(false)
    }
  }

  const confirmarEliminar = async (id: number) => {
    setError(null)
    try {
      await eliminarPartida(id)
      setPartidas((previas) => previas.filter((p) => p.id !== id))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo eliminar la partida.')
    } finally {
      setPorEliminar(null)
    }
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="text-sm font-medium uppercase tracking-widest text-primary">
          Administración
        </p>
        <h1 className="text-3xl font-bold tracking-tight">Partidas</h1>
        <p className="text-muted-foreground">
          Crea una partida y elige qué formas de ganar se juegan en ella.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,22rem)_1fr] lg:items-start">
        <Card className="lg:sticky lg:top-20">
          <CardHeader>
            <CardTitle>Nueva partida</CardTitle>
            <CardDescription>
              El número de juego se asigna automáticamente.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="precio" className="text-sm font-medium">
                Precio del cartón
              </label>
              <Input
                id="precio"
                // Igual que los premios: se escribe a mano, sin flechas de
                // incremento ni rueda del ratón.
                type="text"
                inputMode="numeric"
                value={precio}
                onChange={(e) => setPrecio(e.target.value.replace(/\D/g, ''))}
                className="tabular"
              />
              <p className="text-xs text-muted-foreground">
                {formatearPesos(Number(precio) || 0)}
              </p>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="duracion" className="text-sm font-medium">
                Segundos entre balotas
              </label>
              <Input
                id="duracion"
                type="number"
                min={1}
                max={300}
                value={duracion}
                onChange={(e) => setDuracion(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Lo usará el sorteo automático de la balotera.
              </p>
            </div>

            <Button onClick={() => void crear()} disabled={creando}>
              {creando ? 'Creando…' : 'Crear partida'}
            </Button>
          </CardContent>
        </Card>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold">
            Partidas
            {partidas.length > 0 && (
              <span className="ml-2 text-sm font-normal text-muted-foreground tabular">
                {partidas.length}
              </span>
            )}
          </h2>

          {error && (
            <p
              role="alert"
              className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
            >
              {error}
            </p>
          )}

          {cargando ? (
            <p className="text-sm text-muted-foreground">Cargando…</p>
          ) : partidas.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-muted-foreground">
                  Todavía no hay partidas. Crea la primera con el formulario de
                  la izquierda.
                </p>
              </CardContent>
            </Card>
          ) : (
            <ul className="space-y-3">
              {partidas.map((partida) => (
                <li key={partida.id}>
                  <Card>
                    <CardContent className="flex flex-wrap items-center gap-x-6 gap-y-3 p-4">
                      <div className="min-w-24">
                        <p className="text-xs uppercase tracking-wider text-muted-foreground">
                          Juego
                        </p>
                        <p className="text-2xl font-bold tabular text-primary">
                          {partida.numero_consecutivo}
                        </p>
                      </div>

                      <div className="min-w-24">
                        <p className="text-xs uppercase tracking-wider text-muted-foreground">
                          Estado
                        </p>
                        <p className="font-medium">
                          {ETIQUETA_ESTADO[partida.estado]}
                        </p>
                      </div>

                      <div className="min-w-24">
                        <p className="text-xs uppercase tracking-wider text-muted-foreground">
                          Cartón
                        </p>
                        <p className="font-medium tabular">
                          {formatearPesos(partida.precio_carton)}
                        </p>
                      </div>

                      <div className="min-w-24">
                        <p className="text-xs uppercase tracking-wider text-muted-foreground">
                          Formas
                        </p>
                        <p className="font-medium tabular">
                          {partida.total_formas}
                        </p>
                      </div>

                      <div className="min-w-32">
                        <p className="text-xs uppercase tracking-wider text-muted-foreground">
                          Premios
                        </p>
                        <p className="font-medium tabular text-success">
                          {formatearPesos(partida.premio_total)}
                        </p>
                      </div>

                      <div className="ml-auto flex gap-1.5">
                        {porEliminar === partida.id ? (
                          <>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => void confirmarEliminar(partida.id)}
                            >
                              Sí, eliminar
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setPorEliminar(null)}
                            >
                              No
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button asChild size="sm">
                              <Link to={`/admin/partidas/${partida.id}`}>
                                Configurar formas
                              </Link>
                            </Button>
                            <Button asChild size="sm" variant="outline">
                              <Link to={`/admin/partidas/${partida.id}/cartones`}>
                                Cartones
                              </Link>
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setPorEliminar(partida.id)}
                            >
                              Eliminar
                            </Button>
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
