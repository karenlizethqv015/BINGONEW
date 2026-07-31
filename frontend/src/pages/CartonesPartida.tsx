import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { CartonBingo } from '@/components/cartones/CartonBingo'
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
  MAXIMO_POR_PETICION,
  eliminarCartones,
  generarCartones,
  listarCartones,
  resumenCartones,
  type Carton,
  type ResumenCartones,
} from '@/lib/cartones'
import { obtenerPartida, type Partida } from '@/lib/partidas'

/** Cuántos cartones se muestran por página. */
const POR_PAGINA = 24

/**
 * Cartones virtuales de una partida — tarea #3 de la Fase 1.
 *
 * Los cartones se generan en el backend con un generador criptográficamente
 * seguro y son únicos dentro de la partida. Aquí solo se piden y se muestran:
 * ninguna regla del bingo se reimplementa en el frontend.
 */
export function CartonesPartida() {
  const { id } = useParams<{ id: string }>()
  const partidaId = Number(id)

  const [partida, setPartida] = useState<Partida | null>(null)
  const [cartones, setCartones] = useState<Carton[]>([])
  const [resumen, setResumen] = useState<ResumenCartones | null>(null)
  const [pagina, setPagina] = useState(0)
  const [cantidad, setCantidad] = useState('24')
  const [serie, setSerie] = useState('A')
  const [confirmandoBorrado, setConfirmandoBorrado] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)
  const [generando, setGenerando] = useState(false)

  const cargar = useCallback(
    async (paginaPedida: number) => {
      setCargando(true)
      setError(null)
      try {
        const [datosPartida, datosResumen, lista] = await Promise.all([
          obtenerPartida(partidaId),
          resumenCartones(partidaId),
          listarCartones(partidaId, {
            limite: POR_PAGINA,
            desplazamiento: paginaPedida * POR_PAGINA,
          }),
        ])
        setPartida(datosPartida)
        setResumen(datosResumen)
        setCartones(lista)
        setPagina(paginaPedida)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'No se pudieron cargar los cartones.')
      } finally {
        setCargando(false)
      }
    },
    [partidaId],
  )

  useEffect(() => {
    void cargar(0)
  }, [cargar])

  const generar = async () => {
    setGenerando(true)
    setError(null)
    try {
      await generarCartones(partidaId, {
        cantidad: Number(cantidad) || 1,
        serie: serie.trim() || 'A',
      })
      // Se recarga desde el backend en lugar de agregar a la lista local: así
      // el resumen y la paginación quedan consistentes con lo que hay guardado.
      await cargar(0)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron generar los cartones.')
    } finally {
      setGenerando(false)
    }
  }

  const borrarTodos = async () => {
    setError(null)
    try {
      await eliminarCartones(partidaId)
      await cargar(0)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron eliminar los cartones.')
    } finally {
      setConfirmandoBorrado(false)
    }
  }

  const total = resumen?.total ?? 0
  const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA))

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <Link
          to="/admin/partidas"
          className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          ← Partidas
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">
          {partida ? (
            <>
              Juego{' '}
              <span className="tabular text-primary">
                {partida.numero_consecutivo}
              </span>{' '}
              · Cartones
            </>
          ) : (
            'Cartones'
          )}
        </h1>
        <p className="max-w-3xl text-muted-foreground">
          Cada cartón se genera con números al azar respetando los rangos por
          letra (B 1–15, I 16–30, N 31–45, G 46–60, O 61–75), con la casilla
          libre en el centro. No se repiten dentro de la misma partida.
        </p>
      </header>

      {error && (
        <p
          role="alert"
          className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,20rem)_1fr] lg:items-start">
        <Card className="lg:sticky lg:top-20">
          <CardHeader>
            <CardTitle>Generar cartones</CardTitle>
            <CardDescription>
              Se agregan a los que ya existen; la numeración continúa.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="cantidad" className="text-sm font-medium">
                Cantidad
              </label>
              <Input
                id="cantidad"
                type="number"
                min={1}
                max={MAXIMO_POR_PETICION}
                value={cantidad}
                onChange={(e) => setCantidad(e.target.value)}
                className="tabular"
              />
              <p className="text-xs text-muted-foreground">
                Máximo {MAXIMO_POR_PETICION} por vez.
              </p>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="serie" className="text-sm font-medium">
                Serie
              </label>
              <Input
                id="serie"
                value={serie}
                maxLength={8}
                onChange={(e) => setSerie(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Cada serie lleva su propia numeración.
              </p>
            </div>

            <Button onClick={() => void generar()} disabled={generando}>
              {generando ? 'Generando…' : 'Generar'}
            </Button>

            {total > 0 && (
              <div className="space-y-2 border-t border-border pt-4">
                <p className="text-sm">
                  <span className="font-semibold tabular text-primary">
                    {total}
                  </span>{' '}
                  {total === 1 ? 'cartón' : 'cartones'} en la partida
                </p>
                {resumen && Object.keys(resumen.por_serie).length > 1 && (
                  <ul className="space-y-0.5 text-xs text-muted-foreground">
                    {Object.entries(resumen.por_serie).map(([nombre, cuantos]) => (
                      <li key={nombre} className="tabular">
                        Serie {nombre}: {cuantos}
                      </li>
                    ))}
                  </ul>
                )}

                {confirmandoBorrado ? (
                  <div className="space-y-2">
                    <p className="text-xs text-muted-foreground">
                      ¿Eliminar los {total} cartones de la partida?
                    </p>
                    <div className="flex gap-1.5">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => void borrarTodos()}
                      >
                        Sí, eliminar
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setConfirmandoBorrado(false)}
                      >
                        No
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setConfirmandoBorrado(true)}
                  >
                    Eliminar todos
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <section className="space-y-4">
          {cargando ? (
            <p className="text-sm text-muted-foreground">Cargando…</p>
          ) : cartones.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-muted-foreground">
                  Todavía no hay cartones. Genera los primeros con el formulario
                  de la izquierda.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
                {cartones.map((carton) => (
                  <li key={carton.id}>
                    <CartonBingo
                      numeros={carton.numeros}
                      etiqueta={`${carton.serie}-${carton.numero_carton}`}
                    />
                  </li>
                ))}
              </ul>

              {totalPaginas > 1 && (
                <div className="flex items-center justify-center gap-3">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={pagina === 0}
                    onClick={() => void cargar(pagina - 1)}
                  >
                    Anterior
                  </Button>
                  <span className="text-sm tabular text-muted-foreground">
                    {pagina + 1} / {totalPaginas}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={pagina + 1 >= totalPaginas}
                    onClick={() => void cargar(pagina + 1)}
                  >
                    Siguiente
                  </Button>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  )
}
