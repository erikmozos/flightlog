from django.contrib import admin

from .models import FlightLog


@admin.register(FlightLog)
class FlightLogAdmin(admin.ModelAdmin):
    list_display = (
        "planned_date",
        "pilot",
        "flight_number",
        "aircraft",
        "departure_airport",
        "arrival_airport",
        "alternate_airport",
        "status",
        "imported_source",
        "engine_start_time",
        "engine_stop_time",
        "total_time",
    )
    list_filter = (
        "status",
        "planned_date",
        "imported_source",
        "departure_airport",
        "arrival_airport",
    )
    search_fields = (
        "flight_number",
        "route",
        "remarks",
        "aircraft__registration",
        "departure_airport__icao_code",
        "arrival_airport__icao_code",
        "pilot__username",
        "imported_source",
    )
    readonly_fields = ("total_time", "imported_at")
    autocomplete_fields = (
        "pilot",
        "aircraft",
        "departure_airport",
        "arrival_airport",
        "alternate_airport",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "pilot",
                    "status",
                    "planned_date",
                    "planned_departure_time",
                    "estimated_flight_time",
                    "aircraft",
                    "flight_number",
                    "departure_airport",
                    "arrival_airport",
                    "alternate_airport",
                )
            },
        ),
        (
            "Importación OFP",
            {
                "fields": (
                    "route",
                    "ofp_fuel_ramp_kg",
                    "ofp_fuel_takeoff_kg",
                    "ofp_fuel_landing_kg",
                    "imported_source",
                    "imported_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Combustible",
            {
                "fields": (
                    "fuel_on_board_start_kg",
                    "fuel_on_board_end_kg",
                ),
            },
        ),
        (
            "Motor",
            {"fields": ("engine_start_time", "engine_stop_time", "total_time")},
        ),
        ("Notas", {"fields": ("remarks",)}),
    )
