# Desplegar la demo

Cómo poner la aplicación en una URL pública para enseñársela al cliente, y por
qué está montada así.

## La decisión: un solo servicio, no dos

`docs/06-arquitectura.md` sugería *frontend en Vercel/Netlify, backend en
Railway/Render*. **No se hizo así**, y el motivo importa:

El frontend llama al backend con rutas relativas (`/api/...`, `/ws/...`) — es una
regla del proyecto desde la Fase 0. Separar frontend y backend en dos dominios
obligaría a escribir el host del backend en el código del frontend, que es
exactamente lo que esa regla prohíbe, y lo que haría que la instalación en la
LAN de la sala dejara de funcionar.

Así que **el backend sirve también el frontend compilado**. Todo en un origen:

- No hay CORS que configurar ni URLs que recordar.
- El WebSocket se conecta solo, con `window.location.host`.
- Es **la misma forma** que tendrá la instalación final en la sala, así que lo
  que se prueba en la demo es lo que se va a instalar, no un primo lejano.
- Una cuenta en un proveedor en vez de dos.

En desarrollo esto no cambia nada: sigue habiendo dos procesos (uvicorn y Vite
con su proxy), porque hacen falta el recargado en caliente y el compilador.

## Probarlo en local antes de subir nada

Merece la pena: es exactamente lo que va a correr en el servidor.

```powershell
cd frontend
npm run build          # genera frontend/dist

cd ..\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

Ahora **todo** está en `http://localhost:8000` — sin Vite: la aplicación, la API
y el WebSocket. Si al arrancar aparece «Sirviendo el frontend compilado desde…»,
lo encontró. Si dice «Sin frontend compilado», falta `npm run build`.

## Con Docker

La imagen construye el frontend y lo mete dentro del backend:

```powershell
docker build -t bingo .
docker run --rm -p 8000:8000 bingo     # http://localhost:8000
```

Las migraciones se aplican solas al arrancar.

## Subirlo a la web

Sirve cualquier proveedor que sepa construir un `Dockerfile`. **Hace falta una
cuenta tuya**, así que este paso no está hecho.

### Railway (el camino más corto)

