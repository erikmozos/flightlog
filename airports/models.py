from django.db import models


class Navaid(models.Model):
    """VOR, NDB, DME y waypoints importados desde OurAirports."""

    class NavaidType(models.TextChoices):
        VOR = "VOR", "VOR"
        NDB = "NDB", "NDB"
        DME = "DME", "DME"
        VORDME = "VOR-DME", "VOR-DME"
        VORTAC = "VORTAC", "VORTAC"
        TACAN = "TACAN", "TACAN"
        FIX = "FIX", "Fix/Waypoint"

    ident = models.CharField(max_length=8)
    name = models.CharField(max_length=255, blank=True)
    navaid_type = models.CharField(max_length=10, choices=NavaidType.choices)
    frequency_khz = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    iso_country = models.CharField(max_length=2, blank=True)

    class Meta:
        ordering = ["ident"]
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["iso_country"]),
        ]

    def __str__(self):
        return f"{self.ident} ({self.navaid_type})"


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
