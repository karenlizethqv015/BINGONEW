"""Configuración de la aplicación, leída desde variables de entorno o archivo .env.

Nada de configuración se escribe directamente en el código: todo pasa por aquí,
para que el mismo backend sirva tanto en la demo web como en la instalación
final en LAN sin tocar una sola línea (ver docs/06-arquitectura.md).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # Por defecto SQLite en modo asíncrono, que es lo que usa la demo.
    # Para pasar a PostgreSQL en la Fase 2 basta con definir la variable de
    # entorno DATABASE_URL con, por ejemplo:
    #   postgresql+asyncpg://usuario:clave@servidor:5432/bingo
    database_url: str = "sqlite+aiosqlite:///./bingo.db"

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


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración, cacheada para no releer el .env en cada uso."""
    return Settings()


settings = get_settings()
