import { useEffect, useState } from 'react'

import { CuadriculaFigura } from '@/components/figuras/CuadriculaFigura'
import { formatearPesos, type FormaSeleccionada } from '@/lib/partidas'

/** Cada cuántos milisegundos cambia la forma que se muestra. */
const INTERVALO_MS = 5000

interface Props {
  formas: FormaSeleccionada[]
  /** ids de `partida_figura` que ya se ganaron. */
  ganadas: Set<number>
}

/**
 * Muestra las formas de ganar de a una, alternando en bucle.
 *
 * Antes la pantalla de transmisión listaba todas las formas apiladas — con
 * varias formas eso ocupaba demasiado espacio vertical para caber sin scroll.
 * El cliente pidió condensarlo a un solo cuadro que va rotando.
 */
export function CarruselFormas({ formas, ganadas }: Props) {
  const [indice, setIndice] = useState(0)

  // Formas ya ganadas: no se muestran en el carrusel para no confundir al
  // jugador con un premio que ya se repartió.
  const enJuego = formas.filter((f) => !ganadas.has(f.id))

  // Si cambió la lista en juego (se agregó, quitó, o se acaba de ganar una),
  // no seguir apuntando a una posición que ya no existe.
  useEffect(() => {
    setIndice(0)
  }, [enJuego.length])

  useEffect(() => {
    if (enJuego.length <= 1) return
    const id = window.setInterval(
      () => setIndice((i) => (i + 1) % enJuego.length),
      INTERVALO_MS,
    )
    return () => window.clearInterval(id)
  }, [enJuego.length])

  const forma = enJuego[indice] as FormaSeleccionada | undefined

  return (
    <section className="flex min-h-0 flex-col items-center justify-center gap-1 overflow-hidden rounded-xl border border-border bg-surface p-2 text-center xl:gap-2 xl:p-3">
      {forma === undefined ? (
        <p className="text-xs text-muted-foreground">
          {formas.length === 0
            ? 'Sin formas configuradas.'
            : 'Todas las formas ya se ganaron.'}
        </p>
      ) : (
        <>
          {/* Este envoltorio SÍ lleva `min-h-0` y `flex-1`: a diferencia de
              un tope de ancho fijo (que dejaba que la figura pidiera más
              alto del que había y se recortara o, peor, se saliera de su
              caja y quedara flotando encima del nombre y el premio), aquí
              es el propio `flex-1` el que le da a este recuadro el alto
              exacto que sobra en la tarjeta — ni un pixel más. El
              `overflow-hidden` es solo una red de seguridad local: como
              `CuadriculaFigura` mide su alto a partir del ancho (letras +
              cuadrícula cuadrada), el ajuste no es matemáticamente exacto,
              pero cualquier desajuste queda contenido aquí adentro y nunca
              se derrama sobre el nombre o el premio de abajo. */}
          <div className="flex min-h-0 w-full flex-1 items-center justify-center overflow-hidden">
            <div className="aspect-[5/6] h-full max-w-full">
              <CuadriculaFigura
                patron={forma.figura.patron}
                tamano="grande"
                etiqueta={forma.figura.nombre}
              />
            </div>
          </div>

          <p className="shrink-0 text-sm font-bold tabular text-primary xl:text-lg">
            {formatearPesos(forma.valor_premio)}
          </p>
        </>
      )}
    </section>
  )
}
