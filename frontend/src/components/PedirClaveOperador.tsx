import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { alFaltarClaveOperador } from '@/lib/http'
import {
  alCambiarClaveOperador,
  claveOperador,
  guardarClaveOperador,
  olvidarClaveOperador,
} from '@/lib/operador'

/**
 * Pide la clave de operador cuando el backend la reclama.
 *
 * Calco de `PedirClaveAdmin`, para el otro rol: partidas, balotera y
 * cartones. Va colgado del `Layout` igual que aquel, y por el mismo motivo
 * tampoco aparece nunca si el servidor no tiene `OPERADOR_CLAVE` configurada.
 */
export function PedirClaveOperador() {
  const [pidiendo, setPidiendo] = useState(false)
  const [valor, setValor] = useState('')
  const [hayClave, setHayClave] = useState(() => claveOperador() !== null)

  useEffect(
    () => alCambiarClaveOperador(() => setHayClave(claveOperador() !== null)),
    [],
  )

  // El backend acaba de rechazar una acción por falta de clave de operador.
  useEffect(
    () =>
      alFaltarClaveOperador(() => {
        setValor('')
        setPidiendo(true)
      }),
    [],
  )

  const guardar = () => {
    const limpia = valor.trim()
    if (!limpia) return
    guardarClaveOperador(limpia)
    setPidiendo(false)
  }

  if (!pidiendo) {
    // Con la clave puesta se ofrece salir, para poder dejar la pantalla en un
    // equipo de la sala sin dejar también el mando.
    if (!hayClave) return null

    return (
      // bottom-12 y no bottom-3: si también hay clave de admin guardada, su
      // botón "Salir de administración" ya ocupa esa esquina. Se apilan.
      <button
        type="button"
        onClick={olvidarClaveOperador}
        className="fixed bottom-12 right-3 z-20 rounded-md bg-surface-2/70 px-2.5 py-1 text-xs text-muted-foreground opacity-40 transition-opacity hover:opacity-100"
      >
        Salir de operación
      </button>
    )
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-background/80 p-4 backdrop-blur">
      <div className="w-full max-w-sm space-y-4 rounded-lg border border-border bg-surface p-6 shadow-xl">
        <div className="space-y-1.5">
          <h2 className="text-lg font-semibold">Clave de operador</h2>
          <p className="text-sm text-muted-foreground">
            Esta acción modifica la partida, la balotera o los cartones. El
            tablero de la sala y el cartón del jugador no necesitan clave.
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
