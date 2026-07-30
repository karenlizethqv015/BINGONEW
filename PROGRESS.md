# PROGRESS.md — Registro de Fases de Desarrollo

> Claude Code debe actualizar este archivo cada vez que complete una tarea: marcar el checkbox, agregar fecha y una línea breve de qué se hizo o qué decisión se tomó. No se debe reordenar la prioridad de fases sin que la usuaria lo pida.

Última actualización: 2026-07-30 (creación del plan inicial, ninguna tarea de código empezada aún).

---

## Fase 0 — Setup del proyecto

- [ ] Crear estructura del monorepo (`backend/`, `frontend/`).
- [ ] Elegir e inicializar backend FastAPI + SQLAlchemy + Alembic.
- [ ] Elegir base de datos para la demo (SQLite vs Postgres gestionado) y documentar la decisión aquí.
- [ ] Inicializar frontend React + Vite + TypeScript + TailwindCSS.
- [ ] Definir paleta de colores / identidad visual del MVP (ver `docs/05-requisitos-no-funcionales.md`, requisito de frontend llamativo).
- [ ] Configurar despliegue de demo (frontend en Vercel/Netlify, backend en Railway/Render/Fly.io).

## Fase 1 — MVP a mostrar al cliente (prioridad máxima)

Orden sugerido de implementación (cada una debe funcionar de punta a punta antes de pasar a la siguiente):

- [ ] **1. Módulo de creación de figuras** — cuadrícula editable tipo BINGO, guardar/nombrar patrón en catálogo. (`docs/09-modulos-desarrollo.md` #5, `docs/08-modelo-datos.md` tabla `figura`)
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
