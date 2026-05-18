from datetime import datetime, timedelta

from django.test import TestCase

from logbook.models import duration_engine_run


class DurationEngineRunTests(TestCase):
    def test_simple_duration(self):
        start = datetime(2026, 1, 1, 10, 0)
        stop = datetime(2026, 1, 1, 11, 30)
        self.assertEqual(duration_engine_run(start, stop), timedelta(hours=1, minutes=30))
