from django.contrib import admin

from .models import Airport, Navaid


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("icao_code", "name", "city", "country", "latitude", "longitude")
    search_fields = ("icao_code", "name", "city", "country")


@admin.register(Navaid)
class NavaidAdmin(admin.ModelAdmin):
    list_display = ("ident", "name", "navaid_type", "frequency_khz", "latitude", "longitude", "iso_country")
    list_filter = ("navaid_type", "iso_country")
    search_fields = ("ident", "name")
