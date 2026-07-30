# CLAUDE.md — Plataforma Web de Bingo (instrucciones persistentes del proyecto)

Este archivo es el contexto que Claude Code debe leer **al inicio de cada sesión** de trabajo en este repositorio. Contiene lo que no debe olvidarse aunque cambie la ventana de contexto entre sesiones.

## Qué es este proyecto

Aplicación web para administrar jornadas de bingo en vivo (venta de cartones virtuales, sorteo de balotas, tablero de transmisión, cartón del jugador con marcado automático, panel de administración). Visión final: on-premise en LAN sin internet, multi-sala. Contexto completo y detallado en la carpeta `docs/` (dividido por tema, léase bajo demanda, no todo de una vez):

- `docs/01-vision-general.md`
- `docs/02-roles-actores.md`
- `docs/03-alcance-funcional-mvp.md`
- `docs/04-referencia-app-anterior.md`
- `docs/05-requisitos-no-funcionales.md`
- `docs/06-arquitectura.md`
- `docs/07-coljuegos-futuro.md`
- `docs/08-modelo-datos.md`
- `docs/09-modulos-desarrollo.md`
- `docs/10-proximos-pasos.md`

**Regla de oro de contexto:** no cargues los 10 archivos de `docs/` completos si la tarea de la sesión solo necesita 1 o 2. Lee `PROGRESS.md` primero para saber en qué fase/tarea está el proyecto, y de ahí decide qué archivo(s) de `docs/` son relevantes para esa tarea puntual.

## Otros archivos de la raíz (léanse cuando apliquen)

- `PROGRESS.md` — estado real del proyecto: qué está hecho, qué sigue, y bitácora de decisiones. **Se lee al inicio de cada sesión y se actualiza al final.** Es la memoria persistente entre sesiones; nunca borrarlo ni resumirlo a la fuerza.
- `PLAN-CLAUDE-CODE.md` — cómo trabajar el proyecto sesión por sesión (patrón "una tarea de `PROGRESS.md` = una sesión") y qué archivo de `docs/` corresponde a cada tarea de la Fase 1.
- `SKILLS-RECOMENDADAS.md` — qué skills de Claude Code usar y cuándo. En particular: **usar modo plan antes de implementar la balotera virtual y la validación de ganadores** (son las de reglas más delicadas), y correr `review` sobre el diff antes de marcar una tarea como completa.

## Prioridad de negocio (léase antes de escribir código)

El cliente necesita ver un **MVP funcional y visualmente atractivo cuanto antes**, no el producto completo. El orden de desarrollo NO es el orden del documento de visión original — es este:

**Fase 1 (prioridad máxima, es lo que se le muestra al cliente primero):**
1. Módulo de creación de figuras (catálogo de formas de ganar, cuadrícula editable).
2. Módulo de selección de formas de ganar por partida (elegir cuáles juegan + premio).
3. Generación de cartones virtuales.
4. Balotera virtual (sorteo aleatorio, reglas de bingo de 75 bolas, WebSocket en tiempo real).
5. Cartón del jugador con marcado automático de números cantados.
6. Tablero de transmisión (números cantados, último resaltado en verde, últimas 5 balotas, formas vigentes).
7. Panel de administración de la partida (iniciar/pausar/finalizar, ver estado en tiempo real).
8. Validación de ganadores (necesaria para que el aviso de bingo funcione en el cartón del jugador).
9. Frontend con diseño atractivo y profesional, desplegado en una URL web pública para demo.

**Fase 2 (después de aprobado el MVP):** login real (admin/vendedor por usuario-contraseña, jugador por cédula), gestión de salas/jornadas/partidas completa, módulo de ventas (vendedor), módulo de empleados/usuarios, reportes, auditoría, paquetes/módulos de cartones.

**Fase 3 (futuro, fuera de alcance por ahora):** Reyes/Reyes Especiales, Progresivo, Loco Bingo, Acumulados, cámara(s) y video en vivo, certificación Coljuegos.

El detalle de fases y su estado actual vive en `PROGRESS.md` — **actualízalo después de completar cada tarea**, no lo dejes desactualizado.

## Stack técnico

