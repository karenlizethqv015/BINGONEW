# Imagen única con el frontend compilado dentro del backend.
#
# Frontend y backend se sirven desde el MISMO ORIGEN a propósito: es lo que
# permite que el frontend llame a `/api` y `/ws` con rutas relativas, sin
# escribir nunca un host ni un puerto (regla de la Fase 0, ver CLAUDE.md).
#
# La misma imagen vale para los dos entornos:
#   - la demo en la web (Railway / Render / Fly.io), un solo servicio
#   - la instalación final en la LAN de la sala, con Docker Compose
#
# Construir y probar en local:
#   docker build -t bingo .
#   docker run --rm -p 8000:8000 bingo      ->  http://localhost:8000

# --- 1. Compilar el frontend -------------------------------------------------
FROM node:24-alpine AS frontend

WORKDIR /app

# Las dependencias se copian aparte para que Docker reutilice esta capa mientras
# no cambien: es lo lento de la construcción.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# --- 2. Backend + el frontend ya compilado -----------------------------------
FROM python:3.13-slim AS runtime

# PYTHONUNBUFFERED: los logs salen al instante, sin quedarse en el buffer. Sin
# esto los mensajes del arranque no aparecen en el panel del proveedor.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FRONTEND_DIST=/app/frontend-dist

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend /app/dist /app/frontend-dist

# Usuario sin privilegios: si algo se cuela por el servidor web, no es root.
RUN useradd --create-home --uid 1000 bingo && chown -R bingo:bingo /app
USER bingo

EXPOSE 8000

# Las migraciones se aplican al arrancar para que un despliegue nuevo no exija
# entrar a la máquina a mano. `${PORT:-8000}` porque Railway y Render asignan el
# puerto por variable de entorno.
#
# Se reintentan unas cuantas veces antes de rendirse. Con SQLite nunca hace
# falta, pero con una base de datos aparte la aplicación y el motor arrancan a la
# vez y la red entre los dos tarda un momento en estar lista: sin reintento, el
# primer despliegue puede morir solo por llegar unos segundos antes que su base,
# que es de lo más desconcertante porque volver a lanzarlo funciona.
# Va escrito aquí dentro y no en un script aparte a propósito: un `.sh` en el
# repositorio se guardaría con finales de línea de Windows y el contenedor
# respondería «bad interpreter», que es un rato perdido buscando dónde.
#
# El `exec` final es importante: deja a uvicorn como proceso principal, de forma
# que reciba la señal de apagado y cierre bien las conexiones.
CMD for intento in 1 2 3 4 5; do \
        alembic upgrade head && break; \
        if [ "$intento" = 5 ]; then \
            echo "No se pudo aplicar las migraciones tras 5 intentos." >&2; \
            exit 1; \
        fi; \
        echo "La base de datos aun no responde; reintento $intento de 5 en 3s..." >&2; \
        sleep 3; \
    done; \
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
