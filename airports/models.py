from django.db import models


class Airport(models.Model):
    """Aeropuerto identificado por código ICAO (4 letras)."""

    icao_code = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=128)
    country = models.CharField(max_length=128)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["icao_code"]

    def __str__(self):
        return f"{self.icao_code} — {self.name}"
