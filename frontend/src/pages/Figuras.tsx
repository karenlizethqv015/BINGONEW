import { useCallback, useEffect, useState } from 'react'

import { CuadriculaFigura } from '@/components/figuras/CuadriculaFigura'
import { EditorFigura } from '@/components/figuras/EditorFigura'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { eliminarFigura, listarFiguras, type Figura } from '@/lib/figuras'
import { cn } from '@/lib/utils'

/**
 * Catálogo de figuras (formas de ganar) — tarea #1 de la Fase 1.
 *
 * Es un catálogo global, independiente de las partidas: las figuras se diseñan
 * una vez y se reutilizan. Elegir cuáles juegan en cada partida y con qué premio
 * es la tarea #2.
 */
export function Figuras() {
  const [figuras, setFiguras] = useState<Figura[]>([])
  const [editando, setEditando] = useState<Figura | null>(null)
  const [porEliminar, setPorEliminar] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)

  const recargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      setFiguras(await listarFiguras())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar el catálogo.')
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    void recargar()
  }, [recargar])

  const alGuardar = (figura: Figura) => {
    setEditando(null)
    setFiguras((previas) => {
      const existente = previas.some((f) => f.id === figura.id)
      return existente
        ? previas.map((f) => (f.id === figura.id ? figura : f))
        : [figura, ...previas]
    })
  }

  const confirmarEliminar = async (id: number) => {
    setError(null)
    try {
      await eliminarFigura(id)
      setFiguras((previas) => previas.filter((f) => f.id !== id))
      if (editando?.id === id) setEditando(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo eliminar la figura.')
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
        <h1 className="text-3xl font-bold tracking-tight">Formas de ganar</h1>
        <p className="text-muted-foreground">
          Catálogo global de figuras. Se diseñan una vez y se reutilizan en
          cualquier partida.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,22rem)_1fr] lg:items-start">
        <div className="lg:sticky lg:top-20">
          <EditorFigura
            editando={editando}
            onGuardada={alGuardar}
            onCancelar={() => setEditando(null)}
          />
        </div>

        <section className="space-y-3">
          <div className="flex items-baseline justify-between">
            <h2 className="text-lg font-semibold">
              Catálogo
              {figuras.length > 0 && (
                <span className="ml-2 text-sm font-normal text-muted-foreground tabular">
                  {figuras.length}
                </span>
              )}
            </h2>
          </div>

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
          ) : figuras.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-muted-foreground">
                  Todavía no hay figuras. Crea la primera con el editor de la
                  izquierda.
                </p>
              </CardContent>
            </Card>
          ) : (
            <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {figuras.map((figura) => (
                <li key={figura.id}>
                  <Card
                    className={cn(
                      'h-full transition-colors',
                      editando?.id === figura.id && 'border-primary',
                    )}
                  >
                    <CardContent className="flex h-full flex-col gap-3 p-4">
                      <div className="flex items-start gap-3">
                        <CuadriculaFigura
                          patron={figura.patron}
                          tamano="mini"
                          etiqueta={`Patrón de ${figura.nombre}`}
                        />
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-semibold" title={figura.nombre}>
                            {figura.nombre}
                          </p>
                          <p className="text-xs text-muted-foreground tabular">
                            {figura.celdas_marcadas}{' '}
                            {figura.celdas_marcadas === 1 ? 'celda' : 'celdas'}
                          </p>
                        </div>
                      </div>

                      {porEliminar === figura.id ? (
                        <div className="mt-auto space-y-2">
                          <p className="text-xs text-muted-foreground">
                            ¿Eliminar «{figura.nombre}»?
                          </p>
                          <div className="flex gap-1.5">
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => void confirmarEliminar(figura.id)}
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
                          </div>
                        </div>
                      ) : (
                        <div className="mt-auto flex gap-1.5">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setEditando(figura)}
                          >
                            Editar
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setPorEliminar(figura.id)}
                          >
                            Eliminar
                          </Button>
                        </div>
                      )}
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
