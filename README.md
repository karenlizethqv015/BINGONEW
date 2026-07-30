# Plataforma Web de Bingo

Aplicación web para administrar jornadas de bingo en vivo: catálogo de figuras
(formas de ganar), generación de cartones virtuales, balotera, tablero de
transmisión para proyectar en la sala y cartón del jugador con marcado
automático.

La visión final es una instalación **on-premise en la LAN de cada sala, sin
internet**. La versión actual es un MVP que se muestra al cliente antes de
seguir.

- **Contexto de negocio y prioridades:** [CLAUDE.md](CLAUDE.md)
- **Estado del desarrollo y bitácora de decisiones:** [PROGRESS.md](PROGRESS.md)
- **Documento de visión por temas:** [docs/](docs/)

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI · SQLAlchemy 2.0 (async) · Alembic · WebSockets |
| Frontend | React 19 · Vite 8 · TypeScript · TailwindCSS 4 · shadcn/ui |
| Base de datos | SQLite en la demo · PostgreSQL en producción (LAN) |

## Puesta en marcha

Requiere **Python 3.14+** y **Node 24+**. Hacen falta dos terminales.

**Terminal 1 — backend:**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

**Terminal 2 — frontend:**

```powershell
cd frontend
npm install
npm run dev
```

Abrir <http://localhost:5173>. La documentación de la API queda en
<http://127.0.0.1:8000/docs>.

El frontend llama al backend con rutas relativas (`/api`, `/ws`) y el proxy de
Vite las reenvía, así que **los dos servicios deben estar corriendo**.

## Estructura

```
backend/     API FastAPI, modelos, migraciones — ver backend/README.md
frontend/    SPA React — vistas por rol: /admin, /transmision, /jugador, /vendedor
docs/        Documento de visión dividido por tema
```

## Estado

**Fase 0 (scaffolding) completa.** No hay funcionalidad de negocio todavía: la
Fase 1 arranca con el módulo de creación de figuras. El detalle está en
[PROGRESS.md](PROGRESS.md).
