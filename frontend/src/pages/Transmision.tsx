import { useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { urlWebSocket } from '@/lib/api'

type Estado = 'conectando' | 'conectado' | 'desconectado'

const ETIQUETA_ESTADO: Record<Estado, string> = {
  conectando: 'Conectando…',
  conectado: 'Conectado',
  desconectado: 'Desconectado',
}

/**
 * Pantalla de transmisión.
 *
 * En la Fase 0 solo verifica el canal en tiempo real contra `/ws/echo`, que es
 * el mismo `GestorConexiones` del backend que en la Fase 1 usará la balotera
 * para emitir las balotas. El tablero de 75 números y las últimas 5 balotas
 * llegan en la tarea #6.
 */
export function Transmision() {
  const [estado, setEstado] = useState<Estado>('conectando')
  const [mensajes, setMensajes] = useState<string[]>([])
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const socket = new WebSocket(urlWebSocket('/ws/echo'))
    socketRef.current = socket

    socket.onopen = () => setEstado('conectado')
    socket.onclose = () => setEstado('desconectado')
    socket.onerror = () => setEstado('desconectado')
    socket.onmessage = (evento) => {
      const datos = JSON.parse(evento.data) as { tipo: string; mensaje: string }
      setMensajes((previos) => [`${datos.tipo}: ${datos.mensaje}`, ...previos].slice(0, 5))
    }

    // Cierra el socket al desmontar para no dejar conexiones colgadas, sobre
    // todo con el hot reload de Vite.
    return () => socket.close()
  }, [])

  const enviarPrueba = () => {
    socketRef.current?.send(`prueba ${new Date().toLocaleTimeString()}`)
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Transmisión</h1>
        <p className="text-muted-foreground">
          El tablero de 75 números y las últimas balotas se implementan en la
          tarea #6 de la Fase 1.
        </p>
      </header>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Canal en tiempo real</CardTitle>
          <CardDescription>
            Conexión WebSocket a <code className="text-primary">/ws/echo</code>.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex items-center gap-2 text-sm">
            <span
              className={
                estado === 'conectado'
                  ? 'size-2.5 rounded-full bg-success shadow-[0_0_8px] shadow-success'
                  : estado === 'conectando'
                    ? 'size-2.5 rounded-full bg-primary'
                    : 'size-2.5 rounded-full bg-destructive'
              }
              aria-hidden
            />
            <span
              className={
                estado === 'conectado'
                  ? 'font-semibold text-success'
                  : estado === 'desconectado'
                    ? 'font-semibold text-destructive'
                    : 'font-semibold text-primary'
              }
            >
              {ETIQUETA_ESTADO[estado]}
            </span>
          </div>

          <Button
            onClick={enviarPrueba}
            disabled={estado !== 'conectado'}
            size="sm"
            variant="success"
          >
            Enviar mensaje de prueba
          </Button>

          {mensajes.length > 0 && (
            <ul className="space-y-1 text-sm text-muted-foreground">
              {mensajes.map((mensaje, indice) => (
                <li
                  key={`${mensaje}-${indice}`}
                  className="animate-balota rounded-md bg-surface-2 px-3 py-1.5 tabular"
                >
                  {mensaje}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
