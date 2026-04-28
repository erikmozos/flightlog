from django.contrib import admin

from .models import Aircraft


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ("registration", "manufacturer", "model")
    search_fields = ("registration", "manufacturer", "model")
