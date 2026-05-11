from django import forms

from aircraft.models import Aircraft
from airports.models import Airport

from .models import FlightLog


def strip_simbrief_xml_preamble(raw: str) -> tuple[str, bool]:
    """
    Si el contenido pegado lleva texto del navegador («This XML file…») delante del <OFP>,
    recorta hasta el primer <OFP> para poder usar ElementTree y marcar XML.
    Devuelve (cuerpo_normalizado, es_xml_detectado).
    """
    s = (raw or "").replace("\ufeff", "").strip()
    if not s:
        return "", False
    lowered = s.lower()
    marker = lowered.find("<ofp")
    if marker == -1:
        marker = lowered.find("<simbrief")
    if marker != -1:
        return s[marker:].strip(), True
    return s, False


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
            "fuel_on_board_start_kg",
            "remarks",
        ]
        labels = {
            "planned_date": "Fecha del vuelo",
            "aircraft": "Aeronave",
            "departure_airport": "Aeropuerto salida (ICAO)",
            "arrival_airport": "Aeropuerto llegada (ICAO)",
            "planned_departure_time": "Hora prevista (UTC) · opcional",
            "fuel_on_board_start_kg": "Combustible a bordo al inicio (kg) · opcional",
            "remarks": "Observaciones",
        }
        help_texts = {
            "planned_date": "",
            "planned_departure_time": "",
            "fuel_on_board_start_kg": "Puede completarlo aquí o al pulsar «Iniciar vuelo» en la ficha.",
            "remarks": "",
        }
        widgets = {
            "planned_date": forms.DateInput(
                attrs={"type": "date", "class": "ff-control"}
            ),
            "aircraft": forms.Select(attrs={"class": "ff-control"}),
            "departure_airport": forms.Select(attrs={"class": "ff-control"}),
            "arrival_airport": forms.Select(attrs={"class": "ff-control"}),
            "planned_departure_time": forms.TimeInput(
                attrs={"type": "time", "step": "1", "class": "ff-control"}
            ),
            "fuel_on_board_start_kg": forms.NumberInput(
                attrs={
                    "class": "ff-control",
                    "step": "any",
                    "min": "0",
                    "placeholder": "Ej. 4200",
                    "inputmode": "decimal",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "ff-control ff-textarea",
                    "placeholder": "Detalles de la misión, meteorología prevista o notas del plan de vuelo…",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["aircraft"].empty_label = "Seleccione matrícula…"
        self.fields["aircraft"].queryset = Aircraft.objects.all().order_by(
            "manufacturer",
            "model",
            "registration",
        )
        airport_qs = Airport.objects.all().order_by("country", "city", "icao_code")
        self.fields["departure_airport"].queryset = airport_qs
        self.fields["arrival_airport"].queryset = airport_qs
        self.fields["departure_airport"].empty_label = "Ej.: seleccione ICAO de salida…"
        self.fields["arrival_airport"].empty_label = "Ej.: seleccione ICAO de llegada…"

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


class SimBriefImportForm(forms.Form):
    """
    Formato recomendado: archivo XML SimBrief (.xml).
    Alternativa: archivo .txt UTF-8 o pegado OFP texto (fallback heurístico).
    """

    ofp_text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 9,
                "class": "ff-control ff-textarea",
                "placeholder": "Opcional · pegue texto OFP si no usa archivo .xml/.txt · …",
            }
        ),
        label="Texto OFP (opcional, fallback)",
    )
    ofp_file = forms.FileField(
        required=False,
        label="Archivo SimBrief (.xml recomendado, o .txt)",
        widget=forms.ClearableFileInput(
            attrs={"class": "ff-control", "accept": ".xml,.txt,text/plain,application/xml"}
        ),
    )

    def clean(self):
        data = super().clean()
        text = (data.get("ofp_text") or "").strip()
        upload = data.get("ofp_file")

        body = ""
        file_name_low = ""

        had_file_bytes = upload and getattr(upload, "size", 0)

        if had_file_bytes:
            file_name_low = (upload.name or "").lower()
            if not (file_name_low.endswith(".xml") or file_name_low.endswith(".txt")):
                raise forms.ValidationError(
                    {
                        "ofp_file": "Extensión no admitida; use únicamente .xml (preferido) o .txt codificado en UTF-8.",
                    },
                )
            try:
                body = upload.read().decode("utf-8").strip()
            except UnicodeDecodeError:
                raise forms.ValidationError(
                    {"ofp_file": "No se pudo decodificar el archivo como UTF-8."},
                ) from None
            if not body:
                if text:
                    body = text.strip()
                else:
                    raise forms.ValidationError(
                        {
                            "ofp_file": "El archivo está vacío; cargue otro archivo o pegue texto en el campo opcional.",
                        },
                    )
        elif text:
            body = text.strip()
        else:
            raise forms.ValidationError(
                "Suba el «XML Datafile» de SimBrief (.xml), un .txt UTF-8, o pegue el OFP en texto.",
            )

        body, sniff_xml = strip_simbrief_xml_preamble(body)

        if had_file_bytes:
            if file_name_low.endswith(".xml"):
                is_xml = True
            elif file_name_low.endswith(".txt") and sniff_xml:
                is_xml = True
            else:
                is_xml = False
        else:
            is_xml = sniff_xml

        data["body"] = body.strip()
        data["is_xml"] = is_xml
        return data
