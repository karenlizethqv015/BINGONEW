import { useCallback, useEffect, useState } from 'react'

import { obtenerSalud, type EstadoSalud } from '@/lib/api'
import { cn } from '@/lib/utils'

/**
 * Comprobación de que el backend responde.
 *
 * Existe desde la Fase 0 y se conserva a propósito: en la instalación final en
 * LAN es lo primero que hay que mirar cuando una pantalla de la sala se queda
 * en blanco. Vive aparte (y no dentro de `Admin.tsx`) porque tanto el panel de
 * administración como el de operación la necesitan.
 */
export function EstadoDelBackend() {
  const [salud, setSalud] = useState<EstadoSalud | null>(null)
  const [error, setError] = useState(false)

  const consultar = useCallback(async () => {
    try {
      setSalud(await obtenerSalud())
      setError(false)
    } catch {
      setSalud(null)
      setError(true)
    }
  }, [])

  useEffect(() => {
    void consultar()
  }, [consultar])

  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg border border-border bg-surface px-4 py-2.5 text-sm">
      <span className="flex items-center gap-2">
        <span
          className={cn(
            'size-2 rounded-full',
            salud?.base_datos ? 'bg-success' : 'bg-destructive',
          )}
          aria-hidden
        />
        <span className="text-muted-foreground">
          {error
            ? 'Sin conexión con el backend. ¿Está corriendo uvicorn?'
            : salud
              ? `${salud.servicio} v${salud.version} · ${salud.motor_bd}`
              : 'Comprobando…'}
        </span>
      </span>

      <button
        type="button"
        onClick={() => void consultar()}
        className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
      >
        Volver a comprobar
      </button>
    </div>
  )
}
