from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models

from aircraft.models import Aircraft
from airports.models import Airport


def duration_engine_run(engine_start, engine_stop):
    """
    Duración entre encendido y apagado de motor.
    Si la hora de fin es anterior a la de inicio, se asume vuelo que cruza medianoche.
    """
    if not engine_start or not engine_stop:
        return None
    if engine_stop < engine_start:
        engine_stop = engine_stop + timedelta(days=1)
    return engine_stop - engine_start


class FlightLog(models.Model):
    """
    Ciclo de vida de un vuelo: planificado → en curso (motor) → completado o cancelado.
    """

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planificado"
        IN_PROGRESS = "IN_PROGRESS", "En curso"
        COMPLETED = "COMPLETED", "Completado"
        CANCELLED = "CANCELLED", "Cancelado"

    pilot = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="flights",
        null=True,
        blank=True,
    )
    planned_date = models.DateField(
        help_text="Fecha prevista o fecha del vuelo planificado.",
    )
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name="flight_logs")
    departure_airport = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="departure_flights"
    )
    arrival_airport = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="arrival_flights"
    )
    planned_departure_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora de salida prevista (opcional).",
    )
    engine_start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se inician motores (al pasar a en curso).",
    )
    engine_stop_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se apagan motores al finalizar.",
    )
    total_time = models.DurationField(
        null=True,
        blank=True,
        help_text="Tiempo de motor: se rellena al completar (engine_stop - engine_start).",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-planned_date", "-id"]

    def __str__(self):
        dep = self.departure_airport.icao_code if self.departure_airport_id else "?"
        arr = self.arrival_airport.icao_code if self.arrival_airport_id else "?"
        return f"{self.planned_date} {dep} → {arr} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if (
            self.status == self.Status.COMPLETED
            and self.engine_start_time
            and self.engine_stop_time
        ):
            self.total_time = duration_engine_run(self.engine_start_time, self.engine_stop_time)
        else:
            self.total_time = None
        super().save(*args, **kwargs)

    def is_planned(self) -> bool:
        return self.status == self.Status.PLANNED

    def is_in_progress(self) -> bool:
        return self.status == self.Status.IN_PROGRESS

    def is_completed(self) -> bool:
        return self.status == self.Status.COMPLETED
