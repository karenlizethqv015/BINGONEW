"""Esquemas de `carton`."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.dominio.bingo import Carton as MatrizCarton

#: Tope por petición. Generar de a muchos es normal (una jornada vende cientos
#: de cartones), pero un número absurdo bloquearía el proceso y llenaría la
#: base sin querer.
MAXIMO_POR_PETICION = 500


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
