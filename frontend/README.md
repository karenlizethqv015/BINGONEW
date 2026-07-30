# Frontend — Plataforma Web de Bingo

React 19 + Vite 8 + TypeScript + TailwindCSS 4 + shadcn/ui.

```powershell
npm install
npm run dev      # http://localhost:5173
npm run build
npm run lint
```

Necesita el backend corriendo en el 8000 (ver `backend/README.md`).

## Sistema de diseño — "Casino nocturno"

La paleta vive en un solo lugar: `src/index.css`. Fondo azul-noche, acentos
dorados y verde esmeralda.

**Regla:** no usar colores sueltos de Tailwind (`bg-slate-800`,
`text-yellow-400`). Todo color debe salir de un token:

| Token | Uso |
|---|---|
| `background` | fondo de la aplicación |
| `surface` / `surface-2` | paneles, tarjetas, filas alternas |
| `primary` | dorado: balotas, premios, acción principal |
| `success` | **verde del último número cantado** (requisito funcional) |
| `destructive` | errores |
| `muted-foreground` | texto secundario |

`success` no es decorativo: es el verde con el que el tablero de transmisión
resalta el último número cantado (ver `docs/03-alcance-funcional-mvp.md`).

La utilidad `.animate-balota` da la animación de entrada de una balota, y
respeta `prefers-reduced-motion`.

**Tipografía:** por ahora el stack del sistema. Al autohospedar una tipografía
display para los números, debe ir **dentro del repositorio, no por CDN de Google
Fonts** — la instalación final corre en LAN sin internet.

## Componentes

Convención shadcn/ui: los componentes viven en `src/components/ui/` y son código
propio, no una dependencia. Se pueden agregar más con:

```powershell
npx shadcn@latest add dialog table input
```

Hay que revisar que lo que genere el CLI use los tokens de la paleta y no los
colores por defecto.

## Conexión con el backend

Todas las llamadas usan **rutas relativas** (`/api/...`, `/ws/...`) desde
`src/lib/api.ts`. En desarrollo las resuelve el proxy de `vite.config.ts`; en la
instalación en LAN, frontend y backend comparten origen.

Por eso **no hay archivo `.env` en el frontend**: no hace falta ninguna variable,
y escribir un host o puerto a mano rompería el despliegue en la sala.

## Rutas

| Ruta | Vista | Estado |
|---|---|---|
| `/` | Portada con atajos | Fase 0 |
| `/admin` | Administración de la partida | Fase 1, tarea #7 |
| `/transmision` | Pantalla pública de la sala | Fase 1, tarea #6 |
| `/jugador` | Cartón con marcado automático | Fase 1, tarea #5 |
| `/vendedor` | Módulo de ventas | Fase 2 |

## Nota sobre `npm audit`

`npm audit` reporta un aviso alto en `react-router`
([GHSA-qwww-vcr4-c8h2](https://github.com/advisories/GHSA-qwww-vcr4-c8h2)) que
aplica **solo al modo RSC** con server actions. Esta aplicación es una SPA
puramente de cliente, así que no la afecta. Además, la versión instalada
(7.18.2) es la última publicada y la "corrección" que sugiere npm (7.11.0) es
anterior. Revisar de nuevo cuando salga una versión con el parche.
