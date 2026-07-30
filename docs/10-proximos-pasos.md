# 10 — Próximos Pasos Sugeridos (del documento original)

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 10. No omite información del original.

1. Definir en detalle la mecánica de "Reyes"/"Reyes Especiales", "Progresivo", "Loco Bingo" y "Acumulados" (Balota Final, Bingo Salado, Múltiplo) — quedaron anotados pero sin especificar reglas exactas.
2. Confirmar si el concepto de "módulo/paquete de cartones" aplica igual en la versión web o si se simplifica a venta de cartones individuales.
3. Montar el esqueleto del proyecto (backend FastAPI + frontend React) con Docker Compose, pensado para instalarse igual en cada sala sin internet.
4. Implementar módulo por módulo, empezando por autenticación → salas/jornadas/partidas → figuras → cartones → ventas → balotera en tiempo real → pantalla de transmisión → vista del jugador en celular.

> **Nota:** este orden original (punto 4) se reemplaza en la práctica por la priorización de negocio definida por la usuaria: ver `PROGRESS.md` para el orden real que se está siguiendo, que empieza por figuras → cartones → balotera → tablero de transmisión → cartón del jugador → panel admin, dejando autenticación, ventas y salas/jornadas completas para la fase 2.
