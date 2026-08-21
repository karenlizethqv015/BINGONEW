interface Props {
  aUna: number
  aDos: number
}

/**
 * Cuántos cartones están a punto de ganar, en total, sin importar la forma.
 *
 * Es información **solo del administrador**: al jugador le quitaría la
 * emoción y al tablero de la sala lo convertiría en un delator. Antes
 * mostraba un desglose por forma en una tarjeta aparte; el cliente pidió
 * condensarlo al total general, en dos líneas cortas, para que quepa debajo
 * del control del sorteo sin desplazarse.
 */
export function CercaDeGanar({ aUna, aDos }: Props) {
  return (
    <div className="space-y-1 text-sm text-muted-foreground">
      <p>
        Cartones a una balota de ganar:{' '}
        <span className="font-bold tabular text-primary">{aUna}</span>
      </p>
      <p>
        Cartones a dos balotas de ganar:{' '}
        <span className="font-bold tabular text-primary">{aDos}</span>
      </p>
    </div>
  )
}
