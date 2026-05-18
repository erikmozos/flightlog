from django.test import TestCase

from airports.models import Airport


class AirportModelTests(TestCase):
    def test_str(self):
        airport = Airport.objects.create(
            icao_code="ZZAA",
            name="Aeropuerto de Prueba",
            city="Testville",
            country="Testlandia",
        )
        self.assertEqual(str(airport), "ZZAA — Aeropuerto de Prueba")
