# Menorca (LEMH) · ausente del catálogo inicial pero habitual en rutas Baleares/SimBrief.

from decimal import Decimal

from django.db import migrations


def seed_lemh(apps, schema_editor):
    Airport = apps.get_model("airports", "Airport")
    Airport.objects.update_or_create(
        icao_code="LEMH",
        defaults={
            "name": "Menorca",
            "city": "Mahón",
            "country": "Spain",
            "latitude": Decimal("39.862500"),
            "longitude": Decimal("4.218611"),
        },
    )


def remove_lemh(apps, schema_editor):
    Airport = apps.get_model("airports", "Airport")
    Airport.objects.filter(icao_code="LEMH").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("airports", "0004_airport_coordinates_seed"),
    ]

    operations = [
        migrations.RunPython(seed_lemh, remove_lemh),
    ]
