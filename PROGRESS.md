# PROGRESS.md — Registro de Fases de Desarrollo

> Claude Code debe actualizar este archivo cada vez que complete una tarea: marcar el checkbox, agregar fecha y una línea breve de qué se hizo o qué decisión se tomó. No se debe reordenar la prioridad de fases sin que la usuaria lo pida.

Última actualización: 2026-07-30 (Fase 1, tarea #1 — módulo de creación de figuras — completa).

---

## Fase 0 — Setup del proyecto

- [x] Crear estructura del monorepo (`backend/`, `frontend/`). — 2026-07-30. Monorepo con `backend/` (FastAPI) y `frontend/` (Vite), `.gitignore` y `README.md` en la raíz.
- [x] Elegir e inicializar backend FastAPI + SQLAlchemy + Alembic. — 2026-07-30. FastAPI 0.141 + SQLAlchemy 2.0.51 async + Alembic 1.18. Endpoint `GET /api/health` y canal WebSocket de prueba `/ws/echo` con un `GestorConexiones` en memoria que la balotera reutilizará en la Fase 1. 3 pruebas pasando.
- [x] Elegir base de datos para la demo (SQLite vs Postgres gestionado) y documentar la decisión aquí. — 2026-07-30. **SQLite + aiosqlite**, ver bitácora abajo.
- [x] Inicializar frontend React + Vite + TypeScript + TailwindCSS. — 2026-07-30. React 19 + Vite 8 + TypeScript 6 + Tailwind 4 + shadcn/ui. Rutas por rol funcionando y proxy de `/api` y `/ws` al backend.
- [x] Definir paleta de colores / identidad visual del MVP (ver `docs/05-requisitos-no-funcionales.md`, requisito de frontend llamativo). — 2026-07-30. Paleta **"Casino nocturno"** en `frontend/src/index.css`, ver bitácora.
- [ ] Configurar despliegue de demo (frontend en Vercel/Netlify, backend en Railway/Render/Fly.io). — **Pospuesto a propósito** por decisión de la usuaria (2026-07-30): requiere cuentas propias en esos servicios. Se resuelve completo en la tarea #9 de la Fase 1, que ya contempla el despliegue.

### Cómo levantar el proyecto

Los comandos están en la sección `## Comandos` de `CLAUDE.md`. En corto: uvicorn en el 8000 y Vite en el 5173, **los dos a la vez**.

## Fase 1 — MVP a mostrar al cliente (prioridad máxima)

Orden sugerido de implementación (cada una debe funcionar de punta a punta antes de pasar a la siguiente):

- [x] **1. Módulo de creación de figuras** — cuadrícula editable tipo BINGO, guardar/nombrar patrón en catálogo. (`docs/09-modulos-desarrollo.md` #5, `docs/08-modelo-datos.md` tabla `figura`) — 2026-07-30. CRUD completo en `/api/figuras` (tabla `figura`, patrón como matriz 5x5 en JSON) y pantalla `/admin/figuras` con cuadrícula editable que se pinta arrastrando, 6 plantillas de figuras comunes, catálogo con vista previa en miniatura, y edición/borrado con confirmación. 17 pruebas nuevas de backend más 9 comprobaciones de punta a punta contra el proxy. **La cuadrícula es 5x5, no 5x25 — ver la nota de la bitácora.**
- [ ] **2. Módulo de selección de formas por partida** — elegir figuras del catálogo para la partida activa, definir tipo de premio y valor. (`docs/09-modulos-desarrollo.md` #6, tabla `partida_figura`)
- [ ] **3. Generación de cartones virtuales** — algoritmo de cartones únicos 5x5, sin duplicados dentro de la partida. (`docs/09-modulos-desarrollo.md` #7, tabla `carton`)
- [ ] **4. Balotera virtual** — sorteo aleatorio criptográficamente seguro (`secrets`), sin repetición, rangos B-I-N-G-O, emisión por WebSocket, registro en `balota_cantada`. (`docs/09-modulos-desarrollo.md` #9 y detalle de balotera virtual)
- [ ] **5. Cartón del jugador con marcado automático** — vista celular/web que tacha en tiempo real los números cantados recibidos por WebSocket. (`docs/09-modulos-desarrollo.md` #11)
- [ ] **6. Tablero de transmisión** — tablero completo de 75 números, último cantado resaltado en verde, últimas 5 balotas como "figuritas", formas de ganar vigentes con su premio. (`docs/09-modulos-desarrollo.md` #10)
- [ ] **7. Panel de administración de partida** — iniciar/pausar/finalizar sorteo, ver balotas cantadas y ganadores en tiempo real, control del cronómetro entre balotas. (`docs/03-alcance-funcional-mvp.md` sección Administrador)
- [ ] **8. Validación de ganadores** — comparar cartón vs. balotas cantadas vs. figura jugada, disparar notificación de bingo al jugador. (`docs/09-modulos-desarrollo.md` #12)
- [ ] **9. Pulido visual y despliegue final de la demo** — asegurar apariencia atractiva/profesional en las 3 vistas (admin, transmisión, jugador), responsive básico, deploy en URL pública estable para mostrar al cliente.

## Fase 2 — Después de aprobado el MVP

- [ ] Login real: admin/vendedor (usuario + contraseña, JWT).
- [ ] Login jugador por cédula real.
- [ ] CRUD de salas.
- [ ] CRUD de empleados y usuarios (separado de jugadores).
- [ ] Gestión completa de jornadas y partidas (consecutivo diario, historial).
- [ ] Módulo de ventas (vendedor): registrar comprador, vender cartones/módulos, consultar ventas.
- [ ] Concepto de módulos/paquetes de cartones (ej. "Pirámide x6") — confirmar con la usuaria si aplica igual en web o se simplifica.
- [ ] Módulo de reportes: recaudo por partida/juego/módulo, ventas por vendedor/jornada, ganadores históricos.
- [ ] Módulo de auditoría (`log_auditoria`) explotado completamente.

## Fase 3 — Futuro / fuera de alcance actual

- [ ] Definir reglas exactas de Reyes / Reyes Especiales.
- [ ] Definir reglas exactas de Progresivo / Máximo Progresivo.
- [ ] Definir reglas exactas de Loco Bingo.
- [ ] Definir reglas exactas de Acumulados (Número de Balotas, Balota Final, Bingo Salado, Múltiplo, Adicional Balotas Finales).
- [ ] Configuración de cámara(s) y transmisión de video en vivo.
- [ ] Preparación para certificación Coljuegos (GNA certificado, integración API REST, trazabilidad completa).
- [ ] Empaquetado final Docker Compose para instalación en LAN de cada sala (reemplazo del deploy web de demo).

---

## Decisiones tomadas (bitácora)

> Agregar aquí cada decisión relevante tomada durante el desarrollo, con fecha.

- 2026-07-30 — Se define que el MVP de demo se desplegará temporalmente en la web (no en LAN) solo para mostrárselo al cliente; la arquitectura LAN definitiva se retoma después de aprobado el MVP.

- 2026-07-30 — **Base de datos de la demo: SQLite + `aiosqlite`.** Motivos: (1) el entorno tiene Python 3.14, muy reciente, y los drivers compilados de PostgreSQL todavía tienen cobertura irregular de wheels, mientras que `aiosqlite` es Python puro; (2) no exige crear cuentas ni aprovisionar nada, así la Fase 1 arranca de inmediato; (3) `CLAUDE.md` indica tomar la opción más rápida de entregar y documentarla. **Para que el cambio a PostgreSQL en la Fase 2 sea solo cambiar `DATABASE_URL`**, los modelos deben seguir las reglas de compatibilidad escritas en `backend/README.md` (tipo `JSON` genérico y nunca `JSONB`, `DateTime(timezone=True)`, nada de SQL crudo específico de un motor). `render_as_batch=True` ya está activo en `alembic/env.py` — no quitarlo.

- 2026-07-30 — **Identidad visual: paleta "Casino nocturno"** (elegida por la usuaria entre tres propuestas). Oscura: fondo azul-noche `#0B1120`, acentos dorados `#F5B301` y verde esmeralda `#10B981`. Se eligió por contraste: se lee bien tanto en el monitor del administrador como proyectada en el TV de la sala. Vive completa en `frontend/src/index.css` como tokens; los componentes no deben usar colores sueltos de Tailwind.

- 2026-07-30 — **Componentes: shadcn/ui** (elegido por la usuaria), como sugería `SKILLS-RECOMENDADAS.md`. El CLI oficial no se ejecutó porque el proyecto usa Tailwind 4 + TypeScript 6 + Vite 8 y la detección automática es frágil; se escribieron a mano `button` y `card` siguiendo exactamente la convención de shadcn, y se dejó `components.json` configurado para que `npx shadcn@latest add <componente>` funcione de aquí en adelante.

- 2026-07-30 — **El despliegue de la demo se pospone a la tarea #9 de la Fase 1** (decisión de la usuaria). No se crearon archivos de despliegue en la Fase 0. Nota para cuando se retome: el frontend ya llama al backend con rutas relativas (`/api`, `/ws`), así que servir ambos desde el mismo origen no requiere cambios de código.

- 2026-07-30 — **Corrección al documento de visión: las figuras se diseñan sobre una cuadrícula de 5x5, no de "5x25".** `docs/03-alcance-funcional-mvp.md` y `docs/08-modelo-datos.md` dicen "matriz 5x25 tipo BINGO", pero ambos textos salen de la misma frase del documento original, así que es un solo dato y no dos confirmaciones. 5x25 son 125 celdas, que no corresponde ni al cartón (5x5 = 25) ni al tablero de 75 balotas (5x15); además `carton.numeros` sí está definido como matriz 5x5, y la validación de ganadores de la tarea #8 tiene que comparar la figura celda a celda contra el cartón. Confirmado con la usuaria: **5x5**. Los archivos de `docs/` se dejaron sin tocar por ser transcripción del documento original; esta bitácora es la fuente correcta.

- 2026-07-30 — **La casilla libre (centro, fila 2 columna 2) puede incluirse o no en una figura.** No se fuerza a estar marcada: "cuatro esquinas", por ejemplo, no la incluye. Cuando se implemente la validación de ganadores (tarea #8), si una figura la incluye debe darse por cumplida automáticamente, sin que salga ninguna balota. Las constantes están en `backend/app/dominio/bingo.py` y `frontend/src/lib/bingo.ts` — si cambia una, hay que cambiar las dos.

- 2026-07-30 — **Borrado de figuras: es borrado real, no lógico.** Sirve mientras el catálogo no esté referenciado por nada. En la tarea #2, al crear `partida_figura`, hay que impedir borrar una figura ya jugada o pasar a borrado lógico, o se rompe el historial de ganadores. Queda anotado en el docstring del endpoint.

- 2026-07-30 — **Las pruebas corren contra una base de datos propia en memoria**, no contra `bingo.db`, sobreescribiendo la dependencia `get_db`. El esquema se crea y se destruye en cada prueba, así que el orden en que corran no cambia el resultado.

- 2026-07-30 — **Aviso de seguridad de `react-router` que se decidió NO atender:** `npm audit` reporta `GHSA-qwww-vcr4-c8h2` (severidad alta) en `react-router` 7.18.2. Aplica solo al **modo RSC** con server actions; esta aplicación es una SPA puramente de cliente, así que no la afecta. Además, la versión instalada es la última publicada y la corrección que sugiere npm (7.11.0) es *anterior*. Revisar cuando salga una versión parcheada.
