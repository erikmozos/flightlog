import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("airports", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Chart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                (
                    "chart_type",
                    models.CharField(
                        choices=[
                            ("AIRPORT", "Aeropuerto"),
                            ("APPROACH", "Aproximación"),
                            ("SID", "SID"),
                            ("STAR", "STAR"),
                            ("TAXI", "Taxi"),
                            ("OTHER", "Otra"),
                        ],
                        default="OTHER",
                        max_length=20,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "pdf_file",
                    models.FileField(
                        blank=True,
                        help_text="PDF opcional almacenado en el servidor.",
                        null=True,
                        upload_to="chart_pdfs/%Y/%m/",
                    ),
                ),
                (
                    "external_url",
                    models.URLField(blank=True, help_text="Enlace a fuente web opcional.", max_length=500),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "airport",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="charts",
                        to="airports.airport",
                    ),
                ),
            ],
            options={
                "ordering": ["airport", "chart_type", "title"],
            },
        ),
    ]
