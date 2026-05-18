from django.test import TestCase

from airports.models import Airport
from charts.models import Chart


class ChartModelTests(TestCase):
    def test_default_chart_type_is_other(self):
        airport = Airport.objects.create(
            icao_code="ZZCH",
            name="Aeropuerto Charts",
            city="Testville",
            country="Testlandia",
        )
        chart = Chart.objects.create(airport=airport, title="Ficha aeropuerto")
        self.assertEqual(chart.chart_type, Chart.ChartType.OTHER)
