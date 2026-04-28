# Arquitectura de Flightlog

Documento de arquitectura del proyecto **Flightlog** (Django, SQLite, plantillas, vistas en funciones). Incluye el **concepto funcional objetivo** y, en cada sección relevante, qué hay **realmente implementado** en el repositorio en la fecha de este documento.

---

## 1. Overview

**Flightlog** es una aplicación web pensada para el **registro y consulta de vuelos** en un entorno académico: datos de aeronave, ruta, tiempos de bloque y notas, con una capa pública sencilla (lista, alta y detalle) y un panel de administración para el mantenimiento de catálogos.

- **Tecnología:** Django (p. ej. 6.0.x según `flightlog/settings.py`), base de datos **SQLite** por defecto, **sin dependencias de terceros** fuera del propio ecosistema Django.
- **Interfaz:** **templates** HTML; **vistas basadas en funciones**; **no** hay API REST en el árbol de URLs actual.

---

## 2. Functional Concept

### Objetivo de producto (flujo funcional deseado)

1. **Vuelo previsto** — planificar ruta, aeronave y fechas/horas antes o al inicio de la operación.  
2. **Vuelo en curso** — registrar el momento en que se **arrancan** los motores o se inicia el bloque operativo.  
3. **Vuelo completado** — cerrar el vuelo y registrar el cierre; la duración debería calcularse **automáticamente** a partir de instantes de inicio y fin.  
4. **Cartas aeronáuticas** — asociar y consultar, desde el detalle de un vuelo, **cartas de salida y llegada** (y otras) ligadas a los aeropuertos de la ruta.

### En el código hoy

El dominio y la interfaz actuales implementan un **registro de vuelo en un solo paso**: el usuario introduce fecha, aeronave, aeropuertos, **`block_off`**, **`block_on`** y notas. El **tiempo total** se calcula al guardar. **No** existen aún acciones separadas de “iniciar” o “finalizar” vuelo, ni estados explícitos en el modelo, ni un modelo de cartas; la app `charts` está creada pero **sin modelos** registrados. El apartado 5 detalla el modelo de estados **previsto** frente a la **implementación actual**.

---

## 3. Project Structure

Django carga en `INSTALLED_APPS` las aplicaciones listadas a continuación. El paquete de configuración del proyecto es **`flightlog/`** (settings, `urls.py` raíz, `wsgi`/`asgi`).

| App / paquete | Rol |
|---------------|-----|
| **`flightlog`** | Configuración global: `ROOT_URLCONF`, `TEMPLATES` (`templates/` a nivel de proyecto + `APP_DIRS`), base de datos SQLite, zona horaria (p. ej. `Europe/Madrid`), `STATIC_URL`, apps instaladas. |
| **`aircraft`** | Modelo y admin de **aeronaves** (matrícula, fabricante, modelo). No expone URLs propias; se usa vía `ForeignKey` y admin. |
| **`airports`** | Modelo y admin de **aeropuertos** (ICAO, nombre, ciudad, país). Misma idea: catálogo consumido por el logbook y el admin. |
| **`logbook`** | **Núcleo de la lógica de negocio visible en web:** `FlightLog`, formulario, vistas (`flight_list`, `flight_create`, `flight_detail`) y `urls` bajo el prefijo incluido en el proyecto. |
| **`charts`** | **Reservada** para cartas aeronáuticas: a día de hoy no hay modelos en `charts/models.py` ni URLs de usuario; el admin de charts está vacío. |
| **`core`** | App vacía a nivel de modelos; sirve de placeholder o extensión futura (sin lógica en el código inspeccionado). |
| **`users`** | App vacía a nivel de modelos; no sustituye el modelo de usuario y no añade flujo de registro/login en URLs. |

Las plantillas compartidas viven en **`templates/`** a la raíz (no dentro de `logbook/`), p. ej. `base.html` y `logbook/*.html`.

---

## 4. Domain Model

### `aircraft.Aircraft`

- **Identificación de la aeronave** para asociarla a vuelos.
- Campos importantes: `registration`, `manufacturer`, `model`.
- **Relación:** un `Aircraft` tiene muchos `FlightLog` (`related_name="flight_logs"`).

### `airports.Airport`

- **Catálogo de aeropuertos** por código ICAO de 4 letras.
- Campos: `icao_code`, `name`, `city`, `country`.
- **Relaciones:** un `Airport` puede ser **salida** o **llegada** de muchos vuelos (`departure_flights` / `arrival_flights` vía `ForeignKey` en `FlightLog`).

### `logbook.FlightLog`

