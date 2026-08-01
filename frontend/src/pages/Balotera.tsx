import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Bola } from '@/components/balotera/Bola'
import { AvisoBingo } from '@/components/ganadores/AvisoBingo'
import { CercaDeGanar } from '@/components/ganadores/CercaDeGanar'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { usePartidaEnVivo } from '@/hooks/usePartidaEnVivo'
import { LETRAS, RANGOS_POR_COLUMNA, TOTAL_BALOTAS } from '@/lib/bingo'
import { cambiarEstado, cantarBalota, reiniciarSorteo } from '@/lib/balotas'
import { ETIQUETA_ESTADO } from '@/lib/partidas'
import { cn } from '@/lib/utils'

/** Cuántas balotas recientes se muestran como bolas. */
const RECIENTES = 5

/**
 * Control de la balotera virtual — tarea #4 de la Fase 1.
 *
 * Todo el estado que se ve aquí llega por el WebSocket de la partida, el mismo
 * que alimentará al tablero de transmisión y al cartón del jugador. Esta
 * pantalla no calcula nada del bingo: solo pide balotas y muestra lo que llega.
 *
 * El reloj del modo automático vive en esta pestaña (decisión registrada en
 * PROGRESS.md): si se cierra, el sorteo se detiene y se puede reanudar sin
 * perder nada, porque las balotas ya cantadas están guardadas.
 */
