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
- `docs/11-avisos-y-validacion-de-ganadores.md`

**Regla de oro de contexto:** no cargues los 10 archivos de `docs/` completos si la tarea de la sesión solo necesita 1 o 2. Lee `PROGRESS.md` primero para saber en qué fase/tarea está el proyecto, y de ahí decide qué archivo(s) de `docs/` son relevantes para esa tarea puntual.

## Otros archivos de la raíz (léanse cuando apliquen)

- `DESPLIEGUE.md` — cómo poner la demo en una URL pública, y por qué el backend sirve también el frontend (un solo origen, igual que la instalación final en la sala).
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
- **Base de datos:** los dos motores vienen instalados y el que se usa lo decide `DATABASE_URL`. **SQLite** (`aiosqlite`) por defecto para desarrollo y pruebas; **PostgreSQL** (`asyncpg`) en la demo desplegada y en la instalación final en LAN. La cadena se pega tal como la dé el proveedor: se normaliza sola en `backend/app/config.py`.
- **Tiempo real:** WebSocket nativo o socket.io-client, un endpoint por partida.
- **Despliegue MVP demo:** **una sola imagen Docker** — el backend sirve también el frontend compilado, así que todo va en un origen. No son dos servicios: separarlos obligaría a escribir el host del backend en el frontend, que es justo lo que prohíbe la regla 1 de abajo. Es además la misma forma que tendrá la instalación final en LAN. Ver `DESPLIEGUE.md`; esto corrige lo que dice `docs/06-arquitectura.md`.

### Rutas del frontend por rol

Convención fija, no inventar otras en cada sesión:

- `/admin` — catálogo de figuras y ajustes básicos del juego (Fase 1 sin login). Protegido por `ADMIN_CLAVE`.
- `/operador` — control de la jornada: partidas, balotera y cartones (Fase 1 sin login). Protegido por `OPERADOR_CLAVE`, una clave distinta de la de administración — ver la regla 6 de dominio más abajo.
- `/transmision` — pantalla pública para proyectar en la sala. **Sin login**, solo lectura, se alimenta del mismo WebSocket que emite la balotera.
- `/jugador` — cartón(es) del jugador con marcado automático (Fase 1 sin login; login por cédula en Fase 2).
- `/vendedor` — módulo de ventas. **Fase 2**, no implementar todavía.

El backend expone **un endpoint WebSocket por partida**; todas las vistas en tiempo real se conectan a ese mismo endpoint y reaccionan al mismo evento de balota.

## Comandos

Todos los comandos del backend usan el intérprete del entorno virtual directamente (`.venv\Scripts\python.exe -m ...`), sin activar el venv: así funcionan igual desde cualquier shell y no dependen de que alguien haya corrido `Activate.ps1`.

### Backend (desde `backend/`)

```powershell
# Instalación inicial (una sola vez)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Levantar la API en desarrollo — http://127.0.0.1:8000 (docs en /docs)
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Migraciones
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "descripcion"
.\.venv\Scripts\python.exe -m alembic downgrade -1

# Pruebas
.\.venv\Scripts\python.exe -m pytest                                                 # toda la suite
.\.venv\Scripts\python.exe -m pytest tests/test_health.py                            # un archivo
.\.venv\Scripts\python.exe -m pytest tests/test_health.py::test_health_responde_ok    # UN SOLO TEST
.\.venv\Scripts\python.exe -m pytest -k websocket                                    # por nombre
.\.venv\Scripts\python.exe -m pytest -m lento -s                                     # PRUEBA DE CARGA (5000 cartones)
```

La prueba de carga no corre con la suite normal: genera 5000 cartones y canta las
75 balotas. El `-s` es lo que hace que imprima los tiempos reales por balota.

### La suite contra PostgreSQL (desde la raíz del repositorio)

```powershell
docker compose up -d postgres
cd backend
$env:TEST_DATABASE_URL = "postgresql+asyncpg://bingo:bingo@localhost:5432/bingo"
.\.venv\Scripts\python.exe -m pytest
Remove-Item Env:\TEST_DATABASE_URL     # volver a SQLite
```

Tarda unos dos minutos y medio en vez de quince segundos, porque crea y destruye
el esquema en cada prueba. **Vale la pena antes de tocar el despliegue**: es lo
que descubre las diferencias entre motores aquí y no en el servidor. Si el 5432
está ocupado, `$env:PUERTO_POSTGRES = "5433"` antes del `docker compose up`.

### Frontend (desde `frontend/`)

```powershell
npm install         # instalación inicial
npm run dev         # http://localhost:5173 (proxy de /api y /ws al backend)
npm run dev:lan     # igual, pero accesible desde otros equipos de la red
npm run build       # compila TypeScript y genera dist/
npm run lint        # oxlint
npm run preview     # sirve el build de producción
```

### Demo desde el celular (misma red WiFi)

Para enseñarle el MVP a alguien con su propio teléfono —el cartón marcándose solo mientras se cantan balotas desde el PC—:

1. `npm run dev:lan` en vez de `npm run dev`.
2. Sacar la IP del equipo: `ipconfig` (la "Dirección IPv4" del adaptador WiFi).
3. Abrir el puerto una sola vez, en PowerShell **como administrador**:
   ```powershell
   New-NetFirewallRule -DisplayName "Bingo dev" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
   ```
4. El invitado entra a `http://<ip-del-equipo>:5173/jugador`.

