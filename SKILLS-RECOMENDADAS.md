# SKILLS-RECOMENDADAS.md — Uso Eficiente de Claude Code para este Proyecto

Recomendaciones concretas de skills/comandos/prácticas de Claude Code para este proyecto de bingo, pensadas para aprovechar bien la ventana de contexto y avanzar rápido hacia el MVP.

## Skills / comandos a usar

- **`/init`** — úsalo justo después del scaffolding (Paso 1 de `PLAN-CLAUDE-CODE.md`), una vez ya exista código. Genera un CLAUDE.md complementario autodetectado (estructura de carpetas, comandos de build/test) que convive con el `CLAUDE.md` de negocio que ya te dejé armado. No lo uses antes de tener código, porque no detectará nada útil.
- **Modo plan / "Plan" agent** — antes de implementar cada módulo grande de la Fase 1 (especialmente balotera virtual y validación de ganadores, que tienen lógica de reglas más delicada), pide primero un plan de implementación en modo plan antes de escribir código. Reduce el riesgo de que Claude Code tome atajos incorrectos en las reglas del bingo (rangos B-I-N-G-O, no repetición de balotas, etc.).
- **Subagente `Explore`** — útil en sesiones de Fase 2 en adelante, cuando el código ya sea grande y necesites ubicar dónde vive cierta lógica (ej. "¿dónde está el endpoint que genera cartones?") sin cargar todo el repo en el contexto principal.
- **`review` (revisión de PR/diff)** — antes de dar por cerrada cada tarea de `PROGRESS.md`, corre este skill sobre el diff de esa tarea para detectar errores antes de pasar a la siguiente. Barato de correr y evita arrastrar bugs de un módulo a otro.
- **`security-review`** — resérvalo para la Fase 2, cuando se implemente login real (JWT) y manejo de cédulas/datos personales. No es prioritario en la Fase 1 (sin login real), pero es obligatorio antes de que el sistema maneje credenciales o datos de jugadores reales.
- **`skill-creator`** — si notas que le repites a Claude Code el mismo tipo de instrucción en varias sesiones (ej. "genera un cartón de bingo válido con estas reglas" o "verifica que el patrón de una figura sea válido en la cuadrícula 5x5"), vale la pena convertirlo en un skill propio del proyecto para no reescribirlo cada vez.

## Prácticas de manejo de ventana de contexto (además de la división de docs/)

1. **Una tarea de `PROGRESS.md` por sesión.** Ya está reflejado en `PLAN-CLAUDE-CODE.md` — es la práctica más importante para no perder contexto ni mezclar trabajo a medias.
2. **Cierra cada sesión con `PROGRESS.md` actualizado.** Es tu punto de recuperación: si la sesión se corta, la siguiente retoma leyendo ahí, no re-explicando todo el proyecto de nuevo.
3. **No pegues el documento de visión completo en el chat.** Ya está dividido en `docs/`; referencia el archivo puntual en el prompt (ej. "consulta docs/09-modulos-desarrollo.md").
4. **Usa `CLAUDE.md` como la única fuente de "reglas globales".** Si una regla de negocio cambia (ej. cambias el orden de prioridad), edita `CLAUDE.md` y/o `PROGRESS.md` primero, no lo dejes solo dicho en un mensaje de chat que se puede perder.
5. **Verificación con subagente para tareas críticas.** Para la balotera virtual y la validación de ganadores (son las que tienen reglas más estrictas: no repetir balotas, rangos correctos, detección exacta de patrón ganador), pide una verificación con un agente aparte (o el skill `review`) antes de marcar la tarea como completa en `PROGRESS.md`.

## Sobre el frontend "llamativo" para la demo

- Pide explícitamente a Claude Code que use un sistema de diseño consistente (paleta de colores definida, tipografía, espaciado) desde la Fase 0, no colores por defecto de Tailwind sin criterio.
- Para el tablero de transmisión y el cantador, vale la pena pedir explícitamente animaciones sutiles (ej. la balota que aparece "rebotando", el número que se tacha con una transición) — es lo que más impacto visual da en la demo y no es costoso de implementar con Tailwind + CSS transitions.
- Si quieres acelerar el diseño visual, puedes pedirle a Claude Code que se apoye en componentes prearmados de shadcn/ui (compatible con el stack recomendado) en vez de diseñar cada componente desde cero.
