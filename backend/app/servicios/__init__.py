"""Servicios: orquestan la base de datos y las reglas puras de `app/dominio`.

La separación es a propósito. `app/dominio` no sabe que existe una base de datos
y por eso se puede probar armando cartones a mano; `app/routers` solo se ocupa de
HTTP. Lo que queda en medio —leer, aplicar la regla, guardar— vive aquí, para no
repetirlo en cada endpoint que lo necesita.
"""
