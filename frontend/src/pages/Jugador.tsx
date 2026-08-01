import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Bola } from '@/components/balotera/Bola'
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
import { usePartidaEnVivo } from '@/hooks/usePartidaEnVivo'
import { contarMarcadas } from '@/lib/bingo'
import {
  codigoDeCarton,
  listarCartones,
  obtenerCartonPorCodigo,
  partirCodigo,
  type Carton,
} from '@/lib/cartones'
import { ETIQUETA_ESTADO, listarPartidas, type Partida } from '@/lib/partidas'
import { cn } from '@/lib/utils'

/** Cuántos códigos se ofrecen para elegir a dedo. */
const CODIGOS_A_MOSTRAR = 40

const ALMACEN = 'bingo:jugador'

interface Guardado {
  partidaId: number
  codigos: string[]
}

function leerGuardado(): Guardado | null {
  try {
    const crudo = localStorage.getItem(ALMACEN)
    return crudo ? (JSON.parse(crudo) as Guardado) : null
  } catch {
    return null
  }
}

/**
 * Vista del jugador — tarea #5 de la Fase 1.
 *
 * Muestra el/los cartón(es) del jugador marcándose solos a medida que se cantan
 * las balotas. Todo llega por el mismo WebSocket de la partida que alimenta a la
 * balotera: esta pantalla no consulta al servidor en cada balota.
 *
 * **Diseñada para celular**, a diferencia del resto del proyecto: es la única
 * vista que se usa desde el teléfono (docs/05-requisitos-no-funcionales.md).
 *
 * En la Fase 1 no hay login: se entra por el código del cartón o por un enlace
 * directo. El login por cédula es de la Fase 2.
 *
 * El aviso de bingo no está aquí: depende de la validación de ganadores, que es
 * la tarea #8.
 */
