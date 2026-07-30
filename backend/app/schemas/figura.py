"""Esquemas de la entidad `figura`."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.dominio.bingo import TAMANO_CUADRICULA, Patron, contar_celdas


def _validar_patron(patron: Patron) -> Patron:
    """Comprueba que el patrón sea una matriz 5x5 con al menos una celda.

    Se valida aquí, en el borde de la API, para que ningún patrón mal formado
    llegue a la base de datos: la columna es JSON y el motor no puede
    comprobarlo por su cuenta.
    """
    if len(patron) != TAMANO_CUADRICULA:
        raise ValueError(
            f"El patrón debe tener {TAMANO_CUADRICULA} filas, tiene {len(patron)}."
        )

    for indice, fila in enumerate(patron):
        if len(fila) != TAMANO_CUADRICULA:
            raise ValueError(
                f"La fila {indice} debe tener {TAMANO_CUADRICULA} columnas, "
                f"tiene {len(fila)}."
            )

    if contar_celdas(patron) == 0:
        raise ValueError("La figura debe tener al menos una celda marcada.")

    return patron


class FiguraCrear(BaseModel):
    """Datos para crear una figura."""

    nombre: str = Field(min_length=1, max_length=60)
    patron: Patron

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio:
            raise ValueError("El nombre no puede estar vacío.")
        return limpio

    @field_validator("patron")
    @classmethod
    def comprobar_patron(cls, valor: Patron) -> Patron:
        return _validar_patron(valor)


class FiguraActualizar(BaseModel):
    """Datos para editar una figura. Ambos campos son opcionales."""

    nombre: str | None = Field(default=None, min_length=1, max_length=60)
    patron: Patron | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        if not limpio:
            raise ValueError("El nombre no puede estar vacío.")
        return limpio

    @field_validator("patron")
    @classmethod
    def comprobar_patron(cls, valor: Patron | None) -> Patron | None:
        return None if valor is None else _validar_patron(valor)


class FiguraLeer(BaseModel):
    """Figura tal como la devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    patron: Patron
    creado_en: datetime
    actualizado_en: datetime

    @computed_field
    @property
    def celdas_marcadas(self) -> int:
        """Cuántas celdas componen la figura. Lo usa la lista del frontend."""
        return contar_celdas(self.patron)
