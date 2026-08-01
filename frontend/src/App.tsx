import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/Layout'
import { Admin } from '@/pages/Admin'
import { ConfigurarPartida } from '@/pages/ConfigurarPartida'
import { Figuras } from '@/pages/Figuras'
import { Inicio } from '@/pages/Inicio'
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
        <Route element={<Layout />}>
          <Route index element={<Inicio />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/admin/figuras" element={<Figuras />} />
          <Route path="/admin/partidas" element={<Partidas />} />
          <Route path="/admin/partidas/:id" element={<ConfigurarPartida />} />
          <Route path="/transmision" element={<Transmision />} />
          <Route path="/jugador" element={<Jugador />} />
          <Route path="/vendedor" element={<Vendedor />} />
          {/* Cualquier ruta desconocida vuelve a la portada. */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
