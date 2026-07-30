# 08 — Modelo de Base de Datos

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 8. No omite información del original.

## Entidades principales y relaciones

- **usuario**: cuentas con acceso al sistema (admin/vendedor).
  - `id, nombre, usuario, password_hash, rol (admin|vendedor), sala_id (nullable), creado_en`
- **empleado**: personal de la sala (no necesariamente con login).
  - `id, sala_id (FK), nombre, cargo, documento, activo`
- **jugador**: personas registradas por cédula (compradores/jugadores).
  - `id, nombre, cedula (unique), telefono (opcional), creado_en`
- **sala**: cada sala física donde se instala el sistema (una instancia LAN por sala).
  - `id, nombre, direccion (opcional), activo`
- **jornada**: agrupación de partidas de un día/evento dentro de una sala.
  - `id, sala_id (FK), nombre, fecha, estado (planeada|en_curso|finalizada)`
- **partida**: una partida específica dentro de una jornada (equivalente al "Juego No." de la app anterior).
  - `id, jornada_id (FK), numero_consecutivo, estado (pendiente|en_curso|pausada|finalizada), duracion_segundos_entre_balota, precio_carton, progresivo_activo, loco_bingo_activo, reyes_activos, reyes_especiales_activos, creado_por (FK usuario), iniciada_en, finalizada_en`
- **figura**: catálogo global de formas de ganar, creado con la herramienta de cuadrícula editable del administrador.
  - `id, nombre, patron (JSON con las celdas marcadas de la matriz 5x25 tipo BINGO), creado_por (FK usuario), creado_en`
- **partida_figura**: asociación entre una partida y las figuras elegidas para jugarse, con su precio/premio (tabla intermedia N–N).
  - `id, partida_id (FK), figura_id (FK), tipo_premio (sencillo|figura|pleno), valor_premio, orden`
- **modulo**: paquete/puesto que agrupa varios cartones (ej. "Pirámide x6").
  - `id, sala_id (FK), tipo_modulo, activo`
- **carton**: cartón virtual de bingo.
  - `id, partida_id (FK), modulo_id (FK, nullable), serie, numero_carton, numeros (JSON con la matriz 5x5), jugador_id (FK, nullable hasta que se venda), vendido, vendido_por (FK usuario/vendedor), vendido_en`
- **venta**: registro de venta (puede incluir varios cartones/módulos a un mismo jugador).
  - `id, jugador_id (FK), vendedor_id (FK usuario), partida_id (FK), fecha, total`
- **venta_carton**: tabla intermedia venta-cartón.
  - `id, venta_id (FK), carton_id (FK)`
- **balota_cantada**: registro histórico de balotas sacadas por partida.
  - `id, partida_id (FK), numero (1-75), orden (secuencia), cantada_en (timestamp)`
- **ganador**: registro de quién ganó, con qué cartón y qué figura.
  - `id, partida_id (FK), carton_id (FK), partida_figura_id (FK), validado_por (FK usuario), fecha`
- **log_auditoria**: trazabilidad de acciones sensibles (creación/edición de figuras, inicio/cierre de partida, ventas, cambios de configuración).
  - `id, usuario_id (FK), accion, entidad_afectada, entidad_id, detalle (JSON), fecha`

## Relaciones clave

- `sala 1—N jornada`
- `jornada 1—N partida`
- `partida N—N figura` (a través de `partida_figura`)
- `partida 1—N carton`
- `partida 1—N balota_cantada`
- `modulo 1—N carton`
- `jugador 1—N carton`
- `jugador 1—N venta`
- `venta N—N carton` (a través de `venta_carton`)
- `carton 1—N ganador`
- `usuario 1—N log_auditoria`

## Nota para el MVP de demo (fase 1)

Para la fase 1 (ver `PROGRESS.md`), no es necesario implementar todo el modelo completo. Basta con las entidades mínimas para que el flujo funcione de punta a punta: `figura`, `partida_figura` (simplificada), `partida`, `carton`, `balota_cantada`, y `ganador`. Las entidades `usuario`, `empleado`, `sala`, `jornada`, `jugador` (con cédula real), `venta`, `venta_carton`, `modulo` y `log_auditoria` se implementan completas en la fase 2, aunque pueden dejarse como tablas simplificadas/stub desde ya si no cuesta tiempo extra.
