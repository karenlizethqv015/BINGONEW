/**
 * La clave de administración, guardada en el navegador.
 *
 * **No es un login.** No hay usuarios ni sesiones: es una sola clave compartida
 * que evita que un curioso con el enlace de la demo pública toque la partida en
 * vivo. El login de verdad (admin y vendedor por usuario y contraseña, jugador
 * por cédula) es de la Fase 2.
 *
 * Vive en `localStorage` y no en memoria para que no haya que volver a
 * escribirla en cada recarga: durante una jornada la pantalla de mando se
 * recarga varias veces.
 */

const LLAVE = 'bingo:clave-admin'

/** Aviso a las pantallas abiertas de que la clave cambió. */
const EVENTO = 'bingo:clave-admin-cambio'

export function claveAdmin(): string | null {
  return localStorage.getItem(LLAVE)
}

export function guardarClaveAdmin(clave: string): void {
  localStorage.setItem(LLAVE, clave)
  window.dispatchEvent(new Event(EVENTO))
}

export function olvidarClaveAdmin(): void {
  localStorage.removeItem(LLAVE)
  window.dispatchEvent(new Event(EVENTO))
}

/**
 * Avisa cuando la clave se guarda o se borra.
 *
 * `storage` solo se dispara entre pestañas distintas, así que hace falta un
 * evento propio para que la pantalla que la acaba de guardar se entere.
 */
export function alCambiarClaveAdmin(escuchar: () => void): () => void {
  window.addEventListener(EVENTO, escuchar)
  window.addEventListener('storage', escuchar)
  return () => {
    window.removeEventListener(EVENTO, escuchar)
    window.removeEventListener('storage', escuchar)
  }
}

/** Cabecera con la que viaja la clave. Debe coincidir con `app/seguridad.py`. */
export const CABECERA_ADMIN = 'X-Admin-Clave'

/** Se lanza cuando el backend responde 401: falta la clave o no es la buena. */
export class FaltaClaveAdmin extends Error {
  constructor() {
    super('Hace falta la clave de administración.')
    this.name = 'FaltaClaveAdmin'
  }
}
