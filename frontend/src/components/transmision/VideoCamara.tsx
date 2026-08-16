import { VideoOff } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

/**
 * Cámara del computador que muestra la pantalla de transmisión.
 *
 * Primera versión pedida por el cliente: la cámara **local** del equipo que
 * tiene abierta `/transmision` (la de la sala, apuntando a la mesa o al
 * presentador), sin selector de cámara ni control remoto — eso queda para
 * más adelante si hace falta.
 *
 * Si el navegador niega el permiso o no hay cámara, se muestra un aviso en
 * vez de romper el resto de la pantalla: el tablero y las balotas siguen
 * funcionando igual sin video.
 */
export function VideoCamara() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Este navegador no puede mostrar la cámara.')
      return
    }

    let cancelado = false
    let stream: MediaStream | null = null

    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((obtenido) => {
        if (cancelado) {
          // El componente se desmontó mientras el navegador pedía permiso.
          obtenido.getTracks().forEach((pista) => pista.stop())
          return
        }
        stream = obtenido
        if (videoRef.current) videoRef.current.srcObject = obtenido
      })
      .catch(() => {
        if (!cancelado) {
          setError('Sin acceso a la cámara de este equipo.')
        }
      })

    return () => {
      cancelado = true
      stream?.getTracks().forEach((pista) => pista.stop())
    }
  }, [])

  return (
    <section className="relative min-h-0 overflow-hidden rounded-xl border border-border bg-surface">
      {error ? (
        <div className="flex h-full flex-col items-center justify-center gap-1.5 p-2 text-center">
          <VideoOff className="size-5 text-muted-foreground/60 xl:size-6" aria-hidden />
          <p className="text-[10px] text-muted-foreground xl:text-xs">{error}</p>
        </div>
      ) : (
        // muted: los navegadores bloquean el autoplay con audio sin gesto del
        // usuario, y esta pantalla se deja puesta sola. playsInline evita que
        // algunos navegadores móviles la abran a pantalla completa por su cuenta.
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="size-full object-cover"
        />
      )}
    </section>
  )
}
