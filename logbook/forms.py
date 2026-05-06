from django import forms

from aircraft.models import Aircraft
from airports.models import Airport

from .models import FlightLog


class FlightLogForm(forms.ModelForm):
    """Solo vuelo previsto: sin horas reales de motor (se registran con Iniciar / Finalizar)."""

    class Meta:
        model = FlightLog
        fields = [
            "planned_date",
            "aircraft",
            "departure_airport",
            "arrival_airport",
            "planned_departure_time",
            "remarks",
        ]
        labels = {
            "planned_date": "Fecha prevista",
            "aircraft": "Aeronave",
            "departure_airport": "Aeropuerto de salida",
            "arrival_airport": "Aeropuerto de llegada",
            "planned_departure_time": "Hora de salida prevista",
            "remarks": "Observaciones",
        }
        help_texts = {
            "planned_date": "Fecha prevista o del vuelo planificado.",
            "planned_departure_time": "Opcional.",
            "remarks": "Opcional.",
        }
        widgets = {
            "planned_date": forms.DateInput(attrs={"type": "date"}),
            "planned_departure_time": forms.TimeInput(attrs={"type": "time", "step": "1"}),
            "remarks": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["aircraft"].empty_label = "Selecciona tipo / aeronave…"
        self.fields["aircraft"].queryset = Aircraft.objects.all().order_by(
            "manufacturer",
            "model",
            "registration",
        )
        airport_qs = Airport.objects.all().order_by("country", "city", "icao_code")
        self.fields["departure_airport"].queryset = airport_qs
        self.fields["arrival_airport"].queryset = airport_qs
        self.fields["departure_airport"].empty_label = "Selecciona aeropuerto de salida…"
        self.fields["arrival_airport"].empty_label = "Selecciona aeropuerto de llegada…"

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Alta de vuelo previsto: nunca tiempos reales de motor (Iniciar/Finalizar en otra pantalla).
        instance.status = FlightLog.Status.PLANNED
        if instance.pk is None:
            instance.engine_start_time = None
            instance.engine_stop_time = None
            instance.total_time = None
        if commit:
            instance.save()
        return instance