- **Backend:** FastAPI (Python), SQLAlchemy 2.0 + Alembic, Pydantic, WebSockets nativos.
- **Frontend:** React + Vite + TypeScript + TailwindCSS. Diseño desktop-first pero razonablemente responsivo. Debe verse profesional y moderno (no un prototipo gris de wireframe) — es lo que se le muestra al cliente.
- **Base de datos:** PostgreSQL en producción final (LAN). Para el MVP de demo desplegado en web, puede usarse Postgres gestionado (Railway/Render/Supabase) o SQLite si acelera la entrega — decisión a tomar en la sesión de scaffolding, documentar la elección en `PROGRESS.md`.
- **Tiempo real:** WebSocket nativo o socket.io-client, un endpoint por partida.
- **Despliegue MVP demo:** frontend en Vercel/Netlify, backend en Railway/Render/Fly.io (o equivalente). La versión final de producción es Docker Compose corriendo en LAN sin internet — no confundir ambos entornos, ver `docs/06-arquitectura.md`.

### Rutas del frontend por rol

Convención fija, no inventar otras en cada sesión:

- `/admin` — panel de administración de la partida (Fase 1 sin login).
- `/transmision` — pantalla pública para proyectar en la sala. **Sin login**, solo lectura, se alimenta del mismo WebSocket que emite la balotera.
- `/jugador` — cartón(es) del jugador con marcado automático (Fase 1 sin login; login por cédula en Fase 2).
- `/vendedor` — módulo de ventas. **Fase 2**, no implementar todavía.

El backend expone **un endpoint WebSocket por partida**; todas las vistas en tiempo real se conectan a ese mismo endpoint y reaccionan al mismo evento de balota.

## Comandos

> ⚠️ Pendiente: todavía no existe código. **La sesión que ejecute la Fase 0 (scaffolding) debe llenar esta sección** con los comandos reales antes de cerrar: levantar backend (uvicorn), levantar frontend (Vite), migraciones (Alembic), correr la suite de tests y correr **un solo test**, y lint/format si se configuran. Sin esto, cada sesión futura pierde tiempo redescubriéndolos.

## Reglas de dominio que no se negocian (bingo de 75 bolas)

Estas reglas son las más fáciles de equivocar y las más caras de corregir después. Aplican aunque no se haya leído `docs/09-modulos-desarrollo.md`:

- Rangos por letra: **B** 1–15, **I** 16–30, **N** 31–45, **G** 46–60, **O** 61–75.
- Sorteo **sin reemplazo**: nunca se repite una balota dentro de la misma partida.
- Usar `secrets` (generador criptográficamente seguro), **nunca** `random` — deja abierto el camino a una futura certificación GNA/Coljuegos.
- Toda balota sorteada se registra en `balota_cantada` con su orden y timestamp, venga de balotera virtual o física.
- El evento WebSocket de balota debe ser **idéntico** para fuente virtual y física: cuando se integre la balotera real, solo cambia la fuente, no el resto del sistema.
- El sorteo termina al agotarse las 75 balotas, o antes si ya se cumplió la condición de ganador de la figura en juego.

## Convenciones de trabajo para Claude Code

1. Antes de empezar cualquier tarea, lee `PROGRESS.md` para saber qué está hecho y qué sigue.
2. Trabaja **una tarea/fase a la vez**. No adelantes funcionalidad de Fase 2 o Fase 3 mientras la Fase 1 no esté completa y funcionando de punta a punta.
3. Al terminar una tarea, actualiza el checkbox correspondiente en `PROGRESS.md` con fecha y una línea de qué se hizo.
4. No implementes login/auth real, ni CRUD de salas/jornadas/usuarios, ni reportes, hasta que la Fase 1 esté aprobada — usa rutas directas o datos simulados/seed donde haga falta para no bloquear la demo.
5. El modelo de datos completo está en `docs/08-modelo-datos.md`; para la Fase 1 basta con las entidades mínimas ahí señaladas (figura, partida_figura simplificada, partida, carton, balota_cantada, ganador).
6. Prioriza que cada feature de la Fase 1 funcione de extremo a extremo (con datos reales viajando por WebSocket) antes de pulir detalles visuales menores.
7. Cuida el diseño visual: paleta de colores atractiva, tipografía cuidada, animaciones sutiles al cantar balotas y marcar números — esto es parte del MVP, no un "nice to have".
8. Si una decisión de arquitectura no está clara (ej. SQLite vs Postgres gestionado para la demo), toma la opción más rápida de entregar y documenta la decisión y el motivo en `PROGRESS.md`, no te quedes bloqueado preguntando.

## Qué NO hacer en la Fase 1

- No implementar Reyes, Progresivo, Loco Bingo, Acumulados, ni cámaras/video.
- No implementar auditoría (`log_auditoria`) todavía, salvo que sea trivial de dejar como tabla vacía.
- No optimizar para certificación Coljuegos (eso es solo una nota de diseño a futuro, ver `docs/07-coljuegos-futuro.md`).
