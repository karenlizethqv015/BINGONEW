/**
 * Constantes y utilidades del bingo de 75 bolas, lado frontend.
 *
 * Deben coincidir con `backend/app/dominio/bingo.py`. Si alguna cambia, hay que
 * cambiarla en los dos lados.
 */

/** El cartón y las figuras son matrices de 5x5. */
export const TAMANO_CUADRICULA = 5

/** Encabezados de las columnas. */
export const LETRAS = ['B', 'I', 'N', 'G', 'O'] as const

/**
 * Casilla libre: el centro de la cuadrícula. En el bingo de 75 bolas siempre
 * cuenta como marcada, sin que salga ninguna balota. Una figura puede incluirla
 * o no ("cuatro esquinas" no la incluye).
 */
export const FILA_LIBRE = 2
export const COLUMNA_LIBRE = 2

/** Un patrón de figura: matriz 5x5 de booleanos. */
export type Patron = boolean[][]

/** Un cartón: matriz 5x5 de números, con `null` en la casilla libre. */
export type MatrizCarton = (number | null)[][]

/** Rango de números de cada columna, ambos extremos incluidos. */
export const RANGOS_POR_COLUMNA: [number, number][] = [
  [1, 15],
  [16, 30],
  [31, 45],
  [46, 60],
  [61, 75],
]

/** Total de balotas de una partida. */
export const TOTAL_BALOTAS = 75

/**
 * Indica si una celda del cartón está marcada.
 *
 * **La casilla libre (`null`) siempre cuenta como marcada**, sin que salga
 * ninguna balota: es la regla del bingo de 75 bolas. Tenerla en una función y
 * no repartida por los componentes evita que alguna vista se olvide de ella y
 * dé por incompleto un cartón que sí ganó.
 */
export function estaMarcada(
  valor: number | null,
  cantadas: ReadonlySet<number>,
): boolean {
  return valor === null || cantadas.has(valor)
}

/** Cuántas celdas del cartón están marcadas, contando la casilla libre. */
export function contarMarcadas(
  carton: MatrizCarton,
  cantadas: ReadonlySet<number>,
): number {
  return carton.flat().filter((valor) => estaMarcada(valor, cantadas)).length
}

/** Devuelve la letra ('B', 'I', 'N', 'G' u 'O') de un número. */
export function letraDeNumero(numero: number): string {
  const indice = RANGOS_POR_COLUMNA.findIndex(
    ([desde, hasta]) => numero >= desde && numero <= hasta,
  )
  if (indice === -1) {
    throw new Error(`${numero} no está entre 1 y ${TOTAL_BALOTAS}.`)
  }
  return LETRAS[indice]
}

export function esCeldaLibre(fila: number, columna: number): boolean {
  return fila === FILA_LIBRE && columna === COLUMNA_LIBRE
}

export function patronVacio(): Patron {
  return Array.from({ length: TAMANO_CUADRICULA }, () =>
    Array.from({ length: TAMANO_CUADRICULA }, () => false),
  )
}

export function contarCeldas(patron: Patron): number {
  return patron.flat().filter(Boolean).length
}

/** Devuelve una copia del patrón con una celda invertida. */
export function alternarCelda(
  patron: Patron,
  fila: number,
  columna: number,
): Patron {
  return patron.map((filaActual, f) =>
    f === fila
      ? filaActual.map((celda, c) => (c === columna ? !celda : celda))
      : filaActual,
  )
}

/** Devuelve una copia del patrón con una celda puesta en un valor concreto. */
export function fijarCelda(
  patron: Patron,
  fila: number,
  columna: number,
  valor: boolean,
): Patron {
  if (patron[fila][columna] === valor) return patron

  return patron.map((filaActual, f) =>
    f === fila
      ? filaActual.map((celda, c) => (c === columna ? valor : celda))
      : filaActual,
  )
}

export function sonIguales(a: Patron, b: Patron): boolean {
  return a.every((fila, f) => fila.every((celda, c) => celda === b[f][c]))
}

/** Construye un patrón a partir de una función que decide cada celda. */
function construir(decidir: (fila: number, columna: number) => boolean): Patron {
  return Array.from({ length: TAMANO_CUADRICULA }, (_, fila) =>
    Array.from({ length: TAMANO_CUADRICULA }, (_, columna) =>
      decidir(fila, columna),
    ),
  )
}

/**
 * Plantillas de las figuras más comunes del bingo de 75 bolas.
 * Son solo un punto de partida: el administrador puede editarlas después.
 */
export const PLANTILLAS = [
  {
    nombre: 'Línea horizontal',
    patron: construir((fila) => fila === 0),
  },
  {
    nombre: 'Línea vertical',
    patron: construir((_, columna) => columna === 0),
  },
  {
    nombre: 'Equis',
    patron: construir(
      (fila, columna) => fila === columna || fila + columna === TAMANO_CUADRICULA - 1,
    ),
  },
  {
    nombre: 'Cuatro esquinas',
    patron: construir(
      (fila, columna) =>
        (fila === 0 || fila === TAMANO_CUADRICULA - 1) &&
        (columna === 0 || columna === TAMANO_CUADRICULA - 1),
    ),
  },
  {
    nombre: 'Marco',
    patron: construir(
      (fila, columna) =>
        fila === 0 ||
        columna === 0 ||
        fila === TAMANO_CUADRICULA - 1 ||
        columna === TAMANO_CUADRICULA - 1,
    ),
  },
  {
    nombre: 'Cartón lleno',
    patron: construir(() => true),
  },
] as const
