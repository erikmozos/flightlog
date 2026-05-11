"""
Carga cartas de demostración para cada aeropuerto (solo desarrollo / pruebas).
"""

from django.core.management.base import BaseCommand

from airports.models import Airport
from charts.models import Chart


DEMO_CHART_SPECS = [
    {
        "title": "Airport Chart",
        "chart_type": Chart.ChartType.AIRPORT,
        "description": "Carta de aeropuerto de demostración (no operativa).",
    },
    {
        "title": "Taxi Chart",
        "chart_type": Chart.ChartType.TAXI,
        "description": "Carta de rodaje de demostración (no operativa).",
    },
    {
        "title": "SID Example",
        "chart_type": Chart.ChartType.SID,
        "description": "SID de ejemplo para pruebas en la aplicación.",
    },
    {
        "title": "STAR Example",
        "chart_type": Chart.ChartType.STAR,
        "description": "STAR de ejemplo para pruebas en la aplicación.",
    },
    {
        "title": "ILS Approach",
        "chart_type": Chart.ChartType.APPROACH,
        "description": "Aproximación ILS de ejemplo (no certificada).",
    },
]


class Command(BaseCommand):
    help = "Crea cartas demo activas para cada aeropuerto (sin duplicar por título y tipo)."

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0
        airports = Airport.objects.all().order_by("icao_code")
        airport_total = airports.count()

        for airport in airports:
            icao = airport.icao_code.upper()
            url = f"https://chartfox.org/{icao}"

            for spec in DEMO_CHART_SPECS:
                exists = Chart.objects.filter(
                    airport=airport,
                    title=spec["title"],
                    chart_type=spec["chart_type"],
                ).exists()

                if exists:
                    skipped_count += 1
                    continue

                Chart.objects.create(
                    airport=airport,
                    title=spec["title"],
                    chart_type=spec["chart_type"],
                    description=spec["description"],
                    external_url=url,
                    is_active=True,
                )
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Cartas creadas: {created_count}\n"
                f"Cartas ignoradas (ya existían): {skipped_count}\n"
                f"Aeropuertos procesados: {airport_total}"
            )
        )