- **Un tramo de vuelo** con fecha, aeronave, origen y destino.
- Campos: `date`, `aircraft`, `departure_airport`, `arrival_airport`, `block_off`, `block_on`, `total_time` (calculado, no editable en formularios de usuario), `remarks`.
- **Orden por defecto:** vuelos más recientes primero (`Meta.ordering`).

> **Nota sobre el diseño deseado:** en una evolución del dominio, “block off / block on” puede alinearse con **arranque y paro de motores** u otros instantes; hoy el modelo nombra explícitamente `block_off` y `block_on` y no campos `engine_start_time` / `engine_stop_time`.

### `Chart` (diseño previsto, no presente aún en modelos)

El concepto de producto prevé un modelo del estilo **Chart** (en la app `charts`) vinculado a un `Airport`, con un tipo de carta. En el repositorio actual, **`charts/models.py` no define clases**; la tabla de tipos enumerada (AIRPORT, APPROACH, SID, STAR, TAXI, OTHER) aplica al **diseño futuro** de normalización y administración de cartas.

---

## 5. Flight Lifecycle

### Modelo de estados (diseño orientativo)

| Estado | Significado (intención) |
|--------|------------------------|
| `PLANNED` | Vuelo planificado, sin inicio de operación registrado. |
| `IN_PROGRESS` | Operación en curso (p. ej. motores en marcha o bloque iniciado). |
| `COMPLETED` | Vuelo cerrado; tiempos finales fijados. |
| `CANCELLED` | Vuelo anulado sin cierre en condiciones normales. |

### Transiciones (intención)

| Transición | Efecto esperado en el producto final |
|------------|--------------------------------------|
| **Crear** | Registrar un vuelo previsto; puede quedar en `PLANNED` o, según criterio de producto, completarse con tiempos en un solo paso. |
| **Iniciar** | Marcar inicio (p. ej. arranque de motores) y pasar a `IN_PROGRESS`. |
| **Finalizar** | Registrar cierre, calcular duración, pasar a `COMPLETED`. |

### En el código hoy

- **`FlightLog` no declara** un campo de estado ni constantes `PLANNED` / `IN_PROGRESS` / etc.  
- El flujo web es: **crear** con `block_off` y `block_on` ya rellenados, **listar** y **ver detalle** — sin vistas dedicadas a “iniciar” o “finalizar”.

---

## 6. Time Calculation Logic

La duración almacenada en **`total_time`** se calcula en **`FlightLog.save()`**, no a partir de campos con nombre `engine_*` (esos nombres no existen en el modelo actual).

1. Se llama a **`duration_block_to_block(block_off, block_on)`** en `logbook/models.py`.  
2. Toma el **día de hoy** del sistema y combina con las horas `TimeField` (interpretación de “día de referencia” en el cálculo; el propio vuelo usa `date` en otros contextos de visualización).  
3. Si **`block_on` < `block_off`**, se asume un **cruce de medianoche** y se añade un día al instante de llegada.  
4. El resultado es un `timedelta` almacenado en **`total_time`**.  
5. **Siempre** que se guarda un `FlightLog` con `block_off` y `block_on` definidos, se recalcula; no hay rama con “solo uno de los dos instantes” en el cálculo (ambos participan y son obligatorios a nivel de modelo `TimeField`).

> Para un futuro con **sólo** instantes de arranque/paro de motor y estados, habría que ajustar validación, momentos faltantes y coherencia con el campo `date` del vuelo.

---

## 7. Charts Integration (diseño y situación actual)

- **Asociación a aeropuerto:** en diseño, las cartas se enlazarían a **`Airport`**; hoy no hay modelo `Chart` ni `ForeignKey` en `Airport`.  
- **Detalle de vuelo:** `flight_detail` solo pasa el objeto `flight` a la plantilla; **no** hay consulta a cartas ni listado por salida/llegada.  
- **Tipos de carta (referencia de diseño):** AIRPORT, APPROACH, SID, STAR, TAXI, OTHER — a usar cuando se implemente el modelo y el admin.  
- Carga o enlace a PDFs/URLs de proveedores sería **manual** hasta integraciones automáticas (ver limitaciones y mejoras futuras).

---

## 8. Request Flow

Patrón común: **URL → vista (función) → (opcional) `ModelForm` → modelo → `render` con contexto → plantilla.**

