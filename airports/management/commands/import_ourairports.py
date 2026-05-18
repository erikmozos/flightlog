"""
Importa aeródromos y navaids desde los CSV de OurAirports (dominio público).

Uso:
    python manage.py import_ourairports
    python manage.py import_ourairports --navaids-only
    python manage.py import_ourairports --airports-only
    python manage.py import_ourairports --clear   # borra navaids antes de importar

Fuentes:
    https://davidmegginson.github.io/ourairports-data/airports.csv
    https://davidmegginson.github.io/ourairports-data/navaids.csv
"""

import csv
import io
import urllib.request

from django.core.management.base import BaseCommand, CommandError

from airports.models import Airport, Navaid

AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
NAVAIDS_URL = "https://davidmegginson.github.io/ourairports-data/navaids.csv"

# Solo estos tipos de aeródromo merecen mostrarse en el mapa
AIRPORT_TYPES_WANTED = {"large_airport", "medium_airport", "small_airport", "heliport", "seaplane_base"}

# Tipos de navaid que mapeamos al modelo
NAVAID_TYPE_MAP = {
    "VOR": "VOR",
    "NDB": "NDB",
    "DME": "DME",
    "VOR-DME": "VOR-DME",
    "VORTAC": "VORTAC",
    "TACAN": "TACAN",
    "FIX": "FIX",
}


def _fetch_csv(url: str) -> list[dict]:
    with urllib.request.urlopen(url, timeout=30) as resp:
        content = resp.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


class Command(BaseCommand):
    help = "Importa aeródromos y navaids desde OurAirports (CSV público)."

    def add_arguments(self, parser):
        parser.add_argument("--airports-only", action="store_true")
        parser.add_argument("--navaids-only", action="store_true")
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Borra todos los Navaid existentes antes de importar (útil para reimportar limpio).",
        )

    def handle(self, *args, **options):
        do_airports = not options["navaids_only"]
        do_navaids = not options["airports_only"]

        if do_airports:
            self._import_airports()
        if do_navaids:
            if options["clear"]:
                deleted, _ = Navaid.objects.all().delete()
                self.stdout.write(f"  Borrados {deleted} navaids existentes.")
            self._import_navaids()

    def _import_airports(self):
        self.stdout.write("Descargando airports.csv…")
        try:
            rows = _fetch_csv(AIRPORTS_URL)
        except Exception as exc:
            raise CommandError(f"No se pudo descargar airports.csv: {exc}") from exc

        self.stdout.write(f"  {len(rows)} filas recibidas.")
        created = updated = skipped = 0

        for row in rows:
            apt_type = (row.get("type") or "").strip()
            if apt_type not in AIRPORT_TYPES_WANTED:
                continue
            icao = (row.get("gps_code") or row.get("ident") or "").strip().upper()
            if not icao or len(icao) != 4:
                continue
            try:
                lat = float(row.get("latitude_deg") or "")
                lon = float(row.get("longitude_deg") or "")
            except (ValueError, TypeError):
                continue

            name = (row.get("name") or "").strip()[:255]
            city = (row.get("municipality") or "").strip()[:128]
            iso = (row.get("iso_country") or "").strip()

            obj, was_created = Airport.objects.update_or_create(
                icao_code=icao,
                defaults={
                    "name": name,
                    "city": city,
                    "country": iso,
                    "latitude": lat,
                    "longitude": lon,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  Aeródromos: {created} nuevos, {updated} actualizados, {skipped} omitidos."
            )
        )

    def _import_navaids(self):
        self.stdout.write("Descargando navaids.csv…")
        try:
            rows = _fetch_csv(NAVAIDS_URL)
        except Exception as exc:
            raise CommandError(f"No se pudo descargar navaids.csv: {exc}") from exc

        self.stdout.write(f"  {len(rows)} filas recibidas.")
        created = skipped = 0
        batch = []

        for row in rows:
            raw_type = (row.get("type") or "").strip().upper()
            navaid_type = NAVAID_TYPE_MAP.get(raw_type)
            if navaid_type is None:
                skipped += 1
                continue
            try:
                lat = float(row.get("latitude_deg") or "")
                lon = float(row.get("longitude_deg") or "")
            except (ValueError, TypeError):
                skipped += 1
                continue

            ident = (row.get("ident") or "").strip()[:8]
            if not ident:
                skipped += 1
                continue

            freq_raw = (row.get("frequency_khz") or "").strip()
            try:
                freq = int(float(freq_raw)) if freq_raw else None
            except (ValueError, TypeError):
                freq = None

            batch.append(
                Navaid(
                    ident=ident,
                    name=(row.get("name") or "").strip()[:255],
                    navaid_type=navaid_type,
                    frequency_khz=freq,
                    latitude=lat,
                    longitude=lon,
                    iso_country=(row.get("iso_country") or "").strip()[:2],
                )
            )

            if len(batch) >= 500:
                Navaid.objects.bulk_create(batch, ignore_conflicts=False)
                created += len(batch)
                batch = []

        if batch:
            Navaid.objects.bulk_create(batch, ignore_conflicts=False)
            created += len(batch)

        self.stdout.write(
            self.style.SUCCESS(f"  Navaids: {created} importados, {skipped} omitidos.")
        )
