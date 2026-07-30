# 03 — Alcance Funcional (MVP original del documento de visión)

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 3. No omite información del original.
>
> ⚠️ Esta sección describe el **alcance funcional completo** tal como se definió en el documento de visión original. La **priorización real de desarrollo** (qué se construye primero para la demo al cliente) está en `PROGRESS.md` y `PLAN-CLAUDE-CODE.md` — no son lo mismo. Léase este archivo como "qué debe existir en algún momento del MVP", no como orden de construcción.

## Administrador

- Crear/gestionar salas.
- Crear jornadas y partidas dentro de una sala.
- **Herramienta de creación de figuras (formas de ganar):** una cuadrícula de bingo (5x25 tipo BINGO) editable donde el admin marca/desmarca las celdas que componen el patrón, le da un nombre y lo guarda en la base de datos como una figura reutilizable (catálogo de figuras, independiente de una partida específica).
- **Herramienta de selección de formas por partida:** de ese catálogo, el admin elige cuáles figuras se juegan en la partida actual y define el precio/premio de cada una (equivalente a la pantalla "Configurar/Editar Juego" de la app anterior: tipo de premio Sencillo/Figura/Pleno, valor, orden).
- Configurar duración entre balotas, cantidad de cartones disponibles, valor del cartón.
- Iniciar/pausar/finalizar el sorteo de balotas (manual o automático).
- Ver estado en tiempo real de la partida (balotas cantadas, ganadores, recaudo).
- Gestionar usuarios del sistema (admin/vendedor) y empleados.

## Vendedor

- Registrar comprador (nombre, cédula).
- Vender uno o varios cartones a un comprador, asociados a una partida/jornada.
- Consultar cartones vendidos y disponibles.

## Pantalla de Transmisión (vista pública de sala, ej. proyectada en TV/monitor)

- Muestra el tablero completo de 75 números, marcando los ya cantados, **resaltando en verde el último número cantado** (dentro del tablero mismo, distinto del marcado normal de los ya cantados).
- Muestra, en una sección aparte del tablero, las últimas 5 balotas cantadas representadas como "figuritas" de bolas de bingo con su número (igual a la referencia de la app anterior).
- Muestra las formas de ganar activas en la partida (con su premio).
- Espacio reservado para el componente de video en vivo (a integrar después).
- No requiere login de un jugador particular; es una vista compartida para todos los presentes en la sala.

## Jugador (desde su celular)

- Login por cédula.
- Ver su(s) propio(s) cartón(es) asignado(s), con los números marcados automáticamente a medida que se cantan las balotas.
- Recibir un aviso claro del sistema cuando su cartón complete alguna de las formas de ganar activas en la partida (bingo).
