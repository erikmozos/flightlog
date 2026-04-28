from django import forms

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
        widgets = {
            "planned_date": forms.DateInput(attrs={"type": "date"}),
            "planned_departure_time": forms.TimeInput(attrs={"type": "time", "step": "1"}),
            "remarks": forms.Textarea(attrs={"rows": 4}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.status = FlightLog.Status.PLANNED
        if commit:
            instance.save()
        return instance
