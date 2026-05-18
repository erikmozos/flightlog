# Flightlog

Aplicación web en **Django** para el **registro y consulta de vuelos** con un enfoque didáctico/operativo:
planificación del vuelo, arranque y paro de motores, cálculo automático de tiempo de motor, cartas
aeronáuticas asociadas a los aeródromos y vista meteorológica integrada con Windy.

> Para una descripción detallada del dominio, modelo de datos y decisiones de diseño consulta
> [`ARCHITECTURE.md`](ARCHITECTURE.md). Las notas de desarrollo viven en [`doc/`](doc/).

---

## Funcionalidades

- **Bitácora por piloto:** cada usuario ve solo sus vuelos.
- **Ciclo de vida del vuelo:** `PLANNED` → `IN_PROGRESS` → `COMPLETED` (o `CANCELLED`), con marcado de
  encendido/apagado de motor y cálculo de `total_time` al finalizar.
- **Catálogos administrables** desde `/admin/`:
  - **Aeronaves** (matrícula, fabricante, modelo, código OACI, categoría).
  - **Aeropuertos** (ICAO, ciudad, país, coordenadas).
  - **Navaids** (VOR, NDB, DME, fixes…) importables desde OurAirports.
  - **Cartas** (PDF subido y/o URL externa) por aeropuerto y tipo (AIRPORT, APPROACH, SID, STAR, TAXI, OTHER).
- **Importación de planes SimBrief** (XML Datafile recomendado, fallback de texto) que crea un vuelo
  `PLANNED` con ruta, alternativo, combustibles y horarios previstos.
- **Cartas en el detalle del vuelo:** se listan agrupadas por tipo las cartas activas de salida y llegada.
- **Dashboard del piloto:** próximo vuelo previsto, vuelo en curso, horas acumuladas, aterrizajes
  recientes y mapa Windy contextual.
- **Mapa meteorológico Windy** embebido en el detalle del vuelo y en el dashboard cuando hay
  `WINDY_API_KEY` configurada.
- **Búsqueda y paginación** en el listado por aeronave, ICAO, ciudad o número de vuelo.

---

## Tecnologías

- **Backend:** Django 6.0 (vistas en función, templates).
- **Base de datos:** SQLite por defecto; PostgreSQL si se define `DATABASE_URL` (vía `dj-database-url`).
- **Servidor de producción:** Gunicorn + WhiteNoise (estáticos).
- **Frontend:** plantillas HTML del proyecto + integración Windy Map Forecast API (opcional).
- **Python:** 3.12 (imagen Docker `python:3.12-slim-bookworm`).

Dependencias declaradas en [`requirements.txt`](requirements.txt):

```
Django>=6.0,<6.1
gunicorn>=23.0,<24
whitenoise>=6.8,<7
dj-database-url>=2.1,<3
psycopg[binary]>=3.2,<4
```

---

## Estructura del proyecto

```
flightlog/
├── flightlog/        # Configuración Django (settings, urls raíz, wsgi/asgi)
├── aircraft/         # Catálogo de aeronaves
├── airports/         # Catálogo de aeropuertos y navaids (+ import OurAirports)
├── charts/           # Cartas aeronáuticas (PDF / URL) por aeropuerto
├── logbook/          # Núcleo: FlightLog, vistas, dashboard, import SimBrief
├── users/            # Login, registro y logout (auth de Django)
├── templates/        # base.html + plantillas de logbook/ y users/
├── deployment/       # Dockerfile y entrypoint
├── doc/              # Notas de desarrollo
├── manage.py
├── requirements.txt
└── docker-compose.yml
```

Apps en `INSTALLED_APPS`: `users`, `aircraft`, `airports`, `logbook`, `charts`.

---

## Puesta en marcha local (sin Docker)

Requiere Python 3.12.

```bash
git clone <repo>
cd flightlog

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
```

La aplicación queda en `http://127.0.0.1:8000/` (redirige a `/flights/dashboard/`) y el admin en `/admin/`.

### Datos iniciales útiles

- Importar aeropuertos y navaids desde OurAirports:

  ```bash
  python manage.py import_ourairports
  ```

- Cargar cartas de demostración:

  ```bash
  python manage.py seed_demo_charts
  ```

- Importar cartas reales desde una carpeta local:

  ```bash
  python manage.py import_real_charts
  ```

