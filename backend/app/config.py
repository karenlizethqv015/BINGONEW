"""Configuración de la aplicación, leída desde variables de entorno o archivo .env.

Nada de configuración se escribe directamente en el código: todo pasa por aquí,
para que el mismo backend sirva tanto en la demo web como en la instalación
final en LAN sin tocar una sola línea (ver docs/06-arquitectura.md).
"""

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Parámetros de conexión que `asyncpg` no entiende y hay que quitar de la URL.
#:
#: Son de `libpq`, la librería de C que usan los clientes síncronos de
#: PostgreSQL. `asyncpg` no la usa y los recibe como argumentos sueltos, así que
#: revienta con un `TypeError: connect() got an unexpected keyword argument
#: 'sslmode'` que en ningún momento menciona que el problema esté en la URL.
#: `asyncpg` ya negocia TLS por su cuenta cuando el servidor lo pide.
PARAMETROS_DE_LIBPQ = frozenset(
    {"sslmode", "channel_binding", "target_session_attrs", "gssencmode"}
)


def normalizar_url_de_base_de_datos(url: str) -> str:
    """Deja una cadena de conexión lista para el motor asíncrono.

    Existe para poder **pegar la cadena del proveedor tal como la da**, sin
    editarla a mano: Railway, Render, Neon y Heroku entregan todos una URL
    pensada para clientes síncronos, y las tres diferencias que tienen con lo
    que espera SQLAlchemy son siempre las mismas.

    Se hace aquí, en la configuración, y no en `app/db.py`, porque
    `alembic/env.py` también lee `settings.database_url`: arreglándolo en un solo
    sitio quedan bien la aplicación y las migraciones.

    Lo que ajusta:

    - `postgresql://` y `postgres://` pasan a `postgresql+asyncpg://`. Sin el
      driver explícito, SQLAlchemy busca uno síncrono y el arranque falla.
    - Quita los parámetros de `libpq` (ver `PARAMETROS_DE_LIBPQ`).

    Cualquier otra cadena —SQLite, o una que ya traiga driver— se devuelve
    intacta.
    """
    esquema, _, resto = url.partition("://")
    if esquema not in {"postgres", "postgresql"}:
        return url

    partes = urlsplit(f"postgresql+asyncpg://{resto}")

    conservados = [
        (clave, valor)
        for clave, valor in parse_qsl(partes.query, keep_blank_values=True)
        if clave.lower() not in PARAMETROS_DE_LIBPQ
    ]

    return urlunsplit(partes._replace(query=urlencode(conservados)))


class Settings(BaseSettings):
    """Ajustes de la aplicación con sus valores por defecto para desarrollo."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Nombre y versión que expone la API (aparecen en /docs).
    app_nombre: str = "API Bingo"
    app_version: str = "0.1.0"

    # Cadena de conexión a la base de datos.
    #
    # Por defecto SQLite, que es lo que hace que el proyecto arranque sin tener
    # que levantar nada. Para PostgreSQL basta con definir DATABASE_URL, y se
    # puede pegar **tal como la entregue el proveedor**: el validador de abajo
    # le pone el driver asíncrono y le quita lo que asyncpg no entiende.
    #
    #   postgresql://usuario:clave@servidor:5432/bingo   ← vale
    #   postgresql+asyncpg://usuario:clave@servidor:5432/bingo
    database_url: str = "sqlite+aiosqlite:///./bingo.db"

    @field_validator("database_url")
    @classmethod
    def _normalizar_database_url(cls, valor: str) -> str:
        return normalizar_url_de_base_de_datos(valor)

    # Orígenes autorizados para CORS. En desarrollo son los puertos de Vite.
    # En la instalación en LAN se define por variable de entorno con la IP del
    # servidor de la sala.
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Muestra el SQL generado por SQLAlchemy en consola. Útil al depurar.
    db_echo: bool = False

    # Carpeta con el frontend ya compilado (`npm run build`).
    #
    # Si existe, el backend la sirve él mismo y toda la aplicación queda en un
    # solo origen. Es lo que hace que el frontend nunca tenga que escribir un
    # host ni un puerto (regla de la Fase 0), y vale igual para la demo en la
    # web que para la instalación final en la LAN de la sala.
    #
    # En desarrollo no existe y no se sirve nada: de eso se encarga Vite con su
    # proxy.
    frontend_dist: str = "../frontend/dist"

    # Clave única y compartida que protege lo que MODIFICA la partida.
    #
    # No es el login de la Fase 2: no hay usuarios, ni contraseñas por persona,
    # ni sesiones. Es una tranca para que un curioso con el enlace de la demo
    # pública no reinicie el sorteo en mitad de la jugada.
    #
    # **Vacía (lo de por defecto) significa todo abierto**, que es lo que hace
    # falta en desarrollo y en la LAN de la sala, donde no hay nadie de fuera.
    # En la demo desplegada se define la variable de entorno ADMIN_CLAVE.
    admin_clave: str = ""

    # Clave única y compartida que protege lo que MODIFICA partidas, balotera
    # y cartones — el trabajo del operador de la sala.
    #
    # Es el mismo mecanismo que `admin_clave` (no el login de la Fase 2), pero
    # con su propio alcance: el administrador ya no necesita esta clave para
    # su trabajo (figuras y ajustes básicos), y el operador no necesita la de
    # administración. Igual que `admin_clave`, vacía significa todo abierto.
    operador_clave: str = ""


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración, cacheada para no releer el .env en cada uso."""
    return Settings()


settings = get_settings()
