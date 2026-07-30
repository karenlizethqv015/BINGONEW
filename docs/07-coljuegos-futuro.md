# 07 — Consideraciones de Certificación Coljuegos (a futuro, no MVP)

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 7. No omite información del original.

No es parte del alcance inmediato, pero se resume aquí para que el diseño actual no cierre puertas a una futura certificación:

- **Módulos obligatorios que exige Coljuegos:** control del juego (con Generador de Números Aleatorios certificado — GNA), módulo de registro, tableros de visualización (100% de jugadores de la sala), balotas/baloteras (norma ICONTEC si son electro-neumáticas), y sistema de seguimiento/reportes con acceso de solo consulta para Coljuegos.
- **Trazabilidad e inmutabilidad:** los datos de una partida no deben poder alterarse una vez iniciada; se exigen logs de transacciones, errores y reprocesos.
- **Integración API REST con Coljuegos:** flujo de 3 llamadas (`/JWTAuth` → `/JWTEncryptRequest` → `/enviarTransmision`), con 3 tipos de trama (Tipo 0: sin eventos en el día, Tipo 1: al finalizar cada partida, Tipo 2: cuando el premio de un ganador supera 48 UVT, incluyendo datos personales del ganador).
- **Seguridad:** control de acceso por roles, backups en ubicación física distinta, conservación histórica de bases de datos durante toda la vigencia del contrato.
- **Certificación:** debe renovarse cada 2 años o ante cambios de versión del software (verificado por Coljuegos vía código SHA).

## Decisiones de arquitectura que se toman desde ahora para facilitar esto después

- Diseñar el modelo de datos con una tabla de auditoría (`log_auditoria`) desde el MVP, aunque su explotación completa no sea prioritaria todavía.
- No permitir edición directa de balotas ya cantadas ni de resultados de partidas finalizadas (solo lectura una vez cerrada la partida).
- Mantener separado el control de acceso por rol desde el inicio (ya contemplado en el MVP completo, aunque se simplifique temporalmente en la demo — ver `02-roles-actores.md`).
