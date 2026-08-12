# 02 — Roles y Actores

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 2. No omite información del original.

| Rol | Descripción | Acceso |
|---|---|---|
| **Administrador** | Crea/configura salas y partidas, diseña formas de ganar (herramienta de figuras), elige qué formas juegan en cada partida y su precio, controla el sorteo de balotas (con cronómetro/tiempo de jugada), gestiona usuarios/empleados, ve reportes | Login con usuario/contraseña |
| **Vendedor** | Registra compradores (nombre + cédula), vende cartones/módulos, consulta cartones vendidos | Login con usuario/contraseña |
| **Pantalla de Transmisión** | Vista pública para proyectar en la sala: tablero completo, números cantados, últimas 5 balotas, formas de ganar vigentes. No es la vista del jugador | Sin login (pantalla fija) o acceso restringido de solo lectura |
| **Jugador/Cliente** | Desde su celular: ingresa con cédula, ve su propio cartón con marcado automático de números cantados, recibe aviso de bingo | Login con cédula (sin contraseña o con PIN simple) |

## Nota de priorización MVP

Para el primer entregable de demo, el **login real (usuario/contraseña, cédula)** se pospone a la fase 2 (ver `PROGRESS.md`). En el MVP de demo se puede simular el rol activo (ej. selector simple o rutas directas `/admin`, `/transmision`, `/jugador`) para poder mostrar el flujo funcional sin bloquear el desarrollo en autenticación.

## Nota post-MVP: el rol Administrador se dividió en dos (2026-08-12)

La tabla de arriba es transcripción del documento de visión original y se deja
sin tocar por eso (mismo criterio que la nota del 2026-07-30 sobre la
cuadrícula 5x25 en `docs/03-alcance-funcional-mvp.md`: un documento fuente no
se edita a mano, se anota). Lo que cambió de verdad, tras la primera demo:

El cliente pidió separar lo que la tabla junta bajo "Administrador" en dos
roles con acceso independiente (sin login real todavía, ver `PROGRESS.md`
Fase 1.6):

- **Administrador** — se queda con "diseña formas de ganar" (el catálogo de
  figuras). Ruta `/admin`, clave `ADMIN_CLAVE`.
- **Operador** — se queda con "elige qué formas juegan en cada partida y su
  precio" y "controla el sorteo de balotas", más la generación de cartones.
  Ruta `/operador`, clave `OPERADOR_CLAVE` (independiente de la de
  administración). Es quien de verdad toca la aplicación constantemente
  durante una jornada.

"Gestiona usuarios/empleados" y "ve reportes" siguen sin implementarse: son de
la Fase 2, igual que en la tabla original.
