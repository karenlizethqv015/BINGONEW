import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Bola } from '@/components/balotera/Bola'
import { CuadriculaFigura } from '@/components/figuras/CuadriculaFigura'
import { usePartidaEnVivo } from '@/hooks/usePartidaEnVivo'
import { LETRAS, RANGOS_POR_COLUMNA, TOTAL_BALOTAS } from '@/lib/bingo'
import { textoCartones } from '@/lib/ganadores'
import {
  ETIQUETA_ESTADO,
  formatearPesos,
  listarPartidas,
  obtenerPartida,
  type Partida,
} from '@/lib/partidas'
import { cn } from '@/lib/utils'

/** Cuántas balotas recientes se muestran como figuritas. */
const RECIENTES = 5

/**
 * Tablero de transmisión — tarea #6 de la Fase 1.
 *
 * Pantalla pública para **proyectar en el televisor de la sala**. Sin login y
 * de solo lectura: se alimenta del mismo WebSocket de la partida que la
 * balotera, así que no hay forma de que muestre algo distinto de lo que ve el
 * administrador.
 *
 * Todo está dimensionado para leerse a varios metros: números grandes, mucho
 * contraste y nada de texto pequeño. Por eso tampoco lleva la barra de
 * navegación de la aplicación (va fuera del `Layout`): en la sala ocupa la
 * pantalla entera.
 *
 * **Lo que aquí NO se muestra:** los avisos de «a una / a dos balotas». Son
 * información de control del administrador; proyectados serían un delator que
 * le quita la gracia al juego. El bingo sí se anuncia, que es la fiesta.
 */
