import { useEffect, useState } from 'react'

/**
 * Tiempo transcurrido desde que arrancó el sorteo, en «mm:ss».
 *
 * Es el «reloj de la jugada» que tenía la aplicación anterior (ver
 * `docs/04-referencia-app-anterior.md`). Se calcula contra la hora de arranque
 * que manda el backend, **no acumulando segundos en el navegador**: así una
 * pestaña que se abre a mitad de partida arranca con la hora correcta, y no se
 * desfasa si el equipo se suspende o la pestaña queda en segundo plano (los
 * navegadores frenan los temporizadores de las pestañas ocultas).
 *
 * Sigue corriendo con la partida pausada: mide cuánto lleva la jugada, no
 * cuánto tiempo se ha estado cantando.
 */
export function useRelojDeJugada(iniciadaEn: string | null): string | null {
  const [ahora, setAhora] = useState(() => Date.now())

  useEffect(() => {
    if (!iniciadaEn) return

    const temporizador = window.setInterval(() => setAhora(Date.now()), 1000)
    return () => window.clearInterval(temporizador)
  }, [iniciadaEn])

  if (!iniciadaEn) return null

  const arranque = new Date(iniciadaEn).getTime()
  if (Number.isNaN(arranque)) return null

  const segundos = Math.max(0, Math.floor((ahora - arranque) / 1000))
  const minutos = Math.floor(segundos / 60)

  return `${String(minutos).padStart(2, '0')}:${String(segundos % 60).padStart(2, '0')}`
}