export function Balotera() {
  const { id } = useParams<{ id: string }>()
  const partidaId = Number(id)

  const vivo = usePartidaEnVivo(partidaId)
  const [automatico, setAutomatico] = useState(false)
  const [confirmandoReinicio, setConfirmandoReinicio] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  // Hay un bingo recién cantado que el administrador todavía no ha atendido.
  const [bingoSinAtender, setBingoSinAtender] = useState(false)

  // Evita que dos peticiones de balota se encimen si una tarda más que el
  // intervalo del sorteo automático.
  const cantandoRef = useRef(false)

  const enCurso = vivo.estado === 'en_curso'
  const finalizada = vivo.estado === 'finalizada'
  const intervalo = vivo.duracionEntreBalotas ?? 5

  const cantar = useCallback(async () => {
    if (cantandoRef.current) return
    cantandoRef.current = true
    setError(null)
    try {
      await cantarBalota(partidaId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cantar la balota.')
      // Si el backend rechaza, seguir insistiendo en automático solo repetiría
      // el error una y otra vez.
      setAutomatico(false)
    } finally {
      cantandoRef.current = false
    }
  }, [partidaId])

  // Reloj del modo automático.
  useEffect(() => {
    if (!automatico || !enCurso) return

    const temporizador = window.setInterval(() => void cantar(), intervalo * 1000)
    return () => window.clearInterval(temporizador)
  }, [automatico, enCurso, intervalo, cantar])

  // Al terminarse las balotas, la partida se finaliza sola en el backend.
  useEffect(() => {
    if (finalizada) setAutomatico(false)
  }, [finalizada])

  // Un bingo recién detectado pide atención; uno que ya estaba, no. Sin mirar
  // `nuevo`, el aviso volvería a saltar en cada balota posterior.
  const ganadores = vivo.ganadores
  useEffect(() => {
    if (ganadores.bingos.some((bingo) => bingo.nuevo)) {
      setBingoSinAtender(true)
    } else if (ganadores.bingos.length === 0) {
      // Se reinició el sorteo: no queda nada que atender.
      setBingoSinAtender(false)
    }
  }, [ganadores])

  const transicion = async (
    accion: 'iniciar' | 'pausar' | 'reanudar' | 'finalizar',
  ) => {
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

  const reiniciar = async () => {
    setOcupado(true)
    setError(null)
    setAutomatico(false)
    try {
      await reiniciarSorteo(partidaId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo reiniciar el sorteo.')
    } finally {
      setOcupado(false)
      setConfirmandoReinicio(false)
    }
  }

  const recientes = [...vivo.balotas].slice(-RECIENTES).reverse()

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <Link
          to="/admin/partidas"
          className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          ← Partidas
        </Link>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-3xl font-bold tracking-tight">
            Juego{' '}
            <span className="tabular text-primary">
              {vivo.numeroConsecutivo ?? '—'}
            </span>{' '}
            · Balotera
          </h1>

          {/* En otra pestaña: la de la sala se proyecta y esta se queda
              controlando el sorteo. */}
          <Button asChild variant="outline" size="sm">
            <a
              href={`/transmision?partida=${partidaId}`}
              target="_blank"
              rel="noreferrer"
            >
              Abrir tablero de sala ↗
            </a>
          </Button>
        </div>
      </header>

      {/* Lo primero que hay que ver: alguien ganó. */}
      <AvisoBingo
        bingos={ganadores.bingos}
        totalCartones={ganadores.total_cartones_ganadores}
        sinAtender={bingoSinAtender}
        onCerrar={() => setBingoSinAtender(false)}
      />

      {/* Conexión en tiempo real */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg border border-border bg-surface px-4 py-3 text-sm">
        <span className="flex items-center gap-2">
          <span
            className={cn(
              'size-2.5 rounded-full',
              vivo.conexion === 'conectado'
                ? 'bg-success shadow-[0_0_8px] shadow-success'
                : vivo.conexion === 'conectando'
                  ? 'bg-primary'
                  : 'bg-destructive',
            )}
            aria-hidden
          />
          <span className="text-muted-foreground">
            {vivo.conexion === 'conectado'
              ? 'En vivo'
              : vivo.conexion === 'conectando'
                ? 'Conectando…'
                : 'Sin conexión'}
          </span>
        </span>

        <span className="text-muted-foreground">
          Estado:{' '}
          <span className="font-semibold text-foreground">
            {vivo.estado ? ETIQUETA_ESTADO[vivo.estado] : '—'}
          </span>
        </span>

        <span className="text-muted-foreground">
          Cantadas:{' '}
          <span className="font-semibold tabular text-foreground">
            {vivo.totalCantadas}
          </span>
          <span className="tabular"> / {TOTAL_BALOTAS}</span>
        </span>

        <span className="text-muted-foreground">
          Restantes:{' '}
          <span className="font-semibold tabular text-primary">
            {vivo.restantes}
          </span>
        </span>
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,26rem)_1fr] lg:items-start">
        <div className="space-y-4">
          {/* Última balota */}
          <Card>
            <CardHeader>
              <CardTitle>Última balota</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-5 pb-6">
              {vivo.ultima ? (
                <Bola
                  key={vivo.ultima.numero}
                  balota={vivo.ultima}
                  tamano="grande"
                  destacada
                  className="animate-balota"
                />
              ) : (
                <div className="grid size-32 place-items-center rounded-full border-2 border-dashed border-border text-sm text-muted-foreground">
                  Sin balotas
                </div>
              )}

              {recientes.length > 1 && (
                <div className="flex flex-wrap justify-center gap-2">
                  {recientes.slice(1).map((balota) => (
                    <Bola key={balota.numero} balota={balota} tamano="mini" />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Controles */}
          <Card>
            <CardHeader>
              <CardTitle>Control del sorteo</CardTitle>
              <CardDescription>
                {enCurso
                  ? 'El sorteo está en curso.'
                  : finalizada
                    ? 'La partida terminó.'
                    : vivo.estado === 'pausada'
                      ? 'El sorteo está pausado.'
                      : 'La partida no ha empezado.'}
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

              <div className="space-y-3 border-t border-border pt-4">
                <Button
                  size="lg"
                  variant="success"
                  className="w-full"
                  disabled={!enCurso || automatico}
                  onClick={() => void cantar()}
                >
                  Cantar balota
                </Button>

                <label className="flex items-center gap-2.5 text-sm">
                  <input
                    type="checkbox"
                    checked={automatico}
                    disabled={!enCurso}
                    onChange={(e) => setAutomatico(e.target.checked)}
                    className="size-4 accent-[var(--primary)]"
                  />
                  <span className={cn(!enCurso && 'text-muted-foreground')}>
                    Sorteo automático cada{' '}
                    <span className="font-semibold tabular">{intervalo}s</span>
                  </span>
                </label>

                {automatico && (
                  <p className="text-xs text-muted-foreground">
                    El reloj corre en esta pestaña: si la cierras, el sorteo se
                    detiene y puedes reanudarlo desde aquí.
                  </p>
                )}
              </div>

              {vivo.totalCantadas > 0 && (
                <div className="border-t border-border pt-4">
                  {confirmandoReinicio ? (
                    <div className="space-y-2">
                      <p className="text-xs text-muted-foreground">
                        ¿Borrar las {vivo.totalCantadas} balotas cantadas y
                        empezar de cero?
                      </p>
                      <div className="flex gap-1.5">
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => void reiniciar()}
                          disabled={ocupado}
                        >
                          Sí, reiniciar
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setConfirmandoReinicio(false)}
                        >
                          No
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setConfirmandoReinicio(true)}
                    >
                      Reiniciar sorteo
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          <CercaDeGanar
            cerca={ganadores.cerca}
            aUna={ganadores.a_una}
            aDos={ganadores.a_dos}
          />
        </div>

        {/* Tablero de los 75 números */}
        <Card>
          <CardHeader>
            <CardTitle>Tablero</CardTitle>
            <CardDescription>
              El tablero de sala, en grande y para proyectar, es la tarea #6.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-1.5">
              {RANGOS_POR_COLUMNA.map(([desde, hasta], indice) => (
                <div key={LETRAS[indice]} className="flex items-center gap-2">
                  <span className="w-5 text-lg font-bold text-primary">
                    {LETRAS[indice]}
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {Array.from(
                      { length: hasta - desde + 1 },
                      (_, i) => desde + i,
                    ).map((numero) => {
                      const salio = vivo.cantadas.has(numero)
                      const esUltima = vivo.ultima?.numero === numero

                      return (
                        <span
                          key={numero}
                          className={cn(
                            'grid size-8 place-items-center rounded text-sm font-semibold tabular transition-colors',
                            esUltima
                              ? 'bg-success text-success-foreground'
                              : salio
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-surface-2 text-muted-foreground',
                          )}
                        >
                          {numero}
                        </span>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
