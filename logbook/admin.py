from django.contrib import admin

from .models import FlightLog


@admin.register(FlightLog)
class FlightLogAdmin(admin.ModelAdmin):
    list_display = (
        "planned_date",
        "pilot",
        "aircraft",
        "departure_airport",
        "arrival_airport",
        "status",
        "engine_start_time",
        "engine_stop_time",
        "total_time",
    )
    list_filter = (
        "status",
        "planned_date",
        "departure_airport",
        "arrival_airport",
    )
    search_fields = (
        "remarks",
        "aircraft__registration",
        "departure_airport__icao_code",
        "arrival_airport__icao_code",
        "pilot__username",
    )
    readonly_fields = ("total_time",)
    autocomplete_fields = ("pilot", "aircraft", "departure_airport", "arrival_airport")
    fieldsets = (
        (None, {"fields": ("pilot", "status", "planned_date", "planned_departure_time", "aircraft", "departure_airport", "arrival_airport")}),
        ("Motor", {"fields": ("engine_start_time", "engine_stop_time", "total_time")}),
        ("Notas", {"fields": ("remarks",)}),
    )
