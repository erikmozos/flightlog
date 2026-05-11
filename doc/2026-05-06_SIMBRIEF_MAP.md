# Importación SimBrief/OFP y mapa Leaflet (Flightlog)

Fecha del apunte: 2026-05-06 · actualizado por prioridad XML (2026).

## Qué se añadió / comportamiento vigente

- Rutas **`/flights/import/`**:
  - **Formato preferido**: archivo «**XML Datafile**» de SimBrief (`.xml`), analizado con **`xml.etree.ElementTree`** (**sin dependencias** extra): ver `parse_simbrief_xml` en `logbook/simbrief_xml_parser.py`.
  - **Alternativas**: archivo **`.txt` UTF-8** pegado/exportado desde el OFP, o **texto opcional en el formulario**, interpretados con **`parse_simbrief_text`** (`logbook/simbrief_parser.py`) como **fallback heurístico**.
  - Validación del formulario (`SimBriefImportForm`): sólo admiten archivo **`.xml` o `.txt`**; cualquier otra extensión es error explícito.
- **Coordenadas** opcionales en **`Airport`** (`latitude`, `longitude`) para mapa **Leaflet** en el **detalle del vuelo** (OSM).
- Campos opcionales en **`FlightLog`**: número de vuelo, `route`, `alternate_airport`, `estimated_flight_time`, metadatos de import (`imported_source`, `imported_at`).
- Migración **`airports.0004_airport_coordinates_seed`** para ICAO europeos ya sembrados.

## Archivos principales tocados

| Área | Archivos |
|------|-----------|
| Parser XML | `logbook/simbrief_xml_parser.py` |
| Parser texto (fallback) | `logbook/simbrief_parser.py` |
| Formulario / vistas | `logbook/forms.py`, `logbook/views.py` |
| Plantilla importación | `templates/logbook/flight_import.html` |

(Además modelo/migraciones/admin/UI detalle desde la entrega inicial: ver historial.)

## Limitaciones (explícitas)

1. **XML tolerante pero no XSD cerrado**: la estructura del datafile SimBrief puede cambiar; el código prueba rutas etiquetadas típicas y devuelve `None`/vacío ante nodos ausentes sin lanzar errores fuera de **`ParseError`** del XML ilegible.
2. **Texto pegado**.txt fallback sigue siendo **heurístico**.
3. **Sin PDF**.
4. **Mapa**: línea directa aprox., no airway real.
5. **Sin API SimBrief**: archivo subido manualmente (o texto).

## Operación habitual

Tipos **`Aircraft.icao_code`** deben coincidir con los del XML (p. ej. `B738`, `A320`) para satisfacer FK obligatoria **`aircraft`**.
