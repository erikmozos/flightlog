from django.db import models


class Aircraft(models.Model):
    """Avión u otra aeronave identificada por su matrícula."""

    registration = models.CharField(max_length=32)
    manufacturer = models.CharField(max_length=128)
    model = models.CharField(max_length=128)
    icao_code = models.CharField(
        max_length=16,
        blank=True,
        help_text="Designador tipo OACI (ej. A320, B738).",
    )
    category = models.CharField(
        max_length=32,
        blank=True,
        help_text="Clase general (ej. Jet, SEP, Turboprop).",
    )

    class Meta:
        ordering = ["manufacturer", "model", "registration"]
        verbose_name_plural = "Aircraft"

    def __str__(self):
        if self.icao_code:
            return f"{self.manufacturer} {self.model} ({self.icao_code})"
        return f"{self.registration} · {self.manufacturer} {self.model}"
