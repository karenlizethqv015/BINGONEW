import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// El backend de desarrollo (uvicorn) corre en el 8000.
const BACKEND = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],

  resolve: {
    // Alias @/ -> src/, convención de shadcn/ui.
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },

  server: {
    port: 5173,
    // El proxy hace que el frontend llame a /api y /ws con rutas relativas,
    // sin saber en qué puerto está el backend. Eso evita problemas de CORS en
    // desarrollo y, sobre todo, es lo que necesita la instalación final en LAN,
    // donde ambos se sirven desde el mismo origen (ver docs/06-arquitectura.md).
    proxy: {
      '/api': {
        target: BACKEND,
        changeOrigin: true,
      },
      '/ws': {
        target: BACKEND,
        // Sin esto el proxy no reenvía el handshake de WebSocket.
        ws: true,
      },
    },
  },
})