**El backend se queda en `127.0.0.1` y no hay que abrir el puerto 8000.** El celular solo habla con Vite, que reenvía al backend desde el mismo equipo. Esto funciona sin tocar código gracias a la regla de no escribir nunca host ni puerto: el WebSocket se arma con `window.location.host`, así que se conecta solo a la IP correcta. Es además un ensayo de la instalación final en la sala.

**Para trabajar hay que tener los dos corriendo a la vez** (uvicorn en 8000 y Vite en 5173): el frontend llama a `/api` y `/ws` con rutas relativas y el proxy de Vite las reenvía. Si una vista muestra "sin conexión", casi siempre es que falta levantar uvicorn.

## Convenciones del código (establecidas en la Fase 0)

Cuatro reglas que no son evidentes leyendo el código y que cuesta caro descubrir tarde:

1. **Nunca escribir host ni puerto en el frontend.** Todas las llamadas van a rutas relativas (`/api/...`, `/ws/...`). En desarrollo las resuelve el proxy de Vite; en la instalación final en LAN, frontend y backend comparten origen. Un `http://localhost:8000` escrito a mano rompe el despliegue en la sala.
2. **Ningún color suelto de Tailwind.** Nada de `bg-slate-800` ni `text-yellow-400`: todo color sale de los tokens de `frontend/src/index.css` (`bg-surface`, `text-primary`, `text-success`…). Es lo que mantiene la identidad visual coherente y permite ajustarla desde un solo archivo.
3. **Alembic solo ve los modelos importados en `backend/app/models/__init__.py`.** Si un modelo nuevo no se importa ahí, `--autogenerate` produce una migración **vacía sin dar ningún error**. Revisar siempre el archivo generado antes de aplicarlo.
4. **Los modelos deben seguir siendo compatibles con PostgreSQL** aunque la demo corra en SQLite: tipo `JSON` genérico (nunca `JSONB`), `DateTime(timezone=True)`, y nada de SQL crudo específico de un motor. El detalle está en `backend/README.md`.
5. **La validación de ganadores trabaja con máscaras de bits precalculadas, no recorriendo cartones.** Las salas grandes juegan con 5000 cartones: qué balotas exige cada forma sobre cada cartón se calcula **una vez por partida** y se guarda en `app/servicios/ganadores.py`, con un sello que lo invalida solo si cambian los cartones o los patrones. Si alguien vuelve a meter un `numeros_requeridos` dentro del bucle por balota, la partida pasa de 22 ms a más de 130 ms por balota y bloquea los WebSockets de toda la sala. Hay una prueba de carga que lo vigila (`pytest -m lento`).
6. **Las claves de administración y operador (`ADMIN_CLAVE`, `OPERADOR_CLAVE`) NO son el login de la Fase 2.** Son dos claves compartidas independientes que protegen lo que modifica, cada una con su alcance: `ADMIN_CLAVE` el catálogo de figuras (`figuras.py`), `OPERADOR_CLAVE` partidas, balotera y cartones (`partidas.py`, `balotas.py`, `cartones.py`). Se aplican por método HTTP en `app/seguridad.py`, no ruta por ruta. Las consultas y el WebSocket quedan abiertos a propósito: `/transmision` y `/jugador` son pantallas del público. Vacías = todo abierto (desarrollo y LAN). El frontend manda las dos claves guardadas en cada petición (`lib/http.ts`); el backend responde en qué cabecera (`X-Clave-Requerida`) hacía falta cuál, así el frontend no tiene que adivinar del mensaje de error qué diálogo abrir.

## Reglas de dominio que no se negocian (bingo de 75 bolas)

Estas reglas son las más fáciles de equivocar y las más caras de corregir después. Aplican aunque no se haya leído `docs/09-modulos-desarrollo.md`:

- Rangos por letra: **B** 1–15, **I** 16–30, **N** 31–45, **G** 46–60, **O** 61–75.
- Sorteo **sin reemplazo**: nunca se repite una balota dentro de la misma partida.
- Usar `secrets` (generador criptográficamente seguro), **nunca** `random` — deja abierto el camino a una futura certificación GNA/Coljuegos.
- Toda balota sorteada se registra en `balota_cantada` con su orden y timestamp, venga de balotera virtual o física.
- El evento WebSocket de balota debe ser **idéntico** para fuente virtual y física: cuando se integre la balotera real, solo cambia la fuente, no el resto del sistema.
- El sorteo termina al agotarse las 75 balotas, o cuando el administrador lo finaliza a mano.
- **Un bingo DETIENE el sorteo:** al detectarse un ganador la partida se **pausa sola**, para que el encargado pueda acercarse a la persona y acordar el premio. Se pausa, no se finaliza: las demás formas siguen en juego y el administrador reanuda cuando quiera. Agotar las 75 balotas manda sobre la pausa (una partida finalizada no se despausa). *(Esta regla sustituye a la contraria, vigente hasta el 2026-08-05; ver la bitácora de `PROGRESS.md`.)*
- **Una forma ganada se cierra:** solo ganan los cartones que la completan en la MISMA balota, y comparten el premio. Quien la complete después llegó tarde. Sin esta regla, con las 75 balotas fuera todos los cartones habrían ganado todo.
- **La casilla libre no exige ninguna balota:** una figura que la incluya exige una balota menos que celdas tiene. Una figura formada solo por la casilla libre se ignora.
- **Quién ganó lo decide siempre el backend**, nunca el navegador: hay dinero detrás. El marcado del cartón sí se resuelve en el cliente, que es otra cosa. Detalle completo en `docs/11-avisos-y-validacion-de-ganadores.md`.

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
