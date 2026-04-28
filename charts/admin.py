from django.contrib import admin

from .models import Chart


@admin.register(Chart)
class ChartAdmin(admin.ModelAdmin):
    list_display = ("title", "airport", "chart_type", "is_active", "has_pdf", "has_url")
    list_filter = ("chart_type", "is_active", "airport")
    search_fields = ("title", "description", "airport__icao_code", "airport__name")
    autocomplete_fields = ("airport",)

    @admin.display(boolean=True, description="PDF")
    def has_pdf(self, obj):
        return bool(obj and obj.pdf_file)

    @admin.display(boolean=True, description="URL")
    def has_url(self, obj):
        return bool(obj and obj.external_url)
