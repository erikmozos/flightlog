# Generated manually for aircraft type catalog seed.

from django.db import migrations, models

AIRCRAFT_TYPES = [
    {"manufacturer": "Airbus", "model": "A320", "icao_code": "A320", "category": "Jet"},
    {"manufacturer": "Airbus", "model": "A321", "icao_code": "A321", "category": "Jet"},
    {"manufacturer": "Airbus", "model": "A330", "icao_code": "A330", "category": "Jet"},
    {"manufacturer": "Airbus", "model": "A350", "icao_code": "A359", "category": "Jet"},
    {"manufacturer": "Boeing", "model": "737-800", "icao_code": "B738", "category": "Jet"},
    {"manufacturer": "Boeing", "model": "737 MAX 8", "icao_code": "B38M", "category": "Jet"},
    {"manufacturer": "Boeing", "model": "747-400", "icao_code": "B744", "category": "Jet"},
    {"manufacturer": "Boeing", "model": "777-300ER", "icao_code": "B77W", "category": "Jet"},
    {"manufacturer": "Boeing", "model": "787-9", "icao_code": "B789", "category": "Jet"},
    {"manufacturer": "Cessna", "model": "172 Skyhawk", "icao_code": "C172", "category": "SEP"},
    {"manufacturer": "Cessna", "model": "152", "icao_code": "C152", "category": "SEP"},
    {"manufacturer": "Cessna", "model": "182 Skylane", "icao_code": "C182", "category": "SEP"},
    {"manufacturer": "Cessna", "model": "208 Caravan", "icao_code": "C208", "category": "Turboprop"},
    {"manufacturer": "Piper", "model": "PA-28 Cherokee", "icao_code": "P28A", "category": "SEP"},
    {"manufacturer": "Piper", "model": "PA-28 Archer", "icao_code": "P28A", "category": "SEP"},
    {"manufacturer": "Piper", "model": "PA-44 Seminole", "icao_code": "PA44", "category": "MEP"},
    {"manufacturer": "Beechcraft", "model": "King Air 350", "icao_code": "BE35", "category": "Turboprop"},
    {"manufacturer": "Beechcraft", "model": "Baron 58", "icao_code": "BE58", "category": "MEP"},
    {"manufacturer": "Diamond", "model": "DA40", "icao_code": "DA40", "category": "SEP"},
    {"manufacturer": "Diamond", "model": "DA42", "icao_code": "DA42", "category": "MEP"},
    {"manufacturer": "Cirrus", "model": "SR22", "icao_code": "SR22", "category": "SEP"},
    {"manufacturer": "Cirrus", "model": "Vision Jet", "icao_code": "SF50", "category": "Jet"},
    {"manufacturer": "Embraer", "model": "E190", "icao_code": "E190", "category": "Jet"},
    {"manufacturer": "Embraer", "model": "E195", "icao_code": "E195", "category": "Jet"},
    {"manufacturer": "ATR", "model": "ATR 72", "icao_code": "AT72", "category": "Turboprop"},
    {"manufacturer": "Bombardier", "model": "CRJ900", "icao_code": "CRJ9", "category": "Jet"},
    {"manufacturer": "Bombardier", "model": "Dash 8 Q400", "icao_code": "DH8D", "category": "Turboprop"},
]


def seed_aircraft_types(apps, schema_editor):
    Aircraft = apps.get_model("aircraft", "Aircraft")
    for row in AIRCRAFT_TYPES:
        reg_base = f"{row['manufacturer']} {row['model']}"
        registration = reg_base[:32]
        defaults = {
            "manufacturer": row["manufacturer"],
            "model": row["model"],
            "icao_code": row["icao_code"],
            "category": row["category"],
        }
        _, created = Aircraft.objects.get_or_create(
            registration=registration,
            defaults=defaults,
        )
        if not created:
            Aircraft.objects.filter(registration=registration).update(**defaults)


def unseed_aircraft_types(apps, schema_editor):
    Aircraft = apps.get_model("aircraft", "Aircraft")
    regs = [f"{r['manufacturer']} {r['model']}"[:32] for r in AIRCRAFT_TYPES]
    Aircraft.objects.filter(registration__in=regs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("aircraft", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="aircraft",
            name="icao_code",
            field=models.CharField(
                blank=True,
                help_text="Designador tipo OACI (ej. A320, B738).",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="aircraft",
            name="category",
            field=models.CharField(
                blank=True,
                help_text="Clase general (ej. Jet, SEP, Turboprop).",
                max_length=32,
            ),
        ),
        migrations.AlterModelOptions(
            name="aircraft",
            options={
                "ordering": ["manufacturer", "model", "registration"],
                "verbose_name_plural": "Aircraft",
            },
        ),
        migrations.RunPython(seed_aircraft_types, unseed_aircraft_types),
    ]
