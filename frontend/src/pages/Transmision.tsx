import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Bola } from '@/components/balotera/Bola'
import { BotonPantallaCompleta } from '@/components/transmision/BotonPantallaCompleta'
import { CarruselFormas } from '@/components/transmision/CarruselFormas'
import { EstadoVenta } from '@/components/transmision/EstadoVenta'
import { VideoCamara } from '@/components/transmision/VideoCamara'
import { usePartidaEnVivo } from '@/hooks/usePartidaEnVivo'
import { LETRAS, RANGOS_POR_COLUMNA, TOTAL_BALOTAS } from '@/lib/bingo'
import { textoCartones } from '@/lib/ganadores'
import {
  ETIQUETA_ESTADO,
  listarPartidas,
  obtenerPartida,
  type Partida,
} from '@/lib/partidas'
import { cn } from '@/lib/utils'

/** Cuántas balotas recientes se muestran como figuritas. */
const RECIENTES = 5

/**
 * Tablero de transmisión — tarea #6 de la Fase 1, rediseñado a petición del
 * cliente tras ver la demo (ver `PROGRESS.md`, Fase 1.6, tarea #3).
 *
 * Pantalla pública para **proyectar en el televisor de la sala**. Sin login y
 * de solo lectura: se alimenta del mismo WebSocket de la partida que la
 * balotera, así que no hay forma de que muestre algo distinto de lo que ve el
 * operador. Por eso tampoco lleva la barra de navegación de la aplicación (va
 * fuera del `Layout`): en la sala ocupa la pantalla entera, y además se puede
 * poner en pantalla completa de verdad con `BotonPantallaCompleta`.
 *
 * Orden de bloques pedido por el cliente, de arriba hacia abajo: el tablero
 * de números, las formas de ganar (una a la vez, en bucle), el video de la
 * cámara de la sala, las últimas 5 balotas, y un contador de cuántas de las
 * 75 van cantadas. Todo pensado para caber en la pantalla **sin scroll**.
 *
 * **Lo que aquí NO se muestra:** los avisos de «a una / a dos balotas». Son
 * información de control del operador; proyectados serían un delator que le
 * quita la gracia al juego. El bingo sí se anuncia (de forma anónima: solo el
 * código del cartón, nunca la identidad de quien juega), que es la fiesta.
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
    <div className="flex h-screen flex-col gap-3 overflow-hidden p-3 sm:gap-4 sm:p-4 xl:gap-5 xl:p-6">
      {/* Encabezado: de qué juego se trata, el bombillo de venta, pantalla
          completa y si el canal está vivo. */}
      <header className="flex shrink-0 flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <div className="flex items-baseline gap-4">
          <h1 className="text-2xl font-black tracking-tight sm:text-4xl xl:text-5xl">
            Juego{' '}
            <span className="tabular text-primary">
              {vivo.numeroConsecutivo ?? partida?.numero_consecutivo ?? '—'}
            </span>
          </h1>
          <EstadoVenta ventaAbierta={vivo.ventaAbierta} />
        </div>

        <div className="flex items-center gap-3 text-sm sm:gap-4 sm:text-lg xl:gap-5 xl:text-xl">
          <span className="flex items-center gap-2">
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

          <BotonPantallaCompleta />

          {/* Salida discreta: en la sala nadie pasa el ratón por encima, así
              que queda invisible proyectado, pero permite volver al configurar. */}
          <Link
            to="/operador/partidas"
            className="text-base text-muted-foreground/25 transition-opacity hover:text-muted-foreground"
          >
            ← salir
          </Link>
        </div>
      </header>

      {/* El bingo se anuncia a toda la sala, siempre de forma anónima: solo
          el código del cartón, nunca quién juega. */}
      {vivo.ganadores.bingos.length > 0 && (
        <section
          role="alert"
          className="animate-bingo flex shrink-0 flex-wrap items-center justify-center gap-x-10 gap-y-2 rounded-xl bg-success px-6 py-3 text-success-foreground"
        >
          <span className="text-3xl font-black tracking-wide xl:text-4xl">
            ¡BINGO!
          </span>
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-1 text-lg xl:text-xl">
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
          <span className="text-lg font-semibold xl:text-xl">
            {textoCartones(vivo.ganadores.total_cartones_ganadores)}
          </span>
        </section>
      )}

      {/* Cuerpo: el tablero arriba, dominando la pantalla, y la franja de
          abajo con las cuatro cosas que pidió el cliente en su orden:
          formas de ganar, cámara, últimas balotas y el contador. */}
      <div className="grid min-h-0 flex-1 grid-rows-[minmax(0,1fr)_minmax(0,auto)] gap-3 sm:gap-4 xl:gap-5">
        <section className="min-h-0 overflow-hidden rounded-xl border border-border bg-surface p-2 sm:p-4 xl:p-6">
          <div className="grid h-full grid-rows-5 gap-1 sm:gap-1.5 xl:gap-2.5">
            {RANGOS_POR_COLUMNA.map(([desde, hasta], indice) => (
              <div
                key={LETRAS[indice]}
                className="grid min-h-0 grid-cols-[auto_repeat(15,minmax(0,1fr))] items-stretch gap-2 sm:gap-3"
              >
                <span className="flex items-center justify-center text-lg font-black text-primary sm:text-2xl xl:text-4xl">
                  {LETRAS[indice]}
                </span>
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
                        // Cada celda llena su casilla del grid, tanto de
                        // ancho como de alto: si el tamaño se sacara del
                        // ancho (como con `aspect-square`), 5 filas de
                        // celdas «cuadradas» podían pedir más alto del que
                        // tenía la sección, y el `overflow-hidden` de arriba
                        // recortaba en silencio la fila de encima y la de
                        // abajo. Al depender del propio renglón del grid, el
                        // tablero siempre cabe entero.
                        'grid min-h-0 place-items-center rounded sm:rounded-lg text-[9px] font-bold tabular transition-colors duration-300 sm:text-sm lg:text-lg xl:text-2xl',
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
            ))}
          </div>
        </section>

        <div className="grid h-[30vh] min-h-[9rem] grid-cols-4 gap-3 sm:gap-4 xl:h-[32vh] xl:gap-5">
          {/* 1. Formas de ganar, alternando. */}
          <CarruselFormas formas={formas} ganadas={ganadas} />

          {/* 2. Cámara de la sala. */}
          <VideoCamara />

          {/* 3. Últimas balotas. */}
          <section className="flex min-h-0 flex-col items-center justify-center gap-2 overflow-hidden rounded-xl border border-border bg-surface p-2 xl:gap-3 xl:p-3">
            <h2 className="shrink-0 text-[10px] uppercase tracking-wider text-muted-foreground xl:text-xs">
              Últimas balotas
            </h2>
            {recientes.length === 0 ? (
              <p className="text-xs text-muted-foreground">Sin balotas todavía.</p>
            ) : (
              <div className="flex flex-wrap items-center justify-center gap-1.5 xl:gap-2">
                {recientes.map((balota, i) => (
                  <Bola
                    key={balota.numero}
                    balota={balota}
                    tamano={i === 0 ? 'normal' : 'mini'}
                    destacada={i === 0}
                    className={i === 0 ? 'animate-balota' : undefined}
                  />
                ))}
              </div>
            )}
          </section>

          {/* 4. Contador de balotas jugadas. */}
          <section className="flex min-h-0 flex-col items-center justify-center gap-1 overflow-hidden rounded-xl border border-border bg-surface p-2 text-center xl:p-3">
            <h2 className="text-[10px] uppercase tracking-wider text-muted-foreground xl:text-xs">
              Balotas jugadas
            </h2>
            <p className="text-3xl font-black tabular leading-none sm:text-4xl xl:text-6xl">
              {vivo.totalCantadas}
              <span className="text-base font-semibold text-muted-foreground sm:text-lg xl:text-2xl">
                /{TOTAL_BALOTAS}
              </span>
            </p>
            <p className="text-[10px] text-muted-foreground xl:text-xs">
              quedan {vivo.restantes}
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
