"""Fixtures compartidas por las pruebas del backend."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def cliente() -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP que habla directo con la app, sin levantar un servidor.

    ASGITransport ejecuta la aplicación en el mismo proceso, así que las pruebas
    corren rápido y no dependen de que haya un puerto libre.
    """
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://test") as c:
        yield c