export function Transmision() {
  const [parametros] = useSearchParams()

  // La partida de la URL se lee una sola vez: esta pantalla se deja puesta
  // durante horas y no debe reaccionar a nada que no venga del WebSocket.
  const enUrl = useRef(parametros.get('partida')).current

  const [partida, setPartida] = useState<Partida | null>(null)
  const [partidaId, setPartidaId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)

  const vivo = usePartidaEnVivo(partidaId ?? Number.NaN)

  useEffect(() => {
    let vigente = true

    const arrancar = async () => {
      try {
        const lista = await listarPartidas()
        if (!vigente) return

        const pedida = Number(enUrl)
        const elegida =
          (Number.isFinite(pedida) && lista.some((p) => p.id === pedida)
            ? pedida
            : null) ??
          lista.find((p) => p.estado !== 'finalizada')?.id ??
          lista[0]?.id ??
          null

        setPartidaId(elegida)
        if (elegida !== null) setPartida(await obtenerPartida(elegida))
      } catch (e) {
        if (vigente) {
          setError(
            e instanceof Error ? e.message : 'No se pudo cargar la partida.',
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
  }, [enUrl])

  /**
   * Las formas y sus premios no viajan por el WebSocket, así que se releen al
   * cambiar el estado de la partida.
   *
   * No es un capricho: lo normal es dejar el tablero puesto en el televisor
   * antes de configurar el juego. Sin esto, la lista de premios se quedaría
   * vacía toda la partida. Durante el sorteo el estado casi no cambia, así que
   * son dos o tres peticiones en toda la jornada.
   */
  const estado = vivo.estado
  useEffect(() => {
    if (partidaId === null || estado === null) return

    let vigente = true
    void obtenerPartida(partidaId)
      .then((datos) => {
        if (vigente) setPartida(datos)
      })
      .catch(() => {
        // Si falla, se conserva lo que ya había: mejor unos premios de hace un
        // momento que un panel vacío proyectado en la sala.
      })

    return () => {
      vigente = false
    }
  }, [partidaId, estado])

  if (cargando) {
    return (
      <Centrado>
        <p className="text-2xl text-muted-foreground">Cargando…</p>
      </Centrado>
    )
  }

  if (error || partidaId === null) {
    return (
      <Centrado>
        <p className="text-2xl text-muted-foreground">
          {error ?? 'Todavía no hay ninguna partida creada.'}
        </p>
        <Link
          to="/operador/partidas"
          className="text-lg text-primary underline-offset-4 hover:underline"
        >
          Ir a partidas
        </Link>
      </Centrado>
    )
  }

  const recientes = [...vivo.balotas].slice(-RECIENTES).reverse()
  const ganadas = new Set(
    vivo.ganadores.bingos.map((bingo) => bingo.partida_figura_id),
  )
  const formas = partida?.figuras ?? []

  return (
    <div className="flex min-h-screen flex-col gap-4 p-4 sm:gap-5 sm:p-6 xl:p-8">
      {/* Encabezado: de qué juego se trata y si el canal está vivo */}
      <header className="flex flex-wrap items-baseline justify-between gap-x-8 gap-y-2">
        <h1 className="text-2xl font-black tracking-tight sm:text-4xl xl:text-5xl">
          Juego{' '}
          <span className="tabular text-primary">
            {vivo.numeroConsecutivo ?? partida?.numero_consecutivo ?? '—'}
          </span>
        </h1>

        <div className="flex items-center gap-3 text-base sm:gap-6 sm:text-xl xl:text-2xl">
          {/* Salida discreta: en la sala nadie pasa el ratón por encima, así
              que queda invisible proyectado, pero permite volver al configurar. */}
          <Link
            to="/operador/partidas"
            className="text-base text-muted-foreground/25 transition-opacity hover:text-muted-foreground"
          >
            ← salir
          </Link>

          <span className="text-muted-foreground">
            Balotas{' '}
            <span className="font-bold tabular text-foreground">
              {vivo.totalCantadas}
            </span>
            <span className="tabular text-muted-foreground">
              /{TOTAL_BALOTAS}
            </span>
          </span>

          <span className="flex items-center gap-2.5">
            <span
              className={cn(
                'size-3 rounded-full',
                vivo.conexion === 'conectado'
                  ? 'bg-success shadow-[0_0_10px] shadow-success'
                  : vivo.conexion === 'conectando'
                    ? 'bg-primary'
                    : 'bg-destructive',
              )}
              aria-hidden
            />
            <span
              className={cn(
                'font-semibold',
                vivo.estado === 'en_curso'
                  ? 'text-success'
                  : 'text-muted-foreground',
              )}
            >
              {vivo.conexion === 'conectado'
                ? vivo.estado
                  ? ETIQUETA_ESTADO[vivo.estado]
                  : '—'
                : 'Sin conexión'}
            </span>
          </span>
        </div>
      </header>

      {/* El bingo se anuncia a toda la sala. */}
      {vivo.ganadores.bingos.length > 0 && (
        <section
          role="alert"
          className="animate-bingo flex flex-wrap items-center justify-center gap-x-10 gap-y-3 rounded-xl bg-success px-8 py-4 text-success-foreground"
        >
          <span className="text-4xl font-black tracking-wide xl:text-5xl">
            ¡BINGO!
          </span>
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xl xl:text-2xl">
            {vivo.ganadores.bingos.map((bingo) => (
              <span key={bingo.partida_figura_id} className="font-semibold">
                {bingo.figura}
                <span className="mx-2 opacity-60">·</span>
                <span className="tabular">
                  {bingo.cartones.map((c) => c.codigo).join(', ')}
                </span>
              </span>
            ))}
          </div>
          <span className="text-xl font-semibold xl:text-2xl">
            {textoCartones(vivo.ganadores.total_cartones_ganadores)}
          </span>
        </section>
      )}

      <div className="grid flex-1 gap-5 xl:grid-cols-[minmax(0,1fr)_22rem] xl:items-start">
        {/* Tablero de los 75 números: lo que la sala mira todo el rato */}
        <section className="rounded-xl border border-border bg-surface p-3 sm:p-5 xl:p-6">
          <div className="space-y-1.5 sm:space-y-2 xl:space-y-3">
            {RANGOS_POR_COLUMNA.map(([desde, hasta], indice) => (
              <div key={LETRAS[indice]} className="flex items-center gap-2 sm:gap-3">
                <span className="w-6 text-center text-xl font-black text-primary sm:w-9 sm:text-3xl xl:text-4xl">
                  {LETRAS[indice]}
                </span>
                <div className="grid flex-1 grid-cols-15 gap-1 sm:gap-1.5">
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
                          // Se encoge en pantallas pequeñas: son 15 columnas, y
                          // un tamaño pensado para el televisor desbordaría un
                          // portátil. En la sala manda el `xl`.
                          'grid aspect-square place-items-center rounded sm:rounded-lg text-[10px] font-bold tabular transition-colors duration-300 sm:text-base lg:text-xl xl:text-2xl',
                          // El último cantado va en VERDE, como pide el
                          // documento de alcance: es lo que la sala busca con
                          // la vista al oír el número.
                          esUltima
                            ? 'animate-balota bg-success text-success-foreground shadow-lg shadow-success/40'
                            : salio
                              ? 'bg-primary text-primary-foreground'
                              : 'bg-surface-2 text-muted-foreground/50',
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
        </section>

        <div className="space-y-5">
          {/* Última balota y las anteriores */}
          <section className="rounded-xl border border-border bg-surface p-5 text-center">
            {vivo.ultima ? (
              <Bola
                key={vivo.ultima.numero}
                balota={vivo.ultima}
                tamano="grande"
                destacada
                className="animate-balota mx-auto"
              />
            ) : (
              <div className="mx-auto grid size-32 place-items-center rounded-full border-2 border-dashed border-border text-lg text-muted-foreground">
                Sin balotas
              </div>
            )}

            {recientes.length > 1 && (
              <div className="mt-5 border-t border-border pt-4">
                <p className="mb-2.5 text-sm uppercase tracking-wider text-muted-foreground">
                  Anteriores
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {recientes.slice(1).map((balota) => (
                    <Bola key={balota.numero} balota={balota} tamano="mini" />
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* Formas de ganar en juego, con su premio */}
          <section className="rounded-xl border border-border bg-surface p-5">
            <h2 className="mb-3 text-sm uppercase tracking-wider text-muted-foreground">
              Formas de ganar
            </h2>

            {formas.length === 0 ? (
              <p className="text-muted-foreground">
                Esta partida todavía no tiene formas configuradas.
              </p>
            ) : (
              <ul className="space-y-2.5">
                {formas.map((forma) => {
                  const ganada = ganadas.has(forma.id)

                  return (
                    <li
                      key={forma.id}
                      className={cn(
                        'flex items-center gap-3 rounded-lg px-3 py-2 transition-colors',
                        ganada ? 'bg-success/15' : 'bg-surface-2',
                      )}
                    >
                      <div className={cn(ganada && 'opacity-50')}>
                        <CuadriculaFigura
                          patron={forma.figura.patron}
                          tamano="mini"
                          etiqueta={forma.figura.nombre}
                        />
                      </div>

                      <div className="min-w-0 flex-1">
                        <p
                          className={cn(
                            'truncate font-semibold',
                            ganada && 'text-muted-foreground line-through',
                          )}
                        >
                          {forma.figura.nombre}
                        </p>
                        <p
                          className={cn(
                            'text-lg font-bold tabular',
                            ganada ? 'text-success' : 'text-primary',
                          )}
                        >
                          {formatearPesos(forma.valor_premio)}
                        </p>
                      </div>

                      <span
                        className={cn(
                          'shrink-0 rounded-full px-2.5 py-1 text-xs font-bold uppercase tracking-wide',
                          ganada
                            ? 'bg-success text-success-foreground'
                            : 'bg-primary/20 text-primary',
                        )}
                      >
                        {ganada ? 'Ganada' : 'Jugando'}
                      </span>
                    </li>
                  )
                })}
              </ul>
            )}
          </section>

          {/* Sitio reservado para la cámara de la sala. Es de la Fase 3
              (docs/09 #10 lo pide como marcador de posición): se deja indicado
              para que se vea dónde encaja, sin ocupar espacio útil. */}
          <section className="hidden rounded-xl border border-dashed border-border p-5 text-center xl:block">
            <p className="text-sm uppercase tracking-wider text-muted-foreground">
              Video en vivo
            </p>
            <p className="mt-1 text-xs text-muted-foreground/70">
              La cámara de la sala se integra en la Fase 3.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}

function Centrado({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 text-center">
      {children}
    </div>
  )
}
