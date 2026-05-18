from django.test import TestCase

from aircraft.models import Aircraft


class AircraftModelTests(TestCase):
    def test_str(self):
        aircraft = Aircraft.objects.create(
            registration="EC-ABC",
            manufacturer="TestAir",
            model="T-100",
            icao_code="T100",
        )
        self.assertEqual(str(aircraft), "TestAir T-100 (T100)")
