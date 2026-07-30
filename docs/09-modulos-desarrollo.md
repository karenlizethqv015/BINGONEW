# 09 — Lista de Módulos a Desarrollar

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 9. No omite información del original.
>
> ⚠️ Esta es la lista **completa** de módulos del producto final. El **orden real de construcción** (qué se hace primero) está en `PROGRESS.md`, priorizado según lo que la usuaria necesita mostrarle al cliente primero.

1. **Módulo de autenticación y roles** — login admin/vendedor (JWT), login jugador (cédula), middleware de permisos por rol. *(Fase 2)*
2. **Módulo de gestión de salas** — CRUD de salas (para la instancia LAN correspondiente). *(Fase 2)*
3. **Módulo de gestión de empleados y usuarios** — CRUD separado de empleados (personal) y usuarios (cuentas del sistema). *(Fase 2)*
4. **Módulo de gestión de jornadas y partidas** — crear jornada, crear partida, consecutivo diario, iniciar/pausar/finalizar. *(Simplificado en Fase 1, completo en Fase 2)*
5. **Módulo de creación de figuras** — herramienta de cuadrícula editable (tipo BINGO) para que el admin diseñe y guarde formas de ganar en el catálogo. *(Fase 1 — prioridad alta)*
6. **Módulo de selección de formas por partida** — elegir qué figuras del catálogo juegan en la partida actual, tipo de premio (sencillo/figura/pleno) y su valor. *(Fase 1 — prioridad alta)*
7. **Módulo de módulos/paquetes y generación de cartones** — algoritmo para generar cartones virtuales únicos, agrupables en módulos/paquetes. *(Generación de cartones: Fase 1 — prioridad alta. Agrupación en paquetes/módulos: Fase 2)*
8. **Módulo de ventas (vendedor)** — registrar jugador, vender cartones/módulos, consultar ventas. *(Fase 2)*
9. **Módulo de balotera / motor de partida** — sortear balotas (manual o automático), emitir eventos en tiempo real vía WebSocket dentro de la LAN. *(Fase 1 — prioridad alta, ver detalle de balotera virtual abajo)*
10. **Módulo de pantalla de transmisión** — vista pública para proyectar en la sala: tablero interactivo (con el último número resaltado en verde), últimas 5 balotas como figuritas, formas de ganar activas con su premio, placeholder de video en vivo. Sin login, se actualiza en tiempo real vía el mismo WebSocket que emite el módulo de balotera. *(Fase 1 — prioridad alta)*
11. **Módulo de vista del jugador (celular)** — login por cédula, visualización del/los cartón(es) propios con marcado automático de números cantados en tiempo real, y **notificación de bingo**: cuando el cartón del jugador cumple alguna de las formas de ganar activas en la partida, el sistema se lo notifica de inmediato (esto se apoya en el módulo de validación de ganadores). *(Fase 1 sin login real — prioridad alta. Login por cédula real en Fase 2)*
12. **Módulo de validación de ganadores** — verificar cartón ganador contra balotas cantadas y figura jugada. *(Fase 1 — prioridad alta, necesario para que el aviso de bingo funcione)*
13. **Módulo de reportes** — ventas por vendedor/jornada, recaudo por partida, partidas jugadas, ganadores históricos. *(Fase 2)*
14. **Módulo de auditoría** — registro de acciones sensibles (log_auditoria), base para una futura certificación Coljuegos. *(Fase 2)*
15. **Módulo de configuración de cámara(s) y transmisión en vivo (futuro)** — placeholder de video, con soporte a más de una cámara por sala. *(Fase 3 / futuro)*

## Detalle del módulo de balotera virtual (parte del módulo 9)

Ya que la transmisión de la balotera física aún no se integra, este módulo debe incluir un **generador de balotas 100% aleatorio en software**, que reemplace visualmente a la balotera real y respete las reglas del bingo de 75 bolas:

- Nunca repite un número dentro de la misma partida (se saca de las balotas restantes, sin reemplazo).
- Respeta los rangos por letra: **B** 1–15, **I** 16–30, **N** 31–45, **G** 46–60, **O** 61–75.
- La partida finaliza el sorteo cuando se agotan las 75 balotas (o antes, si ya se cumplió la condición de ganador según la figura en juego).
- Cada balota sorteada queda registrada en `balota_cantada` con su orden y timestamp (igual que si viniera de una balotera física), para no duplicar lógica cuando más adelante se integre la balotera real.
- Debe apoyarse en un generador de números aleatorios criptográficamente seguro (ej. `secrets` de Python) en vez de un `random` básico, dejando el camino más fácil para una futura certificación de GNA ante Coljuegos.
- Expone el mismo evento por WebSocket que usaría una balotera física, de modo que a futuro basta con cambiar la fuente de la balota (física vs. virtual) sin tocar el resto del sistema.
