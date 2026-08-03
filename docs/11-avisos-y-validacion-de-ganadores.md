# 11. Avisos de ganadores y de cartones cerca de ganar

Este documento cubre dos cosas que van juntas porque salen del mismo cálculo:

- La **validación de ganadores** (tarea #8 de la Fase 1): saber qué cartón
  completó qué forma y con qué balota.
- Los **avisos de cerca de ganar**, pedidos por el cliente y que no estaban en
  el documento de visión original: qué cartones están a una y a dos balotas.

Es lo que convierte la partida en algo que se puede seguir. Sin esto, el
administrador tendría que mirar los cartones uno por uno para saber si alguien
ganó, y el momento del bingo —que es el clímax del juego— pasaría inadvertido.

## La cuenta

Para cada par (cartón, forma) se calculan los **números que esa forma exige
sobre ese cartón**: los valores del cartón en las celdas que el patrón marca.

> **La casilla libre no exige ninguna balota.** Ya cuenta como marcada en el
> bingo de 75 bolas, así que una figura que la incluya exige una balota menos
> que celdas tiene. Una figura formada *solo* por la casilla libre exigiría cero
> balotas, y por eso se ignora (ver «casos raros» más abajo).

```
faltan = |números exigidos − balotas cantadas|
```

| `faltan` | Significa            | Quién lo ve            |
| -------- | -------------------- | ---------------------- |
| 0        | Bingo                | Administrador y jugador |
| 1        | A una balota         | Solo el administrador  |
| 2        | A dos balotas        | Solo el administrador  |
| 3 o más  | No se avisa          | —                      |

Es una sola resta de conjuntos: la misma cuenta responde las tres preguntas.

La regla vive en `numeros_requeridos` y `faltan_para`, en
`backend/app/dominio/bingo.py`, junto al resto de reglas del bingo. El evaluador
que las aplica a toda la partida está en `backend/app/dominio/ganadores.py` y no
toca la base de datos: recibe cartones, formas y balotas cantadas y devuelve el
cuadro. Eso permite probarlo armando cartones a mano, que es la única forma de
comprobar de verdad estas cuentas.

## Reglas de juego decididas

### Un bingo no detiene el sorteo

Sale el aviso y la partida sigue. El administrador pausa o finaliza si quiere,
con los botones que ya existen.

**Por qué:** todas las formas de una partida juegan a la vez (ver `PROGRESS.md`),
así que un bingo de «línea» no debe frenar una partida en la que «cartón lleno»
sigue en juego. `docs/09-modulos-desarrollo.md` dice que el sorteo termina «al
agotarse las 75 balotas, o antes si ya se cumplió la condición de ganador», pero
esa frase está escrita pensando en **una sola figura por juego**, que no es cómo
funciona aquí.

### Una forma ganada se cierra

Solo ganan los cartones que completan la forma **en la misma balota**. Esos
comparten el premio — es el caso de «si hace bingo más de uno, decir la
cantidad». Quien la complete tres balotas después llegó tarde y no se registra.

**Por qué:** es la regla estándar del bingo, y sin ella al final del sorteo
*todos* los cartones habrían «ganado» todo: con las 75 balotas fuera, cualquier
figura está completa en cualquier cartón.

Consecuencia: una forma ya ganada **deja de generar avisos de «cerca»**. Decirle
al administrador que a alguien le falta una balota para algo que ya se repartió
sería desinformarlo.

### Quién ve qué

| Pantalla        | Bingo                       | A una / a dos |
| --------------- | --------------------------- | ------------- |
| `/admin` (balotera) | Todos, con premio y códigos | Sí            |
| `/jugador`      | Solo el de **su** cartón    | **No**        |
| `/transmision`  | (tarea #6)                  | **Nunca**     |

El jugador no ve «a una / a dos»: es información de control y además le quitaría
la emoción de ver salir su número. En el tablero de la sala sería directamente
un delator.

## Dónde se calcula

**En el backend, siempre.** Decidir quién ganó es una decisión con dinero detrás
y no puede depender de lo que crea cada navegador.

Es distinto del **marcado** del cartón, que sí se resuelve en el cliente
(`estaMarcada` en `frontend/src/lib/bingo.ts`): ahí el navegador ya tiene el
cartón y las balotas, y marcar es solo cruzarlos. Aquí hace falta conocer las
formas en juego, todos los cartones y quién ganó antes.

La evaluación corre **en cada balota**, dentro del cerrojo de la partida: dos
evaluaciones simultáneas leerían la misma tabla de ganadores vacía y registrarían
los mismos dos veces.

## El evento

Se emite después de cada balota y al conectarse una pantalla. Lleva la **foto
completa**, no lo que cambió, igual que `sincronizacion`: quien se abre o se
reconecta a mitad de partida reconstruye el cuadro entero sin pedir nada más.

```jsonc
{
  "tipo": "ganadores",
  "partida_id": 25,
  "orden_balota": 25,
  "bingos": [{
    "partida_figura_id": 5,
    "figura": "Cuatro esquinas",
    "valor_premio": 120000,
    "orden_balota": 25,        // la balota con la que se ganó, no la actual
    "numero_balota": 74,
    "nuevo": true,             // recién detectado en ESTA evaluación
    "cartones": [{ "carton_id": 7, "codigo": "A-1" }]
  }],
  "total_cartones_ganadores": 1,
  "a_una": 7,                  // totales REALES
  "a_dos": 18,
  "cerca": [                   // lista RECORTADA (50 filas)
    { "carton_id": 7, "codigo": "A-1", "partida_figura_id": 6,
      "figura": "Diagonal", "faltan": 1, "numeros": [55] }
  ]
}
```

Dos detalles que importan:

- **`nuevo` significa «detectado en esta evaluación», no «reciente».** Es lo que
  permite que la pantalla avise una sola vez en lugar de repetir el aviso en cada
  balota posterior. Una consulta HTTP llega siempre después de que el ganador
  quedó registrado, así que para ella `nuevo` es siempre `false`: el aviso fresco
  viaja por el WebSocket.
- **`cerca` va recortada, `a_una` y `a_dos` no.** Con 500 cartones y varias
  formas la lista serían miles de filas que nadie puede leer, pero el recorte no
  debe mentir en el número.

El endpoint `GET /api/partidas/{id}/ganadores` devuelve exactamente el mismo
cuerpo, construido con la misma función, para la carga inicial y para poder
comprobarlo desde un script.

## Persistencia

Tabla `ganador` (`backend/app/models/ganador.py`), la última entidad que
`docs/08-modelo-datos.md` pide para la Fase 1:

`partida_id`, `carton_id`, `partida_figura_id`, `orden_balota`, `numero_balota`,
`detectado_en`. Sin `validado_por`, que necesita la tabla `usuario` de la Fase 2.

- Índice único `(partida_id, carton_id, partida_figura_id)`, porque la evaluación
  corre en cada balota.
- **Reiniciar el sorteo borra los ganadores.** Si quedaran, sus formas seguirían
  saliendo como cerradas y nadie podría volver a ganarlas.
- **No se pueden cambiar las formas de una partida con ganadores registrados**
  (409). `ganador.partida_figura_id` es una llave foránea, y reemplazar la
  selección borraría los ganadores en cascada y en silencio.

## Casos raros que están cubiertos

- **Figura formada solo por la casilla libre.** Exige cero balotas: daría bingo a
  todos los cartones antes de empezar. El evaluador ignora toda forma que no
  exija ningún número.
- **Reevaluar una partida vieja** (al reconectarse una pantalla) devuelve el
  mismo cuadro y con la balota original, no con la que va el sorteo entonces.
- **Varios ganadores a la vez** en la misma forma: se registran todos y el aviso
  dice cuántos son.
- **Un cartón que gana varias formas**: aparece en cada una.

## Qué queda fuera

- **Validación manual del cartón por parte del administrador.** Hoy el sistema
  detecta y registra; no hay un paso de «aprobar» al ganador. En la Fase 2, con
  usuarios, entra `ganador.validado_por`.
- **Pagar el premio / cerrar caja.** Es del módulo de reportes (Fase 2).
- **Terminar el sorteo automáticamente** al ganarse todas las formas. Hoy
  termina a las 75 balotas o cuando el administrador lo finaliza.
