from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airports", "0005_airport_lemh_seed"),
    ]

    operations = [
        migrations.CreateModel(
            name="Navaid",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ident", models.CharField(max_length=8)),
                ("name", models.CharField(blank=True, max_length=255)),
                ("navaid_type", models.CharField(
                    choices=[
                        ("VOR", "VOR"),
                        ("NDB", "NDB"),
                        ("DME", "DME"),
                        ("VOR-DME", "VOR-DME"),
                        ("VORTAC", "VORTAC"),
                        ("TACAN", "TACAN"),
                        ("FIX", "Fix/Waypoint"),
                    ],
                    max_length=10,
                )),
                ("frequency_khz", models.IntegerField(blank=True, null=True)),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("iso_country", models.CharField(blank=True, max_length=2)),
            ],
            options={
                "ordering": ["ident"],
            },
        ),
        migrations.AddIndex(
            model_name="navaid",
            index=models.Index(fields=["latitude", "longitude"], name="airports_na_latitud_idx"),
        ),
        migrations.AddIndex(
            model_name="navaid",
            index=models.Index(fields=["iso_country"], name="airports_na_iso_cou_idx"),
        ),
    ]
