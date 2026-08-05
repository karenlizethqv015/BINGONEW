import { QRCodeSVG } from 'qrcode.react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'

interface Props {
  partidaId: number
  /** Código visible del cartón, como «A-7». */
  codigo: string
  onCerrar: () => void
}

/**
 * El enlace del cartón, en grande y como código QR, para que el jugador entre
 * escaneándolo desde su celular.
 *
 * Existe por lo incómodo que es teclear una dirección larga en un teléfono, que
 * es exactamente lo que hay que hacer para enseñarle el MVP a alguien. Con el QR
 * se apunta la cámara y ya.
 *
 * El origen sale de `window.location`, nunca escrito a mano: es la misma regla
 * que hace que el WebSocket se conecte solo, y lo que permite que esto funcione
 * igual en la demo de internet que en la LAN de la sala, sin recompilar nada.
 */
export function QrDeCarton({ partidaId, codigo, onCerrar }: Props) {
  const [copiado, setCopiado] = useState(false)

  const enlace = `${window.location.origin}/jugador?partida=${partidaId}&carton=${codigo}`

  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(enlace)
      setCopiado(true)
      window.setTimeout(() => setCopiado(false), 2000)
    } catch {
      // Sin permiso de portapapeles: el enlace está a la vista para copiarlo a
      // mano, así que no hace falta molestar con un error.
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-background/80 p-4 backdrop-blur"
      onClick={onCerrar}
    >
      <div
        className="w-full max-w-sm space-y-4 rounded-lg border border-border bg-surface p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">
            Cartón <span className="tabular text-primary">{codigo}</span>
          </h2>
          <p className="text-sm text-muted-foreground">
            Que lo escanee con la cámara del celular. Se marcará solo con cada
            balota que se cante.
          </p>
        </div>

        {/* Blanco y negro literales, no tokens de la paleta: un QR necesita
            contraste máximo para que la cámara lo lea, y en el fondo oscuro de
            la aplicación muchos teléfonos fallan. */}
        <div
          className="grid place-items-center rounded-md p-4"
          style={{ background: '#ffffff' }}
        >
          <QRCodeSVG value={enlace} size={208} level="M" />
        </div>

        <p className="break-all rounded bg-surface-2 px-3 py-2 text-xs text-muted-foreground">
          {enlace}
        </p>

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => void copiar()}>
            {copiado ? 'Copiado' : 'Copiar enlace'}
          </Button>
          <Button onClick={onCerrar}>Cerrar</Button>
        </div>
      </div>
    </div>
  )
}
