import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { obtenerSalud, type EstadoSalud } from '@/lib/api'

/**
 * Panel de administración.
 *
 * En la Fase 0 solo comprueba la conexión con el backend (verifica de paso que
 * el proxy HTTP de Vite está bien configurado). Los controles reales de la
 * partida llegan en la tarea #7 de la Fase 1.
 */
export function Admin() {
  const [salud, setSalud] = useState<EstadoSalud | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)

  const consultar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      setSalud(await obtenerSalud())
    } catch (e) {
      setSalud(null)
      setError(
        e instanceof Error
          ? e.message
          : 'No se pudo contactar el backend. ¿Está corriendo uvicorn?',
      )
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    void consultar()
  }, [consultar])

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Administración</h1>
        <p className="text-muted-foreground">
          Los controles de la partida se implementan en la tarea #7 de la Fase 1.
        </p>
      </header>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Formas de ganar</CardTitle>
          <CardDescription>
            Catálogo de figuras: diseña los patrones que pueden ganar y
            reutilízalos en cualquier partida.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild size="sm">
            <Link to="/admin/figuras">Abrir catálogo</Link>
          </Button>
        </CardContent>
      </Card>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Partidas</CardTitle>
          <CardDescription>
            Crea una partida y elige qué formas de ganar se juegan en ella, con
            su premio y su orden.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild size="sm">
            <Link to="/admin/partidas">Ver partidas</Link>
          </Button>
        </CardContent>
      </Card>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Conexión con el backend</CardTitle>
          <CardDescription>
            Consulta <code className="text-primary">GET /api/health</code> a
            través del proxy de Vite.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {cargando && (
            <p className="text-sm text-muted-foreground">Consultando…</p>
          )}

          {error && (
            <p className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          {salud && (
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <dt className="text-muted-foreground">Servicio</dt>
              <dd className="font-medium">{salud.servicio}</dd>

              <dt className="text-muted-foreground">Versión</dt>
              <dd className="font-medium tabular">{salud.version}</dd>

              <dt className="text-muted-foreground">Motor de base de datos</dt>
              <dd className="font-medium">{salud.motor_bd}</dd>

              <dt className="text-muted-foreground">Base de datos</dt>
              <dd>
                <span
                  className={
                    salud.base_datos
                      ? 'font-semibold text-success'
                      : 'font-semibold text-destructive'
                  }
                >
                  {salud.base_datos ? 'Conectada' : 'Sin conexión'}
                </span>
              </dd>
            </dl>
          )}

          <Button onClick={() => void consultar()} disabled={cargando} size="sm">
            Volver a consultar
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
