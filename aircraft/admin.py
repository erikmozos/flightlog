from django.contrib import admin

from .models import Aircraft


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ("registration", "manufacturer", "model", "icao_code", "category")
    search_fields = ("registration", "manufacturer", "model", "icao_code", "category")
