# Backend — API del Bingo

FastAPI + SQLAlchemy 2.0 (async) + Alembic. Expone la API HTTP y el canal
WebSocket que transmite las balotas en tiempo real.

## Puesta en marcha

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env          # opcional: los valores por defecto ya sirven
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000` y la documentación interactiva en
`http://127.0.0.1:8000/docs`.

## Base de datos: los dos motores a la vez

**Los dos drivers vienen instalados** y el que se usa lo decide `DATABASE_URL`:

- **SQLite** (`aiosqlite`) por defecto, para desarrollo y pruebas. Arranca sin
  levantar nada.
- **PostgreSQL** (`asyncpg`) en la demo desplegada y en la instalación final en
  la LAN de la sala.

Cambiar de uno a otro es solo cambiar `DATABASE_URL`, y **la cadena se puede
pegar tal como la entrega el proveedor**: `normalizar_url_de_base_de_datos`, en
`app/config.py`, le pone el driver asíncrono si viene como `postgresql://` y le
quita los parámetros de `libpq` (`sslmode` y compañía) que asyncpg no entiende.
Se hace en la configuración y no en `db.py` porque `alembic/env.py` lee la misma
variable: así quedan bien la aplicación y las migraciones de una vez.

Para probar contra PostgreSQL de verdad está el `docker-compose.yml` de la raíz.
La suite entera se puede correr contra él:

```powershell
docker compose up -d postgres
$env:TEST_DATABASE_URL = "postgresql+asyncpg://bingo:bingo@localhost:5432/bingo"
.\.venv\Scripts\python.exe -m pytest
```

Sin esa variable, las pruebas siguen usando SQLite en memoria y tardan segundos.

El objetivo de las reglas de abajo es que ese cambio de motor no exija tocar
ningún modelo, y hoy se cumple: pasar la demo a PostgreSQL no obligó a cambiar ni
uno solo.

Para que eso siga siendo cierto, todo modelo nuevo debe respetar estas reglas:

1. **Tipos genéricos, nunca específicos de un motor.** Usar `JSON` de
   SQLAlchemy, jamás `JSONB` ni `postgresql.ARRAY`. Aplica a `figura.patron` y
   `carton.numeros`.
2. **Fechas con zona horaria:** `DateTime(timezone=True)` con
   `server_default=func.now()`.
3. **Nada de SQL crudo específico de SQLite** (`AUTOINCREMENT`, pragmas, etc.).
4. **`render_as_batch=True`** ya está activo en `alembic/env.py`. Es lo que
   permite que los `ALTER TABLE` funcionen en SQLite; en PostgreSQL es
   inofensivo. No quitarlo.
5. **`DATABASE_URL` siempre por variable de entorno**, nunca escrita en el
   código ni en `alembic.ini`.

6. **Los enums van con `native_enum=False`**, es decir, guardados como texto con
   un CHECK. SQLite no tiene ENUM, y en PostgreSQL cambiarle los valores a un
   tipo ENUM obliga a una migración incómoda. Ver `app/models/partida.py`.

Para apuntar a PostgreSQL basta con definir la variable; cualquiera de las dos
formas vale:

```
DATABASE_URL=postgresql://usuario:clave@servidor:5432/bingo
DATABASE_URL=postgresql+asyncpg://usuario:clave@servidor:5432/bingo
```

## Migraciones

```powershell
# Crear una migración a partir de los cambios en los modelos
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "descripcion"

# Aplicar / revertir
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic downgrade -1
```

> **Cuidado:** Alembic solo detecta los modelos que estén importados en
> `app/models/__init__.py`. Si un modelo no aparece ahí, la migración se genera
> **vacía y sin avisar**. Revisar siempre el archivo generado antes de aplicarlo.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest                       # toda la suite
.\.venv\Scripts\python.exe -m pytest tests/test_health.py   # un archivo
.\.venv\Scripts\python.exe -m pytest tests/test_health.py::test_health_responde_ok   # un test
.\.venv\Scripts\python.exe -m pytest -k websocket           # por coincidencia de nombre
```

`asyncio_mode = auto` está activo en `pytest.ini`: los tests asíncronos no
necesitan el decorador `@pytest.mark.asyncio`.

## Estructura

| Ruta | Contenido |
|---|---|
| `app/config.py` | Configuración desde entorno/`.env` |
| `app/db.py` | Engine async, sesiones y `Base` del ORM |
| `app/models/` | Modelos del ORM (vacío en Fase 0) |
| `app/routers/` | Routers HTTP |
| `app/realtime/manager.py` | Gestor de conexiones WebSocket por canal |
| `alembic/` | Migraciones |

## Sobre el WebSocket

`/ws/echo` es solo una prueba del canal en tiempo real. En la Fase 1 se agrega
el endpoint real (uno por partida) reutilizando el mismo `GestorConexiones`.

Las conexiones se guardan **en memoria del proceso**, sin Redis: cada sala corre
una sola instancia del backend en su LAN, así que no hace falta pub/sub
distribuido (ver `docs/06-arquitectura.md`).
