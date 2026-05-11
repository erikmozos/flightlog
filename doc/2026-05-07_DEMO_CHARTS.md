# Cartas demo (`seed_demo_charts`)

## Qué hace

El comando de gestión `seed_demo_charts` recorre todos los aeropuertos de la base de datos y crea, para cada uno, un conjunto fijo de cinco cartas de demostración (Airport Chart, Taxi Chart, SID Example, STAR Example, ILS Approach) con enlace genérico a ChartFox por código ICAO.

Antes de insertar cada carta comprueba si ya existe una con el mismo aeropuerto, título y tipo; en ese caso la omite para no duplicar datos.

## Cómo ejecutarlo

Desde la raíz del proyecto, con el entorno virtual activado:

```bash
python manage.py seed_demo_charts
```

Al finalizar imprime en consola cuántas cartas se han creado, cuántas se han ignorado por ya existir y cuántos aeropuertos se han procesado.

## Propósito

Son datos **solo para pruebas y desarrollo** de la interfaz (por ejemplo el bloque “Cartas aeronáuticas” en el detalle de vuelo). No deben interpretarse como material de navegación real.

## Aviso

Estas cartas demo **no sustituyen** cartas aeronáuticas oficiales ni certificadas. La planificación y ejecución de vuelos debe basarse siempre en la información aprobada por la autoridad competente y en los documentos vigentes del operador.
