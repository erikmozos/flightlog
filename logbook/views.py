from collections import OrderedDict
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from charts.models import Chart
from .forms import FlightLogForm
from .models import FlightLog


@login_required
@require_GET
def dashboard(request):
    """Resumen: previstos (7 días), en curso, completados, horas totales, últimos vuelos."""
    today = timezone.localdate()
    week_end = today + timedelta(days=7)
    qs = FlightLog.objects.filter(pilot=request.user)

    planned_count = qs.filter(
        status=FlightLog.Status.PLANNED,
        planned_date__gte=today,
        planned_date__lte=week_end,
    ).count()

    in_progress = (
        qs.filter(status=FlightLog.Status.IN_PROGRESS)
        .select_related("aircraft", "departure_airport", "arrival_airport")
        .order_by("-planned_date", "-id")
        .first()
    )

    completed_qs = qs.filter(status=FlightLog.Status.COMPLETED)
    completed_count = completed_qs.count()
    agg = completed_qs.aggregate(s=Sum("total_time"))
    total_td = agg["s"]
    total_hours = (total_td.total_seconds() / 3600.0) if total_td else 0.0

    latest_flights = (
        qs.select_related("aircraft", "departure_airport", "arrival_airport")
        .order_by("-planned_date", "-id")[:5]
    )

    return render(
        request,
        "logbook/dashboard.html",
        {
            "planned_count": planned_count,
            "in_progress": in_progress,
            "completed_count": completed_count,
            "total_hours": total_hours,
            "latest_flights": latest_flights,
        },
    )


@login_required
@require_GET
def flight_list(request):
    """Lista vuelos del más reciente al más antiguo."""
    flights = (
        FlightLog.objects.filter(pilot=request.user)
        .select_related(
            "aircraft",
            "departure_airport",
            "arrival_airport",
        )
    )
    return render(request, "logbook/flight_list.html", {"flights": flights})


@login_required
def flight_create(request):
    """Formulario (GET) o crea vuelo previsto en PLANNED (POST)."""
    if request.method == "POST":
        form = FlightLogForm(request.POST)
        if form.is_valid():
            flight = form.save(commit=False)
            flight.pilot = request.user
            flight.save()
            return redirect("logbook:flight_list")
    else:
        form = FlightLogForm()
    return render(request, "logbook/flight_form.html", {"form": form})


def _group_charts_by_type(queryset):
    """
    {etiqueta_tipo: [chart, ...], ...} solo tipos con cartas, orden fijo.
    """
    order = [c[0] for c in Chart.ChartType.choices]
    grouped = OrderedDict((code, []) for code in order)
    for chart in queryset:
        grouped[chart.chart_type].append(chart)
    return OrderedDict(
        (Chart.ChartType(code).label, grouped[code])
        for code in order
        if grouped[code]
    )


@login_required
@require_GET
def flight_detail(request, pk):
    """Detalle del vuelo: estado, acciones, cartas de aeropuertos de salida y llegada."""
    flight = get_object_or_404(
        FlightLog.objects.select_related(
            "aircraft",
            "departure_airport",
            "arrival_airport",
        ),
        pk=pk,
        pilot=request.user,
    )
    dep_qs = (
        Chart.objects.filter(airport=flight.departure_airport, is_active=True)
        .order_by("chart_type", "title")
        .select_related("airport")
    )
    arr_qs = (
        Chart.objects.filter(airport=flight.arrival_airport, is_active=True)
        .order_by("chart_type", "title")
        .select_related("airport")
    )
    elapsed_in_progress_display = None
    if flight.is_in_progress() and flight.engine_start_time:
        sec = max(0, int((timezone.now() - flight.engine_start_time).total_seconds()))
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        elapsed_in_progress_display = f"{h}:{m:02d}:{s:02d}"

    return render(
        request,
        "logbook/flight_detail.html",
        {
            "flight": flight,
            "departure_charts_by_type": _group_charts_by_type(dep_qs),
            "arrival_charts_by_type": _group_charts_by_type(arr_qs),
            "elapsed_in_progress_display": elapsed_in_progress_display,
        },
    )


@login_required
@require_POST
def flight_start(request, pk):
    """PLANNED → IN_PROGRESS, registra encendido de motores ahora."""
    flight = get_object_or_404(FlightLog, pk=pk, pilot=request.user)
    if flight.status == FlightLog.Status.PLANNED:
        flight.engine_start_time = timezone.now()
        flight.status = FlightLog.Status.IN_PROGRESS
        flight.save()
    return redirect("logbook:flight_detail", pk=pk)


@login_required
@require_POST
def flight_finish(request, pk):
    """IN_PROGRESS → COMPLETED, apagado de motores y total_time (vía model.save)."""
    flight = get_object_or_404(FlightLog, pk=pk, pilot=request.user)
    if flight.status == FlightLog.Status.IN_PROGRESS:
        flight.engine_stop_time = timezone.now()
        flight.status = FlightLog.Status.COMPLETED
        flight.save()
    return redirect("logbook:flight_detail", pk=pk)
