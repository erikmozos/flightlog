from django.db import models

from airports.models import Airport


class Chart(models.Model):
    """
    Carta aeronáutica asociada a un aeropuerto: PDF subido, enlace externo, o ambos.
    La app de vuelo enlaza a las cartas de los aeropuertos de salida y llegada.
    """

    class ChartType(models.TextChoices):
        AIRPORT = "AIRPORT", "Aeropuerto"
        APPROACH = "APPROACH", "Aproximación"
        SID = "SID", "SID"
        STAR = "STAR", "STAR"
        TAXI = "TAXI", "Taxi"
        OTHER = "OTHER", "Otra"

    airport = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="charts",
    )
    title = models.CharField(max_length=255)
    chart_type = models.CharField(
        max_length=20,
        choices=ChartType.choices,
        default=ChartType.OTHER,
    )
    description = models.TextField(blank=True)
    pdf_file = models.FileField(
        upload_to="chart_pdfs/%Y/%m/",
        blank=True,
        null=True,
        help_text="PDF opcional almacenado en el servidor.",
    )
    external_url = models.URLField(blank=True, max_length=500, help_text="Enlace a fuente web opcional.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["airport", "chart_type", "title"]

    def __str__(self):
        return f"{self.airport.icao_code} — {self.title}"
