# 04 — Hallazgos de la App de Escritorio Anterior (referencia funcional)

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 4. No omite información del original.

Se revisaron capturas de la app anterior (v3.0.7.0). Resumen de lo más importante a considerar, evitando duplicar lo ya descrito en `03-alcance-funcional-mvp.md`:

- **Menú diferenciado de "Empleados", "Usuarios" y "Clientes":** son 3 entidades distintas — empleados (personal de la sala, no necesariamente con acceso al sistema), usuarios (cuentas con login: admin/vendedor) y clientes (jugadores registrados por cédula).
- **"Módulos":** además del cartón individual, la app maneja el concepto de **módulo** (ej. "Pirámide x6"), que agrupa varios cartones (identificados por serie + número) bajo un mismo puesto/paquete. Es útil replicar este concepto para ventas por paquete, aunque en la versión web puede simplificarse a "paquete de cartones".
- **"Configurar Figuras":** confirma el flujo — es un catálogo global de figuras (patrones), cada una con nombre y su cuadrícula editable, independiente de las partidas.
- **"Categoría Reyes" / "Reyes Activos" / "Reyes Especiales" / "Elegir Rey":** parece ser una categoría especial de módulos/jugadores con reglas propias dentro de la partida (bonificación o elegibilidad especial). Queda anotado como funcionalidad a definir en detalle más adelante; **no es parte del MVP** pero se deja espacio en el modelo de datos.
- **"Progresivo" / "Máximo Progresivo" / "Paga Progresivo":** premio acumulado que crece entre partidas hasta que se gana.
- **"Loco Bingo":** variante especial del juego (activable por checkbox).
- **"Acumulados": Número de Balotas, Balota Final, Bingo Salado, Múltiplo:** condiciones adicionales de premiación ligadas a cuántas balotas se han cantado.
- **"Adicional Balotas Finales":** premio extra configurable con límite de balotas y opción de único ganador.
- **Configuración de cámara(s):** la sala puede tener más de una cámara (Cám 1 / Cám 2) — relevante para el componente de video en vivo mencionado.
- **Informes / Financiero:** módulos de recaudo (por juego y por módulo/máquina), total ronda, total juego — reportes que deben existir en el MVP completo de forma básica.
- **"Lottingo":** aparece como módulo/menú aparte en la app anterior; **se deja fuera del alcance** de este proyecto salvo que se decida incluirlo explícitamente.
- El tablero principal (vista del "cantador") muestra: reloj de la jugada, número de juego, últimas 5 balotas, total de balotas, tabla de premios en juego con su figura en miniatura y estado ("Jugando"), consulta de cartón/ganadores — esto aplica tanto a la vista de administrador (control, con el cronómetro) como, en versión simplificada sin controles, a la **pantalla de transmisión** pública de la sala.

## Funcionalidades explícitamente pospuestas (no MVP inmediato)

- Reyes / Reyes Especiales
- Progresivo / Máximo Progresivo
- Loco Bingo
- Acumulados (Balota Final, Bingo Salado, Múltiplo, Adicional Balotas Finales)
- Configuración de cámara(s) y video en vivo
- Lottingo (fuera de alcance salvo indicación contraria)
