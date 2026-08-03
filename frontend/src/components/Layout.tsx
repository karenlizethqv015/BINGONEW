import { Link, NavLink, Outlet } from 'react-router-dom'

import { cn } from '@/lib/utils'

interface Ruta {
  to: string
  etiqueta: string
  /** Marca las vistas que todavía son de la Fase 2. */
  fase2?: boolean
  /**
   * Resalta el enlace solo con coincidencia exacta. Hace falta en las rutas que
   * son prefijo de otras (`/admin` lo es de todas), pero NO en las que tienen
   * subrutas propias: estando en `/admin/partidas/3` queremos que "Partidas"
   * siga resaltado.
   */
  exacto?: boolean
}

/** Rutas por rol. La convención está fijada en CLAUDE.md. */
const RUTAS: Ruta[] = [
  { to: '/admin', etiqueta: 'Administración', exacto: true },
  { to: '/admin/figuras', etiqueta: 'Figuras' },
  { to: '/admin/partidas', etiqueta: 'Partidas' },
  { to: '/transmision', etiqueta: 'Transmisión' },
  { to: '/jugador', etiqueta: 'Jugador' },
  { to: '/vendedor', etiqueta: 'Vendedor', fase2: true },
]

/** Cabecera y contenedor comunes a todas las vistas. */
export function Layout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-surface/70 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:gap-6 sm:px-6">
          <Link to="/" className="flex shrink-0 items-center gap-2.5">
            <span className="grid size-9 place-items-center rounded-full bg-primary font-bold text-primary-foreground shadow-lg shadow-primary/20">
              B
            </span>
            <span className="hidden text-lg font-semibold tracking-tight sm:inline">
              Bingo
            </span>
          </Link>

          {/* Se desplaza en horizontal en vez de partirse en dos filas: la
              vista del jugador se usa desde el celular, y una cabecera que
              crece hacia abajo le come la pantalla al cartón. */}
          <nav className="-mx-1 flex items-center gap-1 overflow-x-auto px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {RUTAS.map((ruta) => (
              <NavLink
                key={ruta.to}
                to={ruta.to}
                end={ruta.exacto}
                className={({ isActive }) =>
                  cn(
                    'shrink-0 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary/15 text-primary'
                      : 'text-muted-foreground hover:bg-surface-2 hover:text-foreground',
                  )
                }
              >
                {ruta.etiqueta}
                {ruta.fase2 && (
                  <span className="ml-1.5 text-[10px] uppercase tracking-wide opacity-60">
                    F2
                  </span>
                )}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
        <Outlet />
      </main>
    </div>
  )
}
