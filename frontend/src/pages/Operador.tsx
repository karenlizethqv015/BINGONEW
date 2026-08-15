import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Cronometro } from '@/components/balotera/Cronometro'
import { Bola } from '@/components/balotera/Bola'
import { EstadoDelBackend } from '@/components/EstadoDelBackend'
import { AvisoBingo } from '@/components/ganadores/AvisoBingo'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { usePartidaEnVivo } from '@/hooks/usePartidaEnVivo'
import { useRelojDeJugada } from '@/hooks/useRelojDeJugada'
import { cambiarEstado } from '@/lib/balotas'
import { TOTAL_BALOTAS } from '@/lib/bingo'
import { resumenCartones } from '@/lib/cartones'
import { textoCartones } from '@/lib/ganadores'
import {
  cambiarVenta,
  ETIQUETA_ESTADO,
  formatearPesos,
  listarPartidas,
  obtenerPartida,
  type Partida,
} from '@/lib/partidas'
import { cn } from '@/lib/utils'

/**
 * Panel de operación de la partida — antes vivía en `/admin` (tarea #7 de la
 * Fase 1), ahora es del rol operador: partidas, balotera y cartones son suyos.
 * El administrador se quedó con el catálogo de figuras (`/admin`).
 *
 * Es la vista de mando: en qué va la partida ahora mismo, cuánto se recaudó,
 * qué premios quedan por repartir y quién ha ganado. Se alimenta del mismo
 * WebSocket que la balotera y el tablero de la sala, así que las tres pantallas
 * no pueden discrepar.
 *
 * El control balota a balota vive en la balotera
 * (`/operador/partidas/{id}/balotera`) y no se duplica aquí: tener dos sitios
 * donde cantar sería tener dos relojes de sorteo automático corriendo a la vez.
 */
