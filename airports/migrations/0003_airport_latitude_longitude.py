# Generated manually for map support (Flightlog / Leaflet).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airports", "0002_airport_icao_unique_seed_european"),
    ]

    operations = [
        migrations.AddField(
            model_name="airport",
            name="latitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="airport",
            name="longitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
            ),
        ),
    ]
