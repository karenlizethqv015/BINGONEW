"""Esquemas de `partida` y de su selección de formas de ganar."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.dominio.bingo import Patron
from app.models.partida import EstadoPartida
from app.models.partida_figura import TipoPremio


class FiguraResumen(BaseModel):
    """Datos de la figura que necesita la pantalla de configuración."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    patron: Patron


class FormaSeleccionada(BaseModel):
    """Una forma de ganar elegida para una partida, tal como la devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    figura: FiguraResumen
    tipo_premio: TipoPremio
    valor_premio: int
    orden: int


class FormaAElegir(BaseModel):
    """Una forma de ganar que se quiere incluir en la partida."""

    figura_id: int
    tipo_premio: TipoPremio = TipoPremio.FIGURA
    valor_premio: int = Field(default=0, ge=0)


class SeleccionDeFormas(BaseModel):
    """Reemplaza por completo las formas de ganar de una partida.

    Se reemplaza todo de una vez en lugar de ir agregando y quitando de a una:
    la pantalla de configuración es una lista que el administrador arma entera y
    guarda, así que una sola operación evita estados intermedios raros.

    El `orden` no se envía: sale de la posición en esta lista y es solo orden de
    presentación. Todas las formas de la partida juegan al mismo tiempo.
    """

    formas: list[FormaAElegir]

    @model_validator(mode="after")
    def sin_figuras_repetidas(self) -> "SeleccionDeFormas":
        ids = [forma.figura_id for forma in self.formas]
        if len(ids) != len(set(ids)):
            raise ValueError(
                "No se puede elegir la misma figura dos veces en una partida."
            )
        return self


class PartidaCrear(BaseModel):
    """Datos para crear una partida. El consecutivo lo asigna el backend."""

    precio_carton: int = Field(default=0, ge=0)
    duracion_segundos_entre_balota: int = Field(default=5, ge=1, le=300)


class PartidaActualizar(BaseModel):
    """Campos editables de una partida. Todos opcionales."""

    precio_carton: int | None = Field(default=None, ge=0)
    duracion_segundos_entre_balota: int | None = Field(default=None, ge=1, le=300)


class PartidaLeer(BaseModel):
    """Partida con sus formas de ganar."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_consecutivo: int
    estado: EstadoPartida
    precio_carton: int
    duracion_segundos_entre_balota: int
    creado_en: datetime
    iniciada_en: datetime | None
    finalizada_en: datetime | None
    figuras: list[FormaSeleccionada]

    @computed_field
    @property
    def total_formas(self) -> int:
        return len(self.figuras)

    @computed_field
    @property
    def premio_total(self) -> int:
        """Suma de los premios en juego. La muestra el tablero de transmisión."""
        return sum(forma.valor_premio for forma in self.figuras)