export function Operador() {
  const [partidas, setPartidas] = useState<Partida[]>([])
  const [partidaId, setPartidaId] = useState<number | null>(null)
  const [partida, setPartida] = useState<Partida | null>(null)
  const [cartones, setCartones] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [bingoSinAtender, setBingoSinAtender] = useState(false)

  const vivo = usePartidaEnVivo(partidaId ?? Number.NaN)
  const reloj = useRelojDeJugada(vivo.iniciadaEn)

  // --- Elegir la partida que se está administrando --------------------------

  useEffect(() => {
    let vigente = true

    void (async () => {
      try {
        const lista = await listarPartidas()
        if (!vigente) return
        setPartidas(lista)
        // La que está viva; si no hay ninguna, la más reciente.
        setPartidaId(
          lista.find((p) => p.estado !== 'finalizada')?.id ?? lista[0]?.id ?? null,
        )
      } catch (e) {
        if (vigente) {
          setError(
            e instanceof Error
              ? e.message
              : 'No se pudo contactar el backend. ¿Está corriendo uvicorn?',
          )
        }
      } finally {
        if (vigente) setCargando(false)
      }
    })()

    return () => {
      vigente = false
    }
  }, [])

  // Los premios y los cartones no viajan por el WebSocket. Se releen al cambiar
  // el estado, que es cuando pueden haber cambiado.
  const estado = vivo.estado
  const recargar = useCallback(async () => {
    if (partidaId === null) return
    try {
      const [datos, resumen] = await Promise.all([
        obtenerPartida(partidaId),
        resumenCartones(partidaId),
      ])
      setPartida(datos)
      setCartones(resumen.total)
    } catch {
      // Se conserva lo que ya había: mejor un dato de hace un momento que un
      // panel en blanco.
    }
  }, [partidaId])

  useEffect(() => {
    void recargar()
  }, [recargar, estado])

  // Un bingo recién detectado pide atención; uno que ya estaba, no.
  const ganadores = vivo.ganadores
  useEffect(() => {
    if (ganadores.bingos.some((b) => b.nuevo)) setBingoSinAtender(true)
    else if (ganadores.bingos.length === 0) setBingoSinAtender(false)
  }, [ganadores])

  const alternarVenta = async () => {
    if (partidaId === null || vivo.ventaAbierta === null) return
    setOcupado(true)
    setError(null)
    try {
      await cambiarVenta(partidaId, !vivo.ventaAbierta)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cambiar la venta.')
    } finally {
      setOcupado(false)
    }
  }

  const transicion = async (
    accion: 'iniciar' | 'pausar' | 'reanudar' | 'finalizar',
  ) => {
    if (partidaId === null) return
    setOcupado(true)
    setError(null)
    try {
      await cambiarEstado(partidaId, accion)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cambiar el estado.')
    } finally {
      setOcupado(false)
    }
  }

  if (cargando) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  const enCurso = vivo.estado === 'en_curso'
  const premioTotal = partida?.premio_total ?? 0
  const premioGanado = ganadores.bingos.reduce(
    (suma, bingo) => suma + bingo.valor_premio,
    0,
  )
  const recaudo = cartones * (partida?.precio_carton ?? 0)

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Operación</h1>
          <p className="text-muted-foreground">
            {partida
              ? `Juego No. ${partida.numero_consecutivo} · ${
                  vivo.estado ? ETIQUETA_ESTADO[vivo.estado] : '—'
                }`
              : 'Todavía no hay ninguna partida creada.'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {partidas.length > 1 && (
            <label className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Partida</span>
              <select
                value={partidaId ?? ''}
                onChange={(e) => setPartidaId(Number(e.target.value))}
                className="rounded-md border border-input bg-surface px-2.5 py-1.5 text-sm"
              >
                {partidas.map((p) => (
                  <option key={p.id} value={p.id}>
                    Juego {p.numero_consecutivo} · {ETIQUETA_ESTADO[p.estado]}
                  </option>
                ))}
              </select>
            </label>
          )}

          {/* Siempre visible, no solo cuando no hay ninguna partida: es el
              punto de entrada a crear, ver o borrar partidas, y quedaba
              enterrado como un enlace de texto suelto al fondo del panel. */}
          <Button asChild size="sm" variant="outline">
            <Link to="/operador/partidas">Gestionar partidas</Link>
          </Button>
        </div>
      </header>

      {error && (
        <p
          role="alert"
          className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      {partidaId === null ? (
        <Card className="max-w-xl">
          <CardHeader>
            <CardTitle>Empieza por aquí</CardTitle>
            <CardDescription>
              Crea una partida, elige sus formas de ganar y genera los cartones.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button asChild size="sm">
              <Link to="/operador/partidas">Crear una partida</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link to="/admin/figuras">Abrir el catálogo de figuras</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <AvisoBingo
            bingos={ganadores.bingos}
            totalCartones={ganadores.total_cartones_ganadores}
            sinAtender={bingoSinAtender}
            onCerrar={() => setBingoSinAtender(false)}
            onReanudar={
              vivo.estado === 'pausada'
                ? () => void transicion('reanudar')
                : undefined
            }
          />

          {/* Cifras de un vistazo */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Dato
              etiqueta="Reloj de la jugada"
              valor={reloj ?? '—'}
              detalle={
                vivo.iniciadaEn ? 'desde que empezó' : 'la partida no ha empezado'
              }
              acento={enCurso}
            />
            <Dato
              etiqueta="Balotas"
              valor={`${vivo.totalCantadas}`}
              detalle={`de ${TOTAL_BALOTAS} · quedan ${vivo.restantes}`}
            />
            <Dato
              etiqueta="Recaudo"
              valor={formatearPesos(recaudo)}
              detalle={`${cartones} cartones a ${formatearPesos(partida?.precio_carton ?? 0)}`}
            />
            <Dato
              etiqueta="Premios por repartir"
              valor={formatearPesos(premioTotal - premioGanado)}
              detalle={
                premioGanado > 0
                  ? `${formatearPesos(premioGanado)} ya ganados`
                  : `${formatearPesos(premioTotal)} en juego`
              }
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-[minmax(0,24rem)_1fr] lg:items-start">
            {/* Control */}
            <Card>
              <CardHeader>
                <CardTitle>Control de la partida</CardTitle>
                <CardDescription>
                  Cantar balota a balota se hace en la balotera.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {vivo.estado === 'pendiente' && (
                    <Button onClick={() => void transicion('iniciar')} disabled={ocupado}>
                      Iniciar sorteo
                    </Button>
                  )}
                  {enCurso && (
                    <Button
                      variant="secondary"
                      onClick={() => void transicion('pausar')}
                      disabled={ocupado}
                    >
                      Pausar
                    </Button>
                  )}
                  {vivo.estado === 'pausada' && (
                    <Button onClick={() => void transicion('reanudar')} disabled={ocupado}>
                      Reanudar
                    </Button>
                  )}
                  {(enCurso || vivo.estado === 'pausada') && (
                    <Button
                      variant="outline"
                      onClick={() => void transicion('finalizar')}
                      disabled={ocupado}
                    >
                      Finalizar
                    </Button>
                  )}
                </div>

                {/* El «bombillo»: independiente del estado del sorteo, lo lee
                    /transmision del mismo canal en tiempo real. */}
                <button
                  type="button"
                  onClick={() => void alternarVenta()}
                  disabled={ocupado || vivo.ventaAbierta === null}
                  className="flex items-center gap-2 rounded-md border border-border bg-surface-2/50 px-3 py-2 text-sm transition-colors hover:bg-surface-2 disabled:opacity-60"
                >
                  <span
                    className={cn(
                      'size-2.5 rounded-full',
                      vivo.ventaAbierta ? 'bg-success' : 'bg-destructive',
                    )}
                    aria-hidden
                  />
                  <span>
                    Venta de cartones:{' '}
                    <span className="font-medium">
                      {vivo.ventaAbierta ? 'abierta' : 'cerrada'}
                    </span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    (clic para {vivo.ventaAbierta ? 'cerrarla' : 'abrirla'})
                  </span>
                </button>

                {vivo.duracionEntreBalotas !== null && (
                  <div className="border-t border-border pt-4">
                    <Cronometro
                      partidaId={partidaId}
                      segundos={vivo.duracionEntreBalotas}
                    />
                  </div>
                )}

                <div className="flex flex-wrap gap-2 border-t border-border pt-4">
                  <Button asChild size="sm" variant="success">
                    <Link to={`/operador/partidas/${partidaId}/balotera`}>
                      Ir a la balotera
                    </Link>
                  </Button>
                  <Button asChild size="sm" variant="outline">
                    <a
                      href={`/transmision?partida=${partidaId}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Tablero de sala ↗
                    </a>
                  </Button>
                </div>

                <div className="flex flex-wrap gap-x-4 gap-y-1 border-t border-border pt-4 text-sm">
                  <Link
                    to={`/operador/partidas/${partidaId}`}
                    className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
                  >
                    Formas de ganar
                  </Link>
                  <Link
                    to={`/operador/partidas/${partidaId}/cartones`}
                    className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
                  >
                    Cartones
                  </Link>
                  <Link
                    to="/admin/figuras"
                    className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
                  >
                    Catálogo
                  </Link>
                </div>
              </CardContent>
            </Card>

            <div className="space-y-6">
              {/* Últimas balotas */}
              <Card>
                <CardHeader>
                  <CardTitle>Últimas balotas</CardTitle>
                </CardHeader>
                <CardContent>
                  {vivo.balotas.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      Todavía no ha salido ninguna.
                    </p>
                  ) : (
                    <div className="flex flex-wrap items-center gap-2">
                      {[...vivo.balotas]
                        .slice(-8)
                        .reverse()
                        .map((balota, indice) => (
                          <Bola
                            key={balota.numero}
                            balota={balota}
                            tamano={indice === 0 ? 'normal' : 'mini'}
                            destacada={indice === 0}
                            className={indice === 0 ? 'animate-balota' : undefined}
                          />
                        ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Formas y ganadores */}
              <Card>
                <CardHeader>
                  <CardTitle>Formas de ganar</CardTitle>
                  <CardDescription>
                    Todas juegan a la vez. Una forma ganada deja de estar en juego.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {!partida || partida.figuras.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      Esta partida todavía no tiene formas configuradas.{' '}
                      <Link
                        to={`/operador/partidas/${partidaId}`}
                        className="text-primary underline-offset-4 hover:underline"
                      >
                        Configurarlas
                      </Link>
                      .
                    </p>
                  ) : (
                    <ul className="divide-y divide-border">
                      {partida.figuras.map((forma) => {
                        const bingo = ganadores.bingos.find(
                          (b) => b.partida_figura_id === forma.id,
                        )

                        return (
                          <li
                            key={forma.id}
                            className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 py-2.5"
                          >
                            <div className="min-w-0">
                              <p className="font-medium">{forma.figura.nombre}</p>
                              {bingo ? (
                                <p className="text-sm text-success">
                                  {textoCartones(bingo.cartones.length)}:{' '}
                                  <span className="font-semibold tabular">
                                    {bingo.cartones.map((c) => c.codigo).join(', ')}
                                  </span>{' '}
                                  <span className="text-muted-foreground">
                                    · balota {bingo.numero_balota}
                                  </span>
                                </p>
                              ) : (
                                <p className="text-sm text-muted-foreground">
                                  En juego
                                </p>
                              )}
                            </div>

                            <span
                              className={cn(
                                'font-bold tabular',
                                bingo ? 'text-success' : 'text-primary',
                              )}
                            >
                              {formatearPesos(forma.valor_premio)}
                            </span>
                          </li>
                        )
                      })}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      )}

      <EstadoDelBackend />
    </div>
  )
}

interface DatoProps {
  etiqueta: string
  valor: string
  detalle: string
  acento?: boolean
}

/** Una cifra grande del panel. */
function Dato({ etiqueta, valor, detalle, acento }: DatoProps) {
  return (
    <div className="rounded-lg border border-border bg-surface px-4 py-3">
      <p className="text-xs uppercase tracking-wider text-muted-foreground">
        {etiqueta}
      </p>
      <p
        className={cn(
          'mt-1 text-2xl font-bold tabular',
          acento ? 'text-success' : 'text-foreground',
        )}
      >
        {valor}
      </p>
      <p className="text-xs text-muted-foreground">{detalle}</p>
    </div>
  )
}
