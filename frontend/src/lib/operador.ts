/**
 * La clave de operador, guardada en el navegador.
 *
 * **No es un login.** Mismo mecanismo que `admin.ts`, pero para el otro rol:
 * protege partidas, balotera y cartones, mientras que la clave de
 * administración solo protege el catálogo de figuras. El login de verdad
 * (admin y vendedor por usuario y contraseña, jugador por cédula) es de la
 * Fase 2.
 *
 * Vive en `localStorage` y no en memoria por el mismo motivo que la de
 * administración: durante una jornada la balotera se recarga varias veces.
 */

const LLAVE = 'bingo:clave-operador'

/** Aviso a las pantallas abiertas de que la clave cambió. */
const EVENTO = 'bingo:clave-operador-cambio'

export function claveOperador(): string | null {
  return localStorage.getItem(LLAVE)
}

export function guardarClaveOperador(clave: string): void {
  localStorage.setItem(LLAVE, clave)
  window.dispatchEvent(new Event(EVENTO))
}

export function olvidarClaveOperador(): void {
  localStorage.removeItem(LLAVE)
  window.dispatchEvent(new Event(EVENTO))
}

/**
 * Avisa cuando la clave se guarda o se borra.
 *
 * `storage` solo se dispara entre pestañas distintas, así que hace falta un
 * evento propio para que la pantalla que la acaba de guardar se entere.
 */
export function alCambiarClaveOperador(escuchar: () => void): () => void {
  window.addEventListener(EVENTO, escuchar)
  window.addEventListener('storage', escuchar)
  return () => {
    window.removeEventListener(EVENTO, escuchar)
    window.removeEventListener('storage', escuchar)
  }
}

/** Cabecera con la que viaja la clave. Debe coincidir con `app/seguridad.py`. */
export const CABECERA_OPERADOR = 'X-Operador-Clave'

/** Se lanza cuando el backend responde 401: falta la clave o no es la buena. */
export class FaltaClaveOperador extends Error {
  constructor() {
    super('Hace falta la clave de operador.')
    this.name = 'FaltaClaveOperador'
  }
}