---

## Despliegue con Docker

El [`deployment/Dockerfile`](deployment/Dockerfile) construye una imagen con Gunicorn + WhiteNoise.
El entrypoint aplica `migrate` automáticamente en cada arranque.

```bash
docker build -f deployment/Dockerfile -t flightlog .

docker volume create flightlog_data
docker volume create flightlog_media

docker run --rm -p 8000:8000 \
  -e DJANGO_SECRET_KEY="cambia-esta-clave-en-produccion-min-50-chars-xx" \
  -e DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1" \
  -e DJANGO_CSRF_TRUSTED_ORIGINS="http://127.0.0.1:8000,http://localhost:8000" \
  -e DJANGO_SQLITE_PATH=/app/data/db.sqlite3 \
  -e DJANGO_SERVE_MEDIA=1 \
  -e WINDY_API_KEY="${WINDY_API_KEY:-}" \
  -v flightlog_data:/app/data \
  -v flightlog_media:/app/media \
  --name flightlog \
  flightlog
```

La app queda en `http://127.0.0.1:8000/`. Crea el superusuario con el contenedor en marcha:

```bash
docker exec -it flightlog python manage.py createsuperuser
```

Los volúmenes `flightlog_data` (SQLite) y `flightlog_media` (PDF de cartas) sobreviven a
recreaciones del contenedor.

---

## Variables de entorno

Definidas en `flightlog/settings.py` y consumidas también por `docker-compose.yml`:

| Variable | Por defecto | Propósito |
|----------|-------------|-----------|
| `DJANGO_DEBUG` | `1` en local, `0` en Docker | Modo debug. |
| `DJANGO_SECRET_KEY` | clave insegura embebida | **Obligatoria en producción** (mín. 50 caracteres recomendado). |
| `DJANGO_ALLOWED_HOSTS` | vacío (`localhost,127.0.0.1` en Docker) | Hosts permitidos, separados por coma. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | vacío | Orígenes confiables para CSRF (con esquema). |
| `DATABASE_URL` | sin definir | Si se define, Django usa PostgreSQL/Neon/etc. en lugar de SQLite. |
| `DJANGO_SQLITE_PATH` | `BASE_DIR/db.sqlite3` (`/app/data/db.sqlite3` en Docker) | Ruta del SQLite cuando no hay `DATABASE_URL`. |
| `DJANGO_SERVE_MEDIA` | `0` | Si vale `1`, Django sirve `/media/` (útil en contenedor; no en producción de alto tráfico). |
| `WINDY_API_KEY` | vacío | Clave de [Windy Map Forecast API](https://api4.windy.com/api-key/). Sin clave no se muestra el mapa meteorológico. |
| `GUNICORN_WORKERS` | `1` | Workers de Gunicorn dentro del contenedor. |

Idioma `es`, zona horaria `Europe/Madrid` (definidos en settings).

---

## Rutas principales

| Ruta | Descripción |
|------|-------------|
| `/` | Redirige al dashboard del piloto. |
| `/users/login/`, `/users/register/`, `/users/logout/` | Autenticación. |
| `/flights/dashboard/` | Resumen del piloto. |
| `/flights/` | Listado paginado y búsqueda. |
| `/flights/new/` | Crear vuelo manualmente. |
| `/flights/import/` | Importar OFP de SimBrief (XML o texto). |
| `/flights/<id>/` | Detalle: estado, acciones de inicio/fin, cartas, mapa Windy. |
| `/flights/<id>/start/` (POST) | PLANNED → IN_PROGRESS (registra `engine_start_time`). |
| `/flights/<id>/finish/` (POST) | IN_PROGRESS → COMPLETED (registra `engine_stop_time` y `total_time`). |
| `/flights/<id>/windy-embed/`, `/flights/dashboard/windy-embed/` | Iframes con el mapa Windy. |
| `/admin/` | Sitio de administración de Django. |

---

## Tests

```bash
python manage.py test
```

Los módulos `tests.py` están presentes en cada app como esqueleto para ampliar la cobertura.

---

## Documentación adicional

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — arquitectura, dominio y flujo del proyecto.
- [`doc/`](doc/) — bitácora de cambios y notas de diseño (mapa SimBrief, cartas, interfaz, etc.).
