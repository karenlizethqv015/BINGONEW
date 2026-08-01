import { useEffect, useRef, useState } from 'react'

import { CuadriculaFigura } from '@/components/figuras/CuadriculaFigura'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { PLANTILLAS, contarCeldas, patronVacio, type Patron } from '@/lib/bingo'
import {
  TIPOS_FIGURA,
  actualizarFigura,
  crearFigura,
  type Figura,
  type TipoFigura,
} from '@/lib/figuras'

interface Props {
  /** Figura que se está editando, o null para crear una nueva. */
  editando: Figura | null
  onGuardada: (figura: Figura) => void
  onCancelar: () => void
}

/** Formulario de creación y edición de una figura. */
export function EditorFigura({ editando, onGuardada, onCancelar }: Props) {
  const [nombre, setNombre] = useState('')
  const [patron, setPatron] = useState<Patron>(patronVacio)
  const [tipo, setTipo] = useState<TipoFigura>('figura')
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)
  const refNombre = useRef<HTMLInputElement>(null)

  // Al elegir una figura del catálogo (o al pasar a "nueva"), se recarga el
  // formulario con sus datos.
  useEffect(() => {
    setNombre(editando?.nombre ?? '')
    setPatron(editando?.patron ?? patronVacio())
    setTipo(editando?.tipo ?? 'figura')
    setError(null)
  }, [editando])

  const celdas = contarCeldas(patron)
  const faltaNombre = nombre.trim().length === 0
  const faltanCeldas = celdas === 0

  /**
   * El botón de guardar NO se deshabilita cuando falta algo.
   *
   * Un botón gris sin explicación deja al administrador adivinando qué le
   * falta: dibuja la figura, ve el botón apagado y no hay ninguna pista de que
   * el problema es el nombre vacío. Se prefiere dejarlo pulsable y decir
   * exactamente qué falta al intentar guardar.
   */
  const guardar = async () => {
    if (faltaNombre) {
      setError('Ponle un nombre a la figura antes de guardarla.')
      refNombre.current?.focus()
      return
    }

    if (faltanCeldas) {
      setError('Marca al menos una celda en la cuadrícula para formar la figura.')
      return
    }

    setGuardando(true)
    setError(null)
    try {
      const datos = { nombre: nombre.trim(), patron, tipo }
      const figura = editando
        ? await actualizarFigura(editando.id, datos)
        : await crearFigura(datos)

      onGuardada(figura)
      if (!editando) {
        // Tras crear, se deja el formulario limpio para encadenar otra figura.
        // El tipo se conserva: lo normal es clasificar varias seguidas en la
        // misma categoría.
        setNombre('')
        setPatron(patronVacio())
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo guardar la figura.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{editando ? 'Editar figura' : 'Nueva figura'}</CardTitle>
        <CardDescription>
          Haz clic en las celdas, o arrastra para pintar varias de una vez.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-5">
        <div className="space-y-1.5">
          <label
            htmlFor="nombre-figura"
            className="flex items-baseline gap-1.5 text-sm font-medium"
          >
            Nombre
            <span className="text-xs font-normal text-muted-foreground">
              (obligatorio)
            </span>
          </label>
          <Input
            id="nombre-figura"
            ref={refNombre}
            value={nombre}
            onChange={(e) => {
              setNombre(e.target.value)
              // Al empezar a escribir desaparece el aviso de nombre faltante.
              if (error && e.target.value.trim()) setError(null)
            }}
            aria-invalid={Boolean(error) && faltaNombre}
            placeholder="Ej. Cuatro esquinas"
            maxLength={60}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !guardando) void guardar()
            }}
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="tipo-figura" className="text-sm font-medium">
            Categoría
          </label>
          <select
            id="tipo-figura"
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoFigura)}
            className="h-10 w-full rounded-md border border-input bg-surface-2 px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            {TIPOS_FIGURA.map((opcion) => (
              <option key={opcion.valor} value={opcion.valor}>
                {opcion.etiqueta}
              </option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground">
            Al armar una partida, cada categoría ofrecerá solo las figuras
            clasificadas aquí.
          </p>
        </div>

        <CuadriculaFigura patron={patron} onChange={setPatron} />

        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {faltanCeldas
              ? 'Marca al menos una celda'
              : `${celdas} ${celdas === 1 ? 'celda' : 'celdas'}`}
          </span>
          <button
            type="button"
            onClick={() => setPatron(patronVacio())}
            disabled={faltanCeldas}
            className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline disabled:opacity-40 disabled:hover:no-underline"
          >
            Limpiar
          </button>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Plantillas <span className="normal-case tracking-normal">(opcional)</span>
          </p>
          <div className="flex flex-wrap gap-1.5">
            {PLANTILLAS.map((plantilla) => (
              <button
                key={plantilla.nombre}
                type="button"
                onClick={() => {
                  setPatron(plantilla.patron.map((fila) => [...fila]))
                  if (!nombre.trim()) setNombre(plantilla.nombre)
                }}
                className="rounded-md border border-border bg-surface-2 px-2.5 py-1 text-xs transition-colors hover:border-primary/60 hover:text-primary"
              >
                {plantilla.nombre}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {error}
          </p>
        )}

        <div className="flex gap-2">
          <Button onClick={() => void guardar()} disabled={guardando}>
            {guardando ? 'Guardando…' : editando ? 'Guardar cambios' : 'Crear figura'}
          </Button>
          {editando && (
            <Button variant="ghost" onClick={onCancelar} disabled={guardando}>
              Cancelar
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
