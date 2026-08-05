"""Esquemas de `carton`."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.dominio.bingo import Carton as MatrizCarton

#: Tope por petición. Las salas grandes juegan con 5000 cartones o más, y
#: pedirlos de 500 en 500 son diez viajes seguidos por pantalla. El tope sigue
#: existiendo para que un número absurdo no llene la base sin querer.
MAXIMO_POR_PETICION = 5000


class GenerarCartones(BaseModel):
    """Petición para generar cartones en una partida."""

    cantidad: int = Field(ge=1, le=MAXIMO_POR_PETICION)

    #: Etiqueta de la tanda. Los consecutivos van por serie.
    serie: str = Field(default="A", min_length=1, max_length=8)


class CartonLeer(BaseModel):
    """Un cartón tal como lo devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    partida_id: int
    serie: str
    numero_carton: int
    #: Matriz 5x5; `null` en el centro, que es la casilla libre.
    numeros: MatrizCarton
    creado_en: datetime


class ResumenCartones(BaseModel):
    """Cuántos cartones tiene una partida y cómo se reparten por serie."""

    total: int
    por_serie: dict[str, int]


class CartonesGenerados(BaseModel):
    """Lo que devuelve una generación: qué se creó, no los cartones enteros.

    Devolver los 5000 cartones serían varios megabytes de JSON que la pantalla
    ni siquiera mira —recarga la primera página desde el servidor para que el
    resumen y la paginación cuadren—, y obligaría a releer de la base cada
    cartón recién insertado solo para rellenar su fecha de creación.
    """

    cantidad: int
    serie: str
    #: Primer y último consecutivo creados, para poder decir «A-1 … A-5000».
    desde: int
    hasta: int
    #: Cuántos cartones tiene la partida en total después de esta tanda.
    total_en_partida: int