export function Jugador() {
  const [parametros, setParametros] = useSearchParams()

  /**
   * Lo que traía la URL **al entrar**, capturado una sola vez.
   *
   * Los parámetros son el enlace que le mandaron al jugador; a partir de ahí
   * manda lo que él elija en pantalla. Reaccionar a `parametros` en un efecto
   * que también los escribe crea un bucle: agregar un cartón cambiaba la URL,
   * eso reejecutaba la carga, y la carga vaciaba la selección recién hecha.
   */
  const alEntrar = useRef({
    partida: parametros.get('partida'),
    carton: parametros.get('carton'),
  }).current

  const [partidas, setPartidas] = useState<Partida[]>([])
  const [partidaId, setPartidaId] = useState<number | null>(null)
  const [misCartones, setMisCartones] = useState<Carton[]>([])
  const [disponibles, setDisponibles] = useState<Carton[]>([])
  const [codigo, setCodigo] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)

  const vivo = usePartidaEnVivo(partidaId ?? Number.NaN)

  // --- Elegir la partida ----------------------------------------------------

  useEffect(() => {
    let vigente = true

    const arrancar = async () => {
      try {
        const lista = await listarPartidas()
        if (!vigente) return
        setPartidas(lista)

        const guardado = leerGuardado()
        const enUrl = Number(alEntrar.partida)

        // Prioridad: la URL (un enlace que le mandaron), lo último que usó, y
        // si no, la partida más reciente que siga viva.
        const elegida =
          (Number.isFinite(enUrl) && lista.some((p) => p.id === enUrl)
            ? enUrl
            : null) ??
          (guardado && lista.some((p) => p.id === guardado.partidaId)
            ? guardado.partidaId
            : null) ??
          lista.find((p) => p.estado !== 'finalizada')?.id ??
          lista[0]?.id ??
          null

        setPartidaId(elegida)
      } catch (e) {
        if (vigente) {
          setError(
            e instanceof Error ? e.message : 'No se pudieron cargar las partidas.',
          )
        }
      } finally {
        if (vigente) setCargando(false)
      }
    }

    void arrancar()
    return () => {
      vigente = false
    }
    // Solo al montar: después la partida la cambia el jugador a mano.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // --- Cargar los cartones de la partida elegida ----------------------------

  const agregarPorCodigo = useCallback(
    async (texto: string, silencioso = false) => {
      if (partidaId === null) return

      const partido = partirCodigo(texto)
      if (!partido) {
        if (!silencioso) setError(`«${texto}» no parece un código de cartón.`)
        return
      }

      try {
        const carton = await obtenerCartonPorCodigo(
          partidaId,
          partido.serie,
          partido.numero,
        )
        setMisCartones((previos) =>
          previos.some((c) => c.id === carton.id) ? previos : [...previos, carton],
        )
        setCodigo('')
        setError(null)
      } catch (e) {
        if (!silencioso) {
          setError(e instanceof Error ? e.message : 'No se encontró el cartón.')
        }
      }
    },
    [partidaId],
  )

  useEffect(() => {
    if (partidaId === null) return

    let vigente = true
    setMisCartones([])

    const cargar = async () => {
      try {
        const lista = await listarCartones(partidaId, {
          limite: CODIGOS_A_MOSTRAR,
        })
        if (vigente) setDisponibles(lista)
      } catch {
        if (vigente) setDisponibles([])
      }

      // Restaura los cartones del enlace o de la última visita. Se usa lo que
      // traía la URL al entrar, no lo que tenga ahora: lo de ahora lo escribe
      // esta misma pantalla.
      const guardado = leerGuardado()
      const codigos = alEntrar.carton
        ? alEntrar.carton.split(',')
        : guardado?.partidaId === partidaId
          ? guardado.codigos
          : []

      for (const uno of codigos) {
        if (!vigente) return
        await agregarPorCodigo(uno, true)
      }
    }

    void cargar()
    return () => {
      vigente = false
    }
    // Sin `parametros` en las dependencias: solo se recarga al cambiar de
    // partida. Es lo único que debe vaciar la selección de cartones.
  }, [partidaId, agregarPorCodigo, alEntrar])

  // Recuerda la selección: si se bloquea la pantalla del celular o se recarga,
  // el jugador no pierde su cartón a mitad de partida.
  useEffect(() => {
    if (partidaId === null) return

    const codigos = misCartones.map(codigoDeCarton)
    localStorage.setItem(ALMACEN, JSON.stringify({ partidaId, codigos }))

    const nuevos = new URLSearchParams(parametros)
    nuevos.set('partida', String(partidaId))
    if (codigos.length) nuevos.set('carton', codigos.join(','))
    else nuevos.delete('carton')
    setParametros(nuevos, { replace: true })
    // `parametros` fuera de las dependencias a propósito: se escribe aquí, y
    // volver a reaccionar a él provocaría un bucle.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [misCartones, partidaId])

  const quitar = (id: number) =>
    setMisCartones((previos) => previos.filter((c) => c.id !== id))

  const yaElegidos = new Set(misCartones.map((c) => c.id))
  const paraElegir = disponibles.filter((c) => !yaElegidos.has(c.id))

  if (cargando) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  if (partidaId === null) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">
            Todavía no hay ninguna partida creada.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-5">
      {/* Cabecera fija: la última balota debe verse siempre, aunque el jugador
          esté desplazándose por sus cartones. */}
      <div className="sticky top-16 z-10 -mx-2 rounded-lg border border-border bg-surface/95 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-4">
          {vivo.ultima ? (
            <Bola
              key={vivo.ultima.numero}
              balota={vivo.ultima}
              tamano="normal"
              destacada
              className="animate-balota shrink-0"
            />
          ) : (
            <div className="grid size-16 shrink-0 place-items-center rounded-full border-2 border-dashed border-border text-[10px] text-muted-foreground">
              Sin balotas
            </div>
          )}

          <div className="min-w-0 flex-1 space-y-1">
            <p className="flex items-center gap-2 text-sm">
              <span
                className={cn(
                  'size-2 shrink-0 rounded-full',
                  vivo.conexion === 'conectado'
                    ? 'bg-success'
                    : vivo.conexion === 'conectando'
                      ? 'bg-primary'
                      : 'bg-destructive',
                )}
                aria-hidden
              />
              <span className="truncate text-muted-foreground">
                Juego{' '}
                <span className="font-semibold tabular text-foreground">
                  {vivo.numeroConsecutivo ?? '—'}
                </span>
                {vivo.estado && ` · ${ETIQUETA_ESTADO[vivo.estado]}`}
              </span>
            </p>
            <p className="text-xs text-muted-foreground tabular">
              {vivo.totalCantadas} de 75 balotas
            </p>
          </div>
        </div>

        {/* Últimas balotas, para el que se distrajo un momento. */}
        {vivo.balotas.length > 1 && (
          <div className="mt-3 flex gap-1.5 overflow-x-auto pb-1">
            {[...vivo.balotas]
              .slice(-6, -1)
              .reverse()
              .map((balota) => (
                <Bola
                  key={balota.numero}
                  balota={balota}
                  tamano="mini"
                  className="shrink-0"
                />
              ))}
          </div>
        )}
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      {/* Mis cartones */}
      {misCartones.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {misCartones.map((carton) => {
            const marcadas = contarMarcadas(carton.numeros, vivo.cantadas)

            return (
              <div key={carton.id} className="space-y-1.5">
                <CartonBingo
                  numeros={carton.numeros}
                  etiqueta={codigoDeCarton(carton)}
                  marcados={vivo.cantadas}
                  ultimo={vivo.ultima?.numero ?? null}
                />
                <div className="flex items-center justify-between px-1 text-xs">
                  <span className="tabular text-muted-foreground">
                    {marcadas} de 25 marcadas
                  </span>
                  <button
                    type="button"
                    onClick={() => quitar(carton.id)}
                    className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
                  >
                    Quitar
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground">
              Elige tu cartón para empezar a jugar.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Elegir cartón */}
      <Card>
        <CardHeader>
          <CardTitle>Agregar un cartón</CardTitle>
          <CardDescription>
            Escribe su número o elígelo de la lista. Puedes jugar con varios.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="Ej. A-7"
              aria-label="Número de cartón"
              onKeyDown={(e) => {
                if (e.key === 'Enter') void agregarPorCodigo(codigo)
              }}
            />
            <Button
              onClick={() => void agregarPorCodigo(codigo)}
              disabled={!codigo.trim()}
            >
              Agregar
            </Button>
          </div>

          {paraElegir.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {paraElegir.map((carton) => (
                <button
                  key={carton.id}
                  type="button"
                  onClick={() => void agregarPorCodigo(codigoDeCarton(carton), true)}
                  className="rounded-md border border-border bg-surface-2 px-2.5 py-1 text-xs font-medium tabular transition-colors hover:border-primary/60 hover:text-primary"
                >
                  {codigoDeCarton(carton)}
                </button>
              ))}
            </div>
          )}

          {disponibles.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Esta partida todavía no tiene cartones generados.
            </p>
          )}

          {partidas.length > 1 && (
            <div className="space-y-1.5 border-t border-border pt-4">
              <label htmlFor="partida" className="text-sm font-medium">
                Partida
              </label>
              <select
                id="partida"
                value={partidaId}
                onChange={(e) => setPartidaId(Number(e.target.value))}
                className="h-10 w-full rounded-md border border-input bg-surface-2 px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {partidas.map((partida) => (
                  <option key={partida.id} value={partida.id}>
                    Juego {partida.numero_consecutivo} ·{' '}
                    {ETIQUETA_ESTADO[partida.estado]}
                  </option>
                ))}
              </select>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
