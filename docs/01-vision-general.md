# 01 — Visión General del Proyecto

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 1. No omite información del original.

## Objetivo del proyecto

Desarrollar una aplicación web, **desplegada localmente en la red LAN de cada sala** (sin dependencia de internet), para administrar jornadas de bingo en vivo, permitiendo que:

- Un **administrador** configure y controle cada partida (crear formas de ganar, elegir cuáles juegan y su precio, premios, duración, balotas), desde una pantalla con el control total y el tiempo de la jugada.
- Un **vendedor** registre compradores y venda cartones virtuales.
- Una **pantalla de transmisión** (para proyectar en la sala, ej. en un televisor/monitor) muestre el tablero completo, los números cantados, las últimas 5 balotas y las formas de ganar vigentes — es la vista pública del juego, no es la vista personal del jugador.
- Un **jugador/cliente**, desde su celular, compre e inicie sesión con su cédula, vea su(s) propio(s) cartón(es) con los números cantados marcándose automáticamente, y reciba un aviso del sistema cuando complete una de las formas de ganar configuradas (bingo).

La aplicación reemplaza una app de escritorio previa (de la cual se tomó referencia funcional — ver `04-referencia-app-anterior.md`), con una interfaz moderna y bien optimizada.

## Nota importante para el MVP de demo al cliente

Aunque la visión final de producto es una app **sin dependencia de internet, corriendo en LAN**, la prioridad inmediata (ver `PROGRESS.md` y `PLAN-CLAUDE-CODE.md`) es tener un **MVP visual y funcional desplegado en la web** para mostrárselo al cliente cuanto antes. Este MVP de demo puede simplificar temporalmente infraestructura (base de datos, hosting) mientras se valida el producto; la arquitectura LAN definitiva se retoma en fases posteriores de despliegue en sala.
