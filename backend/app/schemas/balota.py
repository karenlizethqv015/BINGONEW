"""Esquemas de `balota_cantada`."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from app.dominio.bingo import letra_de_numero
from app.models.partida import EstadoPartida


class BalotaLeer(BaseModel):
    """Una balota cantada tal como la devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    numero: int
    orden: int
    cantada_en: datetime

    @computed_field
    @property
    def letra(self) -> str:
        """B, I, N, G u O. Viaja resuelta para que el frontend no la calcule."""
        return letra_de_numero(self.numero)


class EstadoSorteo(BaseModel):
    """Situación del sorteo de una partida."""

    partida_id: int
    estado: EstadoPartida
    total_cantadas: int
    restantes: int
    ultima: BalotaLeer | None
