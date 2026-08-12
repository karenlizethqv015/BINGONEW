import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/Layout'
import { Admin } from '@/pages/Admin'
import { Balotera } from '@/pages/Balotera'
import { CartonesPartida } from '@/pages/CartonesPartida'
import { ConfigurarPartida } from '@/pages/ConfigurarPartida'
import { Figuras } from '@/pages/Figuras'
import { Inicio } from '@/pages/Inicio'
import { Operador } from '@/pages/Operador'
import { Partidas } from '@/pages/Partidas'
import { Jugador } from '@/pages/Jugador'
import { Transmision } from '@/pages/Transmision'
import { Vendedor } from '@/pages/Vendedor'

/**
 * Rutas de la aplicación.
 *
 * La convención por rol está fijada en CLAUDE.md y no debe cambiarse sin
 * actualizar ese archivo. En la Fase 1 no hay login: se entra directo a cada
 * vista.
 */
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* La transmisión va FUERA del Layout: se proyecta en el televisor de
            la sala y debe ocupar la pantalla entera, sin la barra de
            navegación de la aplicación. */}
        <Route path="/transmision" element={<Transmision />} />

        <Route element={<Layout />}>
          <Route index element={<Inicio />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/admin/figuras" element={<Figuras />} />
          <Route path="/operador" element={<Operador />} />
          <Route path="/operador/partidas" element={<Partidas />} />
          <Route path="/operador/partidas/:id" element={<ConfigurarPartida />} />
          <Route path="/operador/partidas/:id/cartones" element={<CartonesPartida />} />
          <Route path="/operador/partidas/:id/balotera" element={<Balotera />} />
          <Route path="/jugador" element={<Jugador />} />
          <Route path="/vendedor" element={<Vendedor />} />
          {/* Cualquier ruta desconocida vuelve a la portada. */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
