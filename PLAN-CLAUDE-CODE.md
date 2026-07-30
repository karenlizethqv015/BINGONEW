# PLAN-CLAUDE-CODE.md — Plan Eficiente para Ejecutar con Claude Code

Este plan está pensado para que no se pierda contexto entre sesiones (Claude Code tiene ventana de contexto limitada) y para que cada sesión sea enfocada y productiva. La idea: **una sesión = una tarea de `PROGRESS.md`**, no más.

## Cómo está armado el contexto de este proyecto

- `CLAUDE.md` — se carga automáticamente al abrir el proyecto con Claude Code. Contiene lo esencial: qué es el proyecto, prioridades, stack, convenciones. Es corto a propósito.
- `docs/01...10-*.md` — el documento de visión original, dividido por tema. Claude Code NO debe leerlos todos de una vez; solo el que aplique a la tarea puntual.
- `PROGRESS.md` — el estado real del proyecto. Se lee al inicio de cada sesión y se actualiza al final.

## Paso 0 — Antes de la primera sesión

1. Sube esta carpeta completa (`CLAUDE.md`, `PROGRESS.md`, `docs/`) a la raíz del repositorio del proyecto en Claude Code.
2. Corre `/init` (skill de Claude Code) si quieres que genere un CLAUDE.md adicional autodetectado del código una vez exista código — no reemplaza este `CLAUDE.md`, lo complementa.

## Paso 1 — Sesión de scaffolding (Fase 0)

**Prompt sugerido para Claude Code:**

> Lee CLAUDE.md y PROGRESS.md. Vamos a ejecutar la Fase 0 (setup del proyecto). Crea la estructura del monorepo (backend FastAPI + frontend React/Vite/TS/Tailwind), inicializa ambos con lo mínimo para correr un "hola mundo", decide la base de datos para la demo (documenta el porqué en PROGRESS.md) y deja el proyecto listo para desarrollar. No implementes ninguna funcionalidad de negocio todavía. Al terminar, actualiza los checkboxes de la Fase 0 en PROGRESS.md.

**Por qué una sesión aparte:** el scaffolding genera mucho output (configs, boilerplate) que no aporta al diseño de negocio; conviene cerrarlo y empezar limpio para la Fase 1.

## Paso 2 — Sesiones de Fase 1 (una tarea a la vez)

Para cada una de las 9 tareas de la Fase 1 en `PROGRESS.md`, usa una sesión (o varias si la tarea es grande) con este patrón de prompt:

> Lee CLAUDE.md y PROGRESS.md. Vamos a implementar la tarea [N] de la Fase 1: [nombre de la tarea]. Consulta también [archivo específico de docs/ relevante] para el detalle funcional. Implementa de punta a punta (backend + frontend + tiempo real si aplica) antes de pasar a la siguiente tarea. Al terminar, corre lo necesario para verificar que funciona, y actualiza PROGRESS.md marcando esta tarea como completa con una línea de resumen.

**Orden recomendado y su archivo de referencia:**

1. Creación de figuras → `docs/09-modulos-desarrollo.md` + `docs/08-modelo-datos.md`
2. Selección de formas por partida → mismos archivos
3. Generación de cartones virtuales → `docs/09-modulos-desarrollo.md` + `docs/08-modelo-datos.md`
4. Balotera virtual → `docs/09-modulos-desarrollo.md` (sección "Detalle del módulo de balotera virtual")
5. Cartón del jugador con marcado automático → `docs/03-alcance-funcional-mvp.md` (sección Jugador)
6. Tablero de transmisión → `docs/03-alcance-funcional-mvp.md` (sección Pantalla de Transmisión) + `docs/04-referencia-app-anterior.md`
7. Panel de administración de partida → `docs/03-alcance-funcional-mvp.md` (sección Administrador)
8. Validación de ganadores → `docs/08-modelo-datos.md` (tabla `ganador`)
9. Pulido visual + despliegue → `docs/05-requisitos-no-funcionales.md` + `docs/06-arquitectura.md` (nota de arquitectura MVP demo)

**Por qué una tarea por sesión:** cada módulo (figuras, cartones, balotera, etc.) tiene su propia lógica de datos y UI; mezclarlos en una sola sesión larga aumenta el riesgo de que Claude Code pierda coherencia o mezcle código a medio terminar entre módulos. Cerrar cada tarea con PROGRESS.md actualizado deja un punto de retorno limpio.

## Paso 3 — Verificación antes de mostrar al cliente

Antes de la demo, corre una sesión dedicada solo a QA:

> Lee PROGRESS.md. Todas las tareas de la Fase 1 están marcadas como completas. Haz un recorrido de extremo a extremo: crear una figura, seleccionarla para una partida, generar cartones, iniciar la balotera, verificar que el tablero de transmisión y el cartón del jugador se actualizan en tiempo real, y que se dispara la notificación de bingo cuando corresponde. Reporta cualquier bug encontrado y corrígelo antes de continuar.

## Paso 4 — Fase 2 en adelante

Una vez aprobado el MVP por el cliente, repite el mismo patrón (una sesión por tarea, consultando `docs/` y actualizando `PROGRESS.md`) para las tareas de Fase 2 y luego Fase 3.

## Reglas generales para no perder contexto entre sesiones

1. **Nunca borres ni resumas `PROGRESS.md` a la fuerza** — es la memoria persistente del proyecto entre sesiones de Claude Code.
2. Si una sesión se corta o se queda sin contexto a mitad de una tarea, la siguiente sesión debe empezar con: "Lee PROGRESS.md, la tarea [N] quedó a medias, revisa qué se alcanzó a hacer en el código y termínala."
3. No le pidas a Claude Code que lea los 10 archivos de `docs/` completos en una sola sesión salvo que estés pidiendo un análisis general del proyecto — para desarrollo, apunta siempre al archivo específico.
4. Si cambias de opinión sobre el orden de prioridad, actualiza primero `PROGRESS.md` (y este archivo si aplica) y luego dale la instrucción a Claude Code — no lo dejes solo en el mensaje de chat, para que quede registrado.
