import { Maximize2, Minimize2 } from 'lucide-react'
import { useEffect, useState } from 'react'

/**
 * Pone o quita la pantalla completa del navegador (Fullscreen API).
 *
 * Pedido del cliente para `/transmision`: proyectarla "sin las ventanas del
 * navegador". Discreto a propósito, igual que el enlace "← salir" de al
 * lado: en la sala nadie pasa el mouse por encima del televisor.
 */
export function BotonPantallaCompleta() {
  const [activa, setActiva] = useState(() => document.fullscreenElement !== null)

  useEffect(() => {
    const actualizar = () => setActiva(document.fullscreenElement !== null)
    document.addEventListener('fullscreenchange', actualizar)
    return () => document.removeEventListener('fullscreenchange', actualizar)
  }, [])

  // Si el navegador no soporta la API (poco común), mejor no mostrar un
  // botón que no hace nada.
  if (typeof document.documentElement.requestFullscreen !== 'function') {
    return null
  }

  const alternar = () => {
    if (document.fullscreenElement) {
      void document.exitFullscreen()
    } else {
      void document.documentElement.requestFullscreen()
    }
  }

  return (
    <button
      type="button"
      onClick={alternar}
      title={activa ? 'Salir de pantalla completa' : 'Pantalla completa'}
      className="text-muted-foreground/40 transition-colors hover:text-muted-foreground"
    >
      {activa ? (
        <Minimize2 className="size-4 xl:size-5" aria-hidden />
      ) : (
        <Maximize2 className="size-4 xl:size-5" aria-hidden />
      )}
      <span className="sr-only">
        {activa ? 'Salir de pantalla completa' : 'Pantalla completa'}
      </span>
    </button>
  )
}
