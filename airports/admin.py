from django.contrib import admin

from .models import Airport


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("icao_code", "name", "city", "country")
    search_fields = ("icao_code", "name", "city", "country")
