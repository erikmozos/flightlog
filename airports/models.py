from django.db import models


class Airport(models.Model):
    """Aeropuerto identificado por código ICAO (4 letras)."""

    icao_code = models.CharField(max_length=4)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=128)
    country = models.CharField(max_length=128)

    class Meta:
        ordering = ["icao_code"]

    def __str__(self):
        return f"{self.icao_code} — {self.name}"