1. Entrar en [railway.app](https://railway.app) con la cuenta de GitHub.
2. *New Project* → *Deploy from GitHub repo* → elegir `BINGONEW`.
3. Railway detecta el `Dockerfile` de la raíz y construye. No hay que configurar
   ningún comando de arranque: ya está en la imagen.
4. *Settings* → *Networking* → *Generate Domain*. Esa es la URL de la demo.

Render y Fly.io funcionan igual de bien; el `Dockerfile` es el mismo.

### Variables de entorno

Ninguna es obligatoria para la demo. Las que existen:

| Variable         | Para qué                                  | Por defecto                    |
| ---------------- | ----------------------------------------- | ------------------------------ |
| `PORT`           | Lo pone el proveedor solo                 | `8000`                         |
| `DATABASE_URL`   | Dónde vive la base de datos               | SQLite en `./bingo.db`         |
| `ADMIN_CLAVE`    | Protege el catálogo de figuras            | vacía (todo abierto)           |
| `OPERADOR_CLAVE` | Protege partidas, balotera y cartones     | vacía (todo abierto)           |
| `FRONTEND_DIST`  | Dónde está el frontend compilado          | lo fija el `Dockerfile`        |
| `APP_VERSION`    | Se ve en `/api/health`                    | `0.1.0`                        |

### Las claves de administración y operador

Con la URL pública, cualquiera que tenga el enlace puede entrar a `/admin` o
`/operador` y tocar el catálogo o reiniciar el sorteo en mitad de la demo.
`ADMIN_CLAVE` y `OPERADOR_CLAVE` lo evitan, una por rol:

1. En Railway, *Variables* → `ADMIN_CLAVE` = lo que se quiera, `OPERADOR_CLAVE`
   = otra cosa distinta (no tiene que ser la misma; de hecho es mejor que no lo
   sea, para que un vendedor con la clave de operador no pueda tocar el
   catálogo de figuras).
2. La primera vez que se intente cambiar algo, la aplicación pide la clave que
   corresponda y la guarda en el navegador. Hay un «Salir de administración» y
   un «Salir de operación» abajo a la derecha, uno encima del otro si las dos
   están puestas.

**Las pantallas del público no las necesitan.** `/transmision` y `/jugador` solo
consultan, y el canal en tiempo real está abierto: el jefe puede abrir su cartón
sin que nadie le dé ninguna clave. Eso es a propósito y hay una prueba que lo
fija.

Que quede claro qué son y qué no: **no son el login de la Fase 2**. No hay
usuarios, ni contraseñas por persona, ni sesiones. Son una tranca para la demo.
Sin definirlas, todo queda abierto, que es lo correcto en desarrollo y en la LAN
de la sala.

### La base de datos: PostgreSQL

La demo arranca sobre SQLite en un archivo, y **en Railway y Render el disco se
borra en cada despliegue**: las partidas, figuras y cartones desaparecen. Para
que sobrevivan, lo recomendado es **crear un PostgreSQL en el mismo proveedor**.

Además de conservar los datos, quita de en medio el problema de los volúmenes:
la imagen corre como usuario sin privilegios y los volúmenes se montan como
root, así que montar uno para el archivo de SQLite puede fallar por permisos en
el primer arranque. Con PostgreSQL no hay ningún archivo que persistir. Es
también la ruta que la Fase 2 iba a tomar igualmente, y la forma que tendrá la
instalación final en la sala.

#### Paso a paso en Railway

1. En el proyecto: **New → Database → Add PostgreSQL**. Aparece como un servicio
   propio, al lado del de la aplicación.
2. En el servicio **de la aplicación** —no en el de la base— → *Variables* →
   añadir `DATABASE_URL` con el valor `${{Postgres.DATABASE_URL}}`.
3. Volver a desplegar. En los logs deben verse las migraciones aplicándose una a
   una: el arranque hace `alembic upgrade head` solo.
4. Comprobarlo de verdad: entrar, crear una figura, **volver a desplegar** y ver
   que la figura sigue ahí. Es justo lo que fallaba antes.

> **El paso 2 es el que se salta todo el mundo.** Railway no comparte las
> variables entre servicios: crear la base no basta. Sin esa referencia la
> aplicación no da ningún error — simplemente sigue escribiendo en su SQLite
> efímero, y los datos vuelven a desaparecer en el despliegue siguiente.
>
> `Postgres` es el nombre que Railway le pone al servicio. Si lo renombraste, la
> referencia lleva el nombre nuevo.

Si tenías un volumen montado para `/data/bingo.db`, ya se puede quitar junto con
su `DATABASE_URL`. `ADMIN_CLAVE` no tiene nada que ver y se queda como esté.

#### La cadena se pega tal cual

No hace falta editarla. Railway (y Render, y Neon, y Heroku) entregan una URL
pensada para clientes síncronos, y la aplicación la arregla sola al leerla
(`normalizar_url_de_base_de_datos`, en `backend/app/config.py`): le pone el
driver `asyncpg` y le quita los parámetros de `libpq` como `sslmode`, que
`asyncpg` no entiende y que si no provocan un `TypeError` desconcertante, sin
mencionar en ningún momento que el problema está en la URL.

Los modelos ya eran compatibles con los dos motores desde la Fase 0 (tipo `JSON`
genérico y nunca `JSONB`, `DateTime(timezone=True)`, enums guardados como texto,
nada de SQL específico de un motor), así que no hubo que tocar ninguno.

#### Probarlo antes en el equipo

Merece la pena correrlo contra PostgreSQL de verdad antes de subir nada:

```powershell
docker compose up --build      # http://localhost:8000
```

Y pasar la suite entera contra ese mismo motor, que es lo que de verdad dice que
la aplicación se comporta igual en los dos:

```powershell
docker compose up -d postgres
cd backend
$env:TEST_DATABASE_URL = "postgresql+asyncpg://bingo:bingo@localhost:5432/bingo"
.\.venv\Scripts\python.exe -m pytest
```

Tarda bastante más que contra SQLite, porque crea y destruye el esquema en cada
prueba. Para el trabajo del día a día no hace falta: sin `TEST_DATABASE_URL` la
suite sigue usando SQLite en memoria y tarda segundos.

## Enseñarle la demo a otra persona

Con la aplicación en una URL pública **no hace falta ninguna red local**: quien
la vea abre el enlace desde donde esté, con su propio celular. Lo que hace que
funcione es que todas las pantallas se alimentan del **mismo WebSocket de la
partida**: uno canta las balotas y las demás reaccionan solas.

**Antes**, con calma: crear las figuras en `/admin/figuras`, la partida en
`/admin/partidas` con sus formas y premios, y generar los cartones.

**Durante:**

| Quién              | Dónde                                    |
| ------------------ | ---------------------------------------- |
| Quien dirige       | `/admin/partidas/{id}/balotera`          |
| La sala / el TV    | `/transmision?partida={id}`              |
| El invitado        | `/jugador?partida={id}&carton=A-7`       |

Para el invitado no hace falta dictarle esa dirección: en la pantalla de cartones,
cada cartón tiene un botón **«Enlace y QR»**. Se le enseña el QR, lo escanea con
la cámara y entra directo a su cartón.

Lo que se ve al cantar: el número aparece a la vez en el tablero de la sala y en
el celular del invitado, **y su cartón se marca solo**. Cuando alguien completa
una forma, **el sorteo se detiene solo**, salta el aviso de bingo en la pantalla
de mando y el ¡BINGO! sobre el cartón del ganador. Se reanuda con el botón del
propio aviso.

### Sin internet, en una red local

Es la forma que tendrá la instalación definitiva. En el PC que haga de servidor:

```powershell
docker build -t bingo .
docker run -d -p 8000:8000 -v bingo-datos:/data `
  -e DATABASE_URL=sqlite+aiosqlite:////data/bingo.db bingo
```

Abrir el puerto una sola vez, en PowerShell **como administrador**:

```powershell
New-NetFirewallRule -DisplayName "Bingo" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

Los demás equipos y celulares entran a `http://<ip-del-servidor>:8000` (la IP
sale de `ipconfig`). **No hay que recompilar nada** para pasar de la nube a la
red local: como el frontend no lleva ningún host escrito, se conecta solo a donde
esté servido.

## Después: la instalación en la sala

Es el mismo `Dockerfile`, corriendo en el PC de la sala en vez de en la nube, con
PostgreSQL al lado en un `docker-compose.yml`. Los navegadores de la sala entran
a `http://<ip-del-servidor>:8000`. Como no hay ningún host escrito en el
frontend, **no hay que recompilar nada** para cambiar de la nube a la LAN.