| Flujo | URL (espacio de nombres `logbook`) | Vista | Form / modelo | Plantilla |
|--------|-------------------------------------|-------|---------------|-----------|
| **Lista** | `""` — `/flights/` | `flight_list` | Ninguno; `FlightLog.objects...all()` | `logbook/flight_list.html` |
| **Crear** | `new/` — `/flights/new/` | `flight_create` | `FlightLogForm` (POST) → `save()` | `logbook/flight_form.html` |
| **Detalle** | `<int:pk>/` — `/flights/<id>/` | `flight_detail` | `get_object_or_404(FlightLog, pk=…)` | `logbook/flight_detail.html` |
| **Iniciar / finalizar** (concepto) | *No existen* rutas o vistas aún; formaría parte de una ampliación del ciclo de vida. |
| **Detalle con cartas** (concepto) | Misma ruta de detalle en el futuro, ampliando la vista o el contexto con cartas asociadas a `departure_airport` y `arrival_airport`. |

En `flightlog/urls.py`, el prefijo **`flights/`** incluye `logbook.urls`.

---

## 9. Templates

Plantillas bajo el directorio de proyecto `templates/`, reutilizando `base.html`:

| Fichero | Uso |
|---------|-----|
| `base.html` | Cabecera con enlaces a lista y “Nuevo vuelo”; `{% block title %}` y `{% block content %}`. |
| `logbook/flight_list.html` | Listado con enlaces al detalle; muestra `total_time`. |
| `logbook/flight_form.html` | Formulario de creación (tabla de campos, CSRF, POST a la misma URL). |
| `logbook/flight_detail.html` | Ficha: aeronave, aeropuertos, `block_off`, `block_on`, `total_time`, notas. |

**No** hay plantilla específica aún para listados de cartas; encajaría en una evolución de `flight_detail` o en vistas dedicadas a `charts`.

---

## 10. Admin Site

El **sitio de administración** (`/admin/`) concentra el mantenimiento de catálogos y la inspección de vuelos.

- **Aeronaves:** `aircraft` — listado, búsqueda por matrícula/fabricante/modelo.  
- **Aeropuertos:** `airports` — listado, búsqueda por ICAO, nombre, ciudad, país.  
- **Vuelos:** `logbook` — `FlightLogAdmin` con `list_display`, filtros, búsqueda en notas y matrícula, **`total_time` de solo lectura**, **autocompletado** de FKs hacia aeronave y aeropuertos.  
- **Cartas:** la app `charts` **no** registra modelos; no hay gestión de cartas en el admin hasta que exista el modelo.  
- **Usuarios Django:** el proyecto incluye `django.contrib.auth` y `users` en `INSTALLED_APPS`, pero **no** hay en este código un registro de modelos de dominio de piloto en `users` ni un flujo de login propio; el staff usa el **usuario del admin estándar** de Django.

---

## 11. Current Limitations

- **Autenticación de piloto / multiusuario:** no hay vistas de registro, login o **vuelos asociados a un piloto** en el dominio; solo el mecanismo estándar de Django para el admin.  
- **API:** no hay endpoints JSON/REST.  
- **Ciclo de tres pasos (planificar / iniciar / finalizar) y estados** (`PLANNED`, etc.): **no** implementados en el modelo ni en las URLs.  
- **Integración con proveedores de cartas:** inexistente; en el diseño, las cartas serían añadidas **manualmente** (archivo o URL) en una futura implementación.  
- **App `users` y `core`:** sin modelos de negocio; no amplían aún el comportamiento de la app web pública.  
- **Cálculo de duración** basado en `block_off` / `block_on` con lógica de medianoche, no en campos `engine_start_time` / `engine_stop_time` (no presentes en el repositorio).

---

## 12. Future Improvements

Propuestas razonables alineadas con el concepto funcional y las limitaciones actuales:

- **Autenticación de usuarios** y, si aplica, perfiles de **piloto**.  
- **Vuelos por piloto** (p. ej. `ForeignKey` a usuario o a un modelo `Pilot`).  
- **Modelo de estados y vistas** de iniciar / finalizar, con cálculo de **duración a partir de instantes reales** alineados con `date` del vuelo.  
- **Filtros avanzados** en listado (fechas, aeropuerto, aeronave) y, opcionalmente, un **dashboard** de resúmenes.  
- **Modelo `Chart`**, tipos (AIRPORT, APPROACH, SID, STAR, TAXI, OTHER), asociación a `Airport` y sección en **detalle de vuelo** con enlaces a documentación de salida/llegada.  
- **Integración externa** (p. ej. trazas o datos de terceros): mención típica en proyectos de aula — p. ej. **Flightradar24** u otra fuente, sujeta a términos de uso y APIs.  
- **Sincronización automática de cartas** con proveedores oficiales o repositorios, en sustitución o complemento de la carga manual.

---

*Documento pensado para uso en entorno de clase; el comportamiento concreto debe verificarse siempre con el código y las migraciones del repositorio.*
