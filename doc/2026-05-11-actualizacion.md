# Flightlog — actualización: Windy Map Forecast API (11 de mayo de 2026)

## Resumen

Integración del **Windy Map Forecast API** para meteorología animada sobre mapa Leaflet oficial de Windy. La clave de API se gestiona sólo mediante variable de entorno (`WINDY_API_KEY`). El widget se muestra como **iframe** a una página mínima del propio proyecto, manteniendo el mapa meteorológico aislado del **Leaflet 1.9** usado para la **vista ortodrómica** en la ficha de vuelo (evitar conflictos de versiones globales).

---

## Configuración

| Variable | Ubicación / uso |
|---------|----------------|
| `WINDY_API_KEY` | Envío al arrancar Django (`export WINDY_API_KEY='…'` en la misma terminal que `manage.py runserver`). Definición en código: `flightlog/settings.py` (`WINDY_API_KEY`). Sin clave, no se renderizan los bloques Windy ni tendrá efecto Docker Compose (si lo usaras). |

**Nota sobre la clave en Windy:** en el alta de la clave conviene seleccionar el servicio **Map Forecast API** y cumplimentar «Project identification» (puede ser localhost en desarrollo, URL futura del despliegue o repositorio público si aplica).

---

## Backend (`logbook`)

### Vistas nuevas / lógica

- **`windy_flight_embed`**: página mínima autenticada para iframe; centro y zoom entre **salida** y **llegada** del vuelo si ambos aeropuertos tienen coordenadas.
- **`windy_dashboard_embed`**: iframe del **panel de control**; centro y zoom deducidos de un conjunto de puntos aeroportuarios: vuelos **en curso**, **próximo planificado** (fecha ≥ hoy) y **recientes** (hasta ~12 filas / 16 puntos ICAO únicos con coordenadas).

### Helpers (reuso de zoom)

- **`_windy_zoom_from_span`**: convierte dispersión angular aproximada en nivel de zoom Windy.
- **`_windy_route_center_zoom`**: dos puntos (ruta de un vuelo).
- **`_windy_center_zoom_from_coords`**: varios puntos (dashboard).
- **`_gather_dashboard_windy_coords`**: recolecta y deduplica coordenadas para el mapa del dashboard.

### Respuestas de error (`windy_*_embed`)

- **503**: clave Windy no configurada.
- **404** (solo embed): falta cualquier aeropuerto utilizable con lat/lon (vuelo concreto o bitácora del usuario según vista).

---

## Rutas (`logbook/urls.py`)

| Ruta nombre | Pattern |
|-------------|---------|
| `windy_flight_embed` | `<int:pk>/windy-embed/` |
| `windy_dashboard_embed` | `dashboard/windy-embed/` |

Colocadas de forma que no colisionan con `<int:pk>/` ni `dashboard/`.

---

## Plantillas y UI

### `templates/logbook/windy_flight_embed.html`

HTML autónomo (sin extender `base.html`): `#windy`, scripts según tutorial oficial [**Map Forecast — Hello world**](https://api4.windy.com/map-forecast/tutorials/hello-world):

- Leaflet cargado desde `unpkg.com/leaflet@1.4.0/dist/leaflet.js`
- `https://api.windy.com/assets/map-forecast/libBoot.js`
- Inicialización con `windyInit(options, …)` y `options` serializado en JSON desde el servidor (incluye `key`, `lat`, `lon`, `zoom`).

### `templates/logbook/flight_detail.html`

- Tarjeta lateral **«Meteorología (Windy)»** cuando `windy_enabled` es verdadero (`WINDY_API_KEY` + coordenadas de al menos uno de los aeródromos del vuelo).
- Estilos compartidos con el iframe (`.fd-windy-*`).

### `templates/logbook/dashboard.html`

- Columna principal envuelta en **`.dash-main-stack`**: primera tarjeta **Últimos vuelos**, segunda **Meteorología (Windy)** si `windy_dashboard_enabled`.
- iframe apuntando a `windy_dashboard_embed`.
- `@media print`: el panel Windy se oculta en impresión.

---

## Docker (opcional)

En `docker-compose.yml`, el servicio `web` puede recibir **`WINDY_API_KEY`** mediante interpolación (`${WINDY_API_KEY:-}`) para quien arranque con Compose y un fichero `.env` en la raíz del repo.

---

## Referencias externas

- Documentación Windy Map Forecast: [api4.windy.com/map-forecast/docs](https://api4.windy.com/map-forecast/docs).
- Alta de clave: [api4.windy.com/api-key/](https://api4.windy.com/api-key/).
- Repositorio de ejemplos (fork informal del histórico `windycom/API`): [github.com/TristanBridge/windycom-api](https://github.com/TristanBridge/windycom-api) — la integración efectiva sigue los scripts/rutas oficiales vigentes enlazadas arriba.

---

## Archivos modificados / añadidos (lista rápida)

- `flightlog/settings.py` — `WINDY_API_KEY`.
- `logbook/views.py` — helpers Windy, `windy_flight_embed`, `windy_dashboard_embed`, contexto `windy_enabled` y `windy_dashboard_enabled`.
- `logbook/urls.py` — rutas embed.
- `templates/logbook/windy_flight_embed.html` — **nuevo**.
- `templates/logbook/flight_detail.html` — bloque Windy + estilos.
- `templates/logbook/dashboard.html` — layout columna izquierda + panel Windy.
- `docker-compose.yml` — variable `WINDY_API_KEY` opcional para Compose.
