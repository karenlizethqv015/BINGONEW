# 06 — Arquitectura Recomendada

> Fuente: dividido desde `vision-proyecto-bingo_1.md`, sección 6. No omite información del original.

## Entorno de despliegue (visión final de producto)

- Se descarta la nube como requisito: el backend corre en un servidor local (un PC/mini-servidor dentro de la sala) conectado a la misma red LAN que los computadores de administrador, vendedor y jugadores.
- Acceso vía navegador a `http://<ip-lan-del-servidor>:puerto`.
- Se recomienda igualmente Docker Compose (backend + frontend + base de datos) para que el mismo paquete se instale igual en cualquier sala, sin importar que no haya internet — las imágenes se construyen una vez y se replican.

## Backend

- **FastAPI** (Python) — async, tipado, soporta **WebSockets** de forma nativa (necesarios para transmitir balotas en tiempo real dentro de la LAN).
- **SQLAlchemy 2.0** como ORM + **Alembic** para migraciones.
- **PostgreSQL** como base de datos (correrá en el mismo servidor local).
- **Pydantic** para validación de esquemas.
- **JWT** para autenticación de administrador/vendedor; sesión simple por cédula para el jugador.
- Redis es opcional aquí: al ser una sola instancia por sala (no múltiples servidores), no es indispensable para el pub/sub de WebSockets; se puede manejar en memoria del propio proceso FastAPI. Se deja como mejora futura si una sala llegara a necesitar más de un servidor.

## Frontend

- **React + Vite + TypeScript**.
- **TailwindCSS**, con un layout pensado primero para pantallas de escritorio (grillas fijas tipo la del cantador) y adaptado de forma secundaria a pantallas más pequeñas.
- WebSocket nativo (o `socket.io-client` si se opta por Socket.IO) para recibir balotas y eventos en tiempo real.
- Vistas por rol: `/admin`, `/vendedor`, `/jugador`.

## Comunicación en tiempo real

- FastAPI expone un endpoint WebSocket por partida.
- Cuando el administrador "canta" una balota, el backend la guarda y emite el evento a todos los clientes conectados a esa partida en la LAN.

## Diagrama de alto nivel

```
   [Jugador]      [Vendedor]      [Administrador]
   (navegador)    (navegador)     (navegador)
        \              |               /
         \             |              /
          +------------+-------------+
                       |
              Red LAN de la sala
                       |
             React (Vite) SPA
                       |
          HTTP / WebSocket (solo LAN)
                       |
             FastAPI Backend
             /                  \
       SQLAlchemy              Auth (JWT)
             |
        PostgreSQL
      (servidor local de la sala)
```

## Nota: arquitectura específica para el MVP de demo web

Para la demo al cliente (fase 1, ver `PROGRESS.md`), se recomienda mantener el mismo stack (React + Vite + TypeScript + Tailwind en frontend, FastAPI + WebSockets en backend) pero desplegado temporalmente en servicios web accesibles por URL (ej. frontend en Vercel/Netlify, backend en Railway/Render/Fly.io, base de datos gestionada tipo Postgres en la nube o SQLite si se busca máxima velocidad). Esto no cambia el diseño del código: el mismo backend FastAPI que corre en la nube para la demo es el que luego se empaqueta con Docker Compose para instalarse en la LAN de cada sala. Ver detalle de decisión en `PLAN-CLAUDE-CODE.md`.
