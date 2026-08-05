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
| `ADMIN_CLAVE`    | Protege lo que modifica la partida        | vacía (todo abierto)           |
| `FRONTEND_DIST`  | Dónde está el frontend compilado          | lo fija el `Dockerfile`        |
| `APP_VERSION`    | Se ve en `/api/health`                    | `0.1.0`                        |

### La clave de administración

Con la URL pública, cualquiera que tenga el enlace puede entrar a `/admin` y
reiniciar el sorteo en mitad de la demo. `ADMIN_CLAVE` lo evita:

1. En Railway, *Variables* → `ADMIN_CLAVE` = lo que se quiera.
2. La primera vez que se intente cambiar algo, la aplicación la pide y la guarda
   en el navegador. Hay un «Salir de administración» abajo a la derecha.

**Las pantallas del público no la necesitan.** `/transmision` y `/jugador` solo
consultan, y el canal en tiempo real está abierto: el jefe puede abrir su cartón
sin que nadie le dé ninguna clave. Eso es a propósito y hay una prueba que lo
fija.

Que quede claro qué es y qué no: **no es el login de la Fase 2**. No hay
usuarios, ni contraseñas por persona, ni sesiones. Es una tranca para la demo.
Sin definirla, todo queda abierto, que es lo correcto en desarrollo y en la LAN
de la sala.

### Ojo con la base de datos

La demo usa SQLite en un archivo, y **en Railway y Render el disco se borra en
cada despliegue**: las partidas, figuras y cartones desaparecen.

Para que sobrevivan, en Railway:

1. *Settings* → *Volumes* → *New Volume*, con punto de montaje `/data`.
2. *Variables* → `DATABASE_URL` = `sqlite+aiosqlite:////data/bingo.db`
   (**cuatro barras**: tres del esquema más la de la ruta absoluta).
3. Volver a desplegar. Las migraciones crean el esquema solas al arrancar.

> **Si el despliegue falla justo después de montar el volumen**, mira el log: lo
> más probable es un error de permisos al abrir `/data/bingo.db`. La imagen corre
> como un usuario sin privilegios (`USER bingo`) y los volúmenes se montan como
> root. Se arregla dándole permiso a la carpeta desde el panel del proveedor, o
> pasando a PostgreSQL, que no tiene este problema.

La otra ruta es **crear un PostgreSQL** en el mismo proveedor y poner su cadena
en `DATABASE_URL`. No exige tocar código: los modelos se escribieron desde el
principio para funcionar igual en los dos motores (tipo `JSON` genérico y nunca
`JSONB`, `DateTime(timezone=True)`, nada de SQL específico de un motor). Es la
ruta que la Fase 2 va a tomar de todas formas.

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
