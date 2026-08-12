import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { CuadriculaFigura } from '@/components/figuras/CuadriculaFigura'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { TIPOS_FIGURA, listarFiguras, type Figura } from '@/lib/figuras'
import {
  definirFormas,
  formatearPesos,
  obtenerPartida,
  type FormaAElegir,
  type Partida,
} from '@/lib/partidas'

/** Una forma en el editor: la figura completa, para poder dibujarla. */
interface FormaEnEdicion {
  figura: Pick<Figura, 'id' | 'nombre' | 'patron' | 'tipo'>
  valor_premio: number
}

/**
 * Selección de formas de ganar de una partida — tarea #2 de la Fase 1.
 *
 * Equivale a la pantalla "Configurar/Editar Juego" de la app anterior. Cada una
 * de las tres categorías ofrece **solo las figuras que el administrador
 * clasificó ahí** en el catálogo (`/admin/figuras`), y a cada forma elegida se
 * le fija su propio premio.
 *
 * Las categorías son solo organizativas: cómo se gana lo define el patrón de
 * cada figura. Tampoco son etapas — todas las formas juegan al mismo tiempo —,
 * así que no hay orden de juego que configurar, ni tiene sentido sumar los
 * premios por categoría: son independientes entre sí.
 */
export function ConfigurarPartida() {
  const { id } = useParams<{ id: string }>()
  const partidaId = Number(id)

  const [partida, setPartida] = useState<Partida | null>(null)
  const [catalogo, setCatalogo] = useState<Figura[]>([])
  const [seleccion, setSeleccion] = useState<FormaEnEdicion[]>([])
  const [sinGuardar, setSinGuardar] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)

  const cargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const [datosPartida, figuras] = await Promise.all([
        obtenerPartida(partidaId),
        listarFiguras(),
      ])
      setPartida(datosPartida)
      setCatalogo(figuras)
      setSeleccion(
        datosPartida.figuras.map((forma) => ({
          figura: forma.figura,
          valor_premio: forma.valor_premio,
        })),
      )
      setSinGuardar(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar la partida.')
    } finally {
      setCargando(false)
    }
  }, [partidaId])

  useEffect(() => {
    void cargar()
  }, [cargar])

  const cambiar = (nueva: FormaEnEdicion[]) => {
    setSeleccion(nueva)
    setSinGuardar(true)
    setAviso(null)
  }

  const idsElegidos = new Set(seleccion.map((f) => f.figura.id))
  const premioTotal = seleccion.reduce((suma, f) => suma + (f.valor_premio || 0), 0)

  const agregar = (figura: Figura) =>
    cambiar([...seleccion, { figura, valor_premio: 0 }])

  const quitar = (figuraId: number) =>
    cambiar(seleccion.filter((f) => f.figura.id !== figuraId))

  const cambiarPremio = (figuraId: number, valor: number) =>
    cambiar(
      seleccion.map((f) =>
        f.figura.id === figuraId ? { ...f, valor_premio: Math.max(0, valor) } : f,
      ),
    )

  const guardar = async () => {
    setGuardando(true)
    setError(null)
    setAviso(null)
    try {
      const formas: FormaAElegir[] = seleccion.map((f) => ({
        figura_id: f.figura.id,
        valor_premio: f.valor_premio || 0,
      }))
      const actualizada = await definirFormas(partidaId, formas)
      setPartida(actualizada)
      setSinGuardar(false)
      setAviso('Formas de ganar guardadas.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron guardar las formas.')
    } finally {
      setGuardando(false)
    }
  }

  if (cargando) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  if (!partida) {
    return (
      <div className="space-y-4">
        <p
          role="alert"
          className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error ?? 'No se encontró la partida.'}
        </p>
        <Button asChild variant="outline" size="sm">
          <Link to="/operador/partidas">Volver a partidas</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <Link
          to="/operador/partidas"
          className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          ← Partidas
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">
          Juego{' '}
          <span className="tabular text-primary">
            {partida.numero_consecutivo}
          </span>{' '}
          · Formas de ganar
        </h1>
        <p className="max-w-3xl text-muted-foreground">
          Cada categoría ofrece solo las figuras que clasificaste en ella dentro
          del{' '}
          <Link
            to="/admin/figuras"
            className="text-primary underline-offset-4 hover:underline"
          >
            catálogo
          </Link>
          . Ponle a cada forma su propio premio; todas juegan al mismo tiempo y
          gana quien complete el patrón de cualquiera de ellas.
        </p>
      </header>

      {/* Barra de acciones, fija al hacer scroll: las tres categorías son
          largas y el botón de guardar debe seguir a mano. */}
      <div className="sticky top-16 z-10 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface/90 px-4 py-3 backdrop-blur">
        <div className="flex items-baseline gap-4 text-sm">
          <span className="text-muted-foreground">
            Formas:{' '}
            <span className="font-semibold tabular text-foreground">
              {seleccion.length}
            </span>
          </span>
          <span className="text-muted-foreground">
            Total en premios:{' '}
            <span className="font-semibold tabular text-success">
              {formatearPesos(premioTotal)}
            </span>
          </span>
          {sinGuardar && (
            <span className="text-primary">Hay cambios sin guardar</span>
          )}
          {aviso && !sinGuardar && <span className="text-success">{aviso}</span>}
        </div>

        <Button onClick={() => void guardar()} disabled={guardando}>
          {guardando ? 'Guardando…' : 'Guardar formas'}
        </Button>
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      {catalogo.length === 0 && (
        <p className="rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-muted-foreground">
          El catálogo de figuras está vacío.{' '}
          <Link
            to="/admin/figuras"
            className="text-primary underline-offset-4 hover:underline"
          >
            Crea una figura
          </Link>{' '}
          antes de configurar la partida.
        </p>
      )}

      <div className="grid gap-4 xl:grid-cols-3">
        {TIPOS_FIGURA.map((tipo) => {
          // Cada categoría solo muestra y solo ofrece figuras clasificadas en
          // ella: la clasificación viene del catálogo, no de esta pantalla.
          const formas = seleccion.filter((f) => f.figura.tipo === tipo.valor)
          const disponibles = catalogo.filter(
            (f) => f.tipo === tipo.valor && !idsElegidos.has(f.id),
          )
          const enCatalogo = catalogo.filter((f) => f.tipo === tipo.valor).length

          return (
            <Card key={tipo.valor} className="flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-baseline justify-between gap-2">
                  <span>{tipo.etiqueta}</span>
                  <span className="text-sm font-normal tabular text-muted-foreground">
                    {formas.length}
                  </span>
                </CardTitle>
                <CardDescription>
                  {enCatalogo === 0
                    ? 'No hay figuras clasificadas en esta categoría.'
                    : `${formas.length} de ${enCatalogo} en juego.`}
                </CardDescription>
              </CardHeader>

              <CardContent className="flex flex-1 flex-col gap-2">
                {formas.map((forma) => (
                  <div
                    key={forma.figura.id}
                    className="flex items-center gap-3 rounded-md border border-border bg-surface-2 p-2.5"
                  >
                    <CuadriculaFigura
                      patron={forma.figura.patron}
                      tamano="mini"
                      etiqueta={`Patrón de ${forma.figura.nombre}`}
                    />

                    <div className="min-w-0 flex-1 space-y-1">
                      <p
                        className="truncate text-sm font-semibold"
                        title={forma.figura.nombre}
                      >
                        {forma.figura.nombre}
                      </p>
                      <Input
                        // type="text" y no "number": el campo se escribe a
                        // mano, sin flechas de incremento ni rueda del ratón.
                        type="text"
                        inputMode="numeric"
                        value={forma.valor_premio === 0 ? '' : forma.valor_premio}
                        placeholder="Premio"
                        aria-label={`Premio de ${forma.figura.nombre}`}
                        onChange={(e) =>
                          cambiarPremio(
                            forma.figura.id,
                            // Solo dígitos: evita comas, puntos y signos que
                            // luego habría que interpretar.
                            Number(e.target.value.replace(/\D/g, '')) || 0,
                          )
                        }
                        className="h-8 tabular"
                      />
                      {forma.valor_premio > 0 && (
                        <p className="text-xs tabular text-success">
                          {formatearPesos(forma.valor_premio)}
                        </p>
                      )}
                    </div>

                    <Button
                      size="sm"
                      variant="ghost"
                      aria-label={`Quitar ${forma.figura.nombre}`}
                      onClick={() => quitar(forma.figura.id)}
                    >
                      Quitar
                    </Button>
                  </div>
                ))}

                <select
                  value=""
                  disabled={disponibles.length === 0}
                  aria-label={`Agregar una figura a ${tipo.etiqueta}`}
                  onChange={(e) => {
                    const figura = catalogo.find(
                      (f) => f.id === Number(e.target.value),
                    )
                    if (figura) agregar(figura)
                  }}
                  className="mt-auto h-9 w-full rounded-md border border-dashed border-border bg-transparent px-2 text-sm text-muted-foreground transition-colors hover:border-primary/60 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                >
                  <option value="">
                    {enCatalogo === 0
                      ? 'Sin figuras en esta categoría'
                      : disponibles.length === 0
                        ? 'Todas ya están en juego'
                        : `+ Agregar a ${tipo.etiqueta}`}
                  </option>
                  {disponibles.map((figura) => (
                    <option key={figura.id} value={figura.id}>
                      {figura.nombre}
                    </option>
                  ))}
                </select>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
