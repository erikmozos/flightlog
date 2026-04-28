from django.db import models


class Aircraft(models.Model):
    """Avión u otra aeronave identificada por su matrícula."""

    registration = models.CharField(max_length=32)
    manufacturer = models.CharField(max_length=128)
    model = models.CharField(max_length=128)

    class Meta:
        ordering = ["registration"]
        verbose_name_plural = "Aircraft"

    def __str__(self):
        return f"{self.registration} ({self.manufacturer} {self.model})"
