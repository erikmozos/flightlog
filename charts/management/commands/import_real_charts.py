"""
Importa PDFs desde charts/imports/<ICAO>/ creando objetos Chart.
"""

import re
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from airports.models import Airport
from charts.models import Chart

IMPORTS_REL = Path("charts") / "imports"


def detect_chart_type(filename_stem: str) -> str:
    """Devuelve Chart.ChartType según el nombre del archivo (sin extensión).

    Incluye patrones habituales del AIP ENAIRE (AD 2): SID, STAR, IAC, ADC, PDC,
    AOC, VAC, etc. «loc» solo como token (evita falsos positivos en palabras como
    «block»).
    """
    low = filename_stem.lower()
    tokens = re.split(r"[^a-z0-9]+", low)

    if "sid" in low:
        return Chart.ChartType.SID
    if "star" in low:
        return Chart.ChartType.STAR
    # IAC / LOC: procedimientos de aproximación (España denomina IAC al ILLOC/ILS…)
    if "iac" in low:
        return Chart.ChartType.APPROACH
    if "approach" in low or "ils" in low or "app" in tokens:
        return Chart.ChartType.APPROACH
    if "loc" in tokens:
        return Chart.ChartType.APPROACH
    # PDC: parking/docking (plano de estacionamiento en rodadura)
    if "pdc" in low:
        return Chart.ChartType.TAXI
    if "taxi" in low:
        return Chart.ChartType.TAXI
    if "airport" in low or "adc" in low:
        return Chart.ChartType.AIRPORT
    if "aoc" in low or "vac" in low:
        return Chart.ChartType.OTHER

    return Chart.ChartType.OTHER


def title_from_stem(stem: str) -> str:
    t = stem.replace("_", " ").strip()
    if len(t) > 255:
        return t[:255]
    return t or stem


class Command(BaseCommand):
    help = "Importa PDFs desde charts/imports/<ICAO>/ hacia Chart (FileField)."

    def handle(self, *args, **options):
        imports_dir = settings.BASE_DIR / IMPORTS_REL
        imports_dir.mkdir(parents=True, exist_ok=True)

        total_created = 0
        total_skipped = 0
        errors: list[str] = []
        airports_touched: list[tuple[str, int, int]] = []  # icao, created, skipped

        for entry in sorted(imports_dir.iterdir()):
            if not entry.is_dir():
                continue
            icao_folder = entry.name.upper()
            if not (len(icao_folder) == 4 and icao_folder.isalpha()):
                self.stdout.write(
                    self.style.WARNING(
                        f"Ignorada carpeta «{entry.name}»: no es un código ICAO de 4 letras."
                    )
                )
                continue

            try:
                airport = Airport.objects.get(icao_code__iexact=icao_folder)
            except Airport.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"Ignorada carpeta «{icao_folder}»: no hay aeropuerto con ese ICAO en la base de datos."
                    )
                )
                continue

            a_created = 0
            a_skipped = 0
            pdfs = sorted(
                p for p in entry.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"
            )
            for pdf_path in pdfs:
                stem = pdf_path.stem
                chart_type = detect_chart_type(stem)
                title = title_from_stem(stem)

                exists = Chart.objects.filter(
                    airport=airport,
                    title=title,
                    chart_type=chart_type,
                ).exists()
                if exists:
                    a_skipped += 1
                    total_skipped += 1
                    continue

                description = f"Importada automáticamente desde {pdf_path.name}."
                try:
                    chart = Chart(
                        airport=airport,
                        title=title,
                        chart_type=chart_type,
                        description=description,
                        is_active=True,
                    )
                    with open(pdf_path, "rb") as fh:
                        chart.pdf_file.save(pdf_path.name, File(fh), save=False)
                    chart.save()
                    a_created += 1
                    total_created += 1
                except Exception as exc:
                    err = f"{icao_folder}/{pdf_path.name}: {exc}"
                    errors.append(err)
                    self.stdout.write(self.style.ERROR(err))

            airports_touched.append((icao_folder, a_created, a_skipped))
            self.stdout.write(
                f"Aeropuerto {icao_folder}: creadas {a_created}, ignoradas {a_skipped}."
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Total cartas creadas: {total_created}\n"
                f"Total cartas ignoradas (duplicado): {total_skipped}\n"
                f"Aeropuertos con carpeta procesada: {len(airports_touched)}"
            )
        )
        if errors:
            self.stdout.write(self.style.ERROR(f"Errores: {len(errors)}"))
