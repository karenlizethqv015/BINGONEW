# 05 — Requisitos No Funcionales

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 5. No omite información del original.

- **Sin dependencia de internet:** la aplicación corre sobre un servidor dentro de la LAN de cada sala; todos los equipos (admin, vendedor, jugadores) acceden por la IP local del servidor. No debe haber llamadas obligatorias a servicios externos para el funcionamiento normal. *(Ver excepción temporal para el MVP de demo en `01-vision-general.md`)*.
- **Diseño orientado a PC/escritorio:** aunque puede ser responsiva, el diseño debe priorizarse para pantallas de computador (resoluciones tipo 1366x768 en adelante), replicando la densidad de información de la app anterior, no un enfoque mobile-first.
- Multi-sala: cada sala opera de forma independiente (cada una con su propio servidor/instancia en su LAN).
- Actualización en tiempo real (balotas, tablero, ganadores) sin recargar la página, dentro de la misma red local.
- Separación clara de roles y permisos.
- Trazabilidad básica de acciones (quién configuró qué, quién vendió qué cartón) — sienta las bases para la auditoría que exige Coljuegos (ver `07-coljuegos-futuro.md`).

## Requisito adicional (agregado por la usuaria, no en el documento original)

- El **frontend del MVP debe tener una apariencia llamativa y profesional** ("buena apariencia"), no un prototipo visualmente básico, ya que se usará para mostrarle el producto a un cliente potencial antes de continuar con las siguientes fases.
- El MVP debe quedar **desplegado en una URL accesible por web** (no solo corriendo en local) para que el cliente pueda verlo sin instalación previa.
