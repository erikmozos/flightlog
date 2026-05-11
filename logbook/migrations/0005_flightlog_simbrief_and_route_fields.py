# SimBrief/OFP import and route-related optional fields.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airports", "0003_airport_latitude_longitude"),
        ("logbook", "0004_flightlog_add_pilot"),
    ]

    operations = [
        migrations.AddField(
            model_name="flightlog",
            name="alternate_airport",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="alternate_flights",
                to="airports.airport",
            ),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="estimated_flight_time",
            field=models.DurationField(
                blank=True,
                help_text="Duración prevista desde el OFP (ej. EET/ETE), si se importó.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="flight_number",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="imported_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="imported_source",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="route",
            field=models.TextField(blank=True),
        ),
    ]
