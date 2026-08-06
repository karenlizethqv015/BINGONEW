import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  alCambiarClaveAdmin,
  claveAdmin,
  guardarClaveAdmin,
  olvidarClaveAdmin,
} from '@/lib/admin'
import { alFaltarClaveAdmin } from '@/lib/http'

/**
 * Pide la clave de administración cuando el backend la reclama.
 *
 * Va colgado del `Layout` y no de cada pantalla: la clave hace falta en
 * cualquier acción que modifique la partida, y repetir este diálogo en cada
 * vista sería garantizar que falte en alguna.
 *
 * **No aparece nunca si el servidor no tiene clave configurada**, que es el caso
 * de desarrollo y el de la instalación en la LAN de la sala: el backend no
 * responde 401 y aquí no se entera nadie. Solo sale en la demo pública.
 */
export function PedirClaveAdmin() {
  const [pidiendo, setPidiendo] = useState(false)
  const [valor, setValor] = useState('')
  const [hayClave, setHayClave] = useState(() => claveAdmin() !== null)

  useEffect(() => alCambiarClaveAdmin(() => setHayClave(claveAdmin() !== null)), [])

  // El backend acaba de rechazar una acción por falta de clave.
  useEffect(
    () =>
      alFaltarClaveAdmin(() => {
        setValor('')
        setPidiendo(true)
      }),
    [],
  )

  const guardar = () => {
    const limpia = valor.trim()
    if (!limpia) return
    guardarClaveAdmin(limpia)
    setPidiendo(false)
  }

  if (!pidiendo) {
    // Con la clave puesta se ofrece salir, para poder dejar la pantalla en un
    // equipo de la sala sin dejar también el mando.
    if (!hayClave) return null

    return (
      <button
        type="button"
        onClick={olvidarClaveAdmin}
        className="fixed bottom-3 right-3 z-20 rounded-md bg-surface-2/70 px-2.5 py-1 text-xs text-muted-foreground opacity-40 transition-opacity hover:opacity-100"
      >
        Salir de administración
      </button>
    )
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-background/80 p-4 backdrop-blur">
      <div className="w-full max-w-sm space-y-4 rounded-lg border border-border bg-surface p-6 shadow-xl">
        <div className="space-y-1.5">
          <h2 className="text-lg font-semibold">Clave de administración</h2>
          <p className="text-sm text-muted-foreground">
            Esta acción modifica la partida. El tablero de la sala y el cartón
            del jugador no necesitan clave.
          </p>
        </div>

        <Input
          type="password"
          autoFocus
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') guardar()
            if (e.key === 'Escape') setPidiendo(false)
          }}
          placeholder="Clave"
        />

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setPidiendo(false)}>
            Cancelar
          </Button>
          <Button onClick={guardar} disabled={!valor.trim()}>
            Entrar
          </Button>
        </div>

        <p className="text-xs text-muted-foreground">
          Después de entrar hay que repetir la acción.
        </p>
      </div>
    </div>
  )
}
