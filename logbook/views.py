import json
from collections import OrderedDict
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET, require_POST

from aircraft.models import Aircraft
from airports.models import Airport
from charts.models import Chart
from .forms import FlightLogForm, SimBriefImportForm
from .models import FlightLog
from .simbrief_parser import parse_simbrief_text
from .simbrief_xml_parser import parse_simbrief_xml


def _optional_decimal_from_post(post, key: str) -> Decimal | None:
    s = (post.get(key) or "").strip().replace(" ", "").replace(",", ".")
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


@login_required
def flight_import(request):
    """Importa XML/texto SimBrief (.xml recomendado) y crea un vuelo PLANNED para el piloto."""
    import_errors: list[str] = []
    if request.method == "POST":
        form = SimBriefImportForm(request.POST, request.FILES)
        if form.is_valid():
            body = form.cleaned_data["body"]
            is_xml = form.cleaned_data["is_xml"]
            parsed = parse_simbrief_xml(body) if is_xml else parse_simbrief_text(body)

            dep_icao = (parsed.get("departure_icao") or "").strip().upper()
            arr_icao = (parsed.get("arrival_icao") or "").strip().upper()

            departure = (
                Airport.objects.filter(icao_code__iexact=dep_icao).first()
                if dep_icao
                else None
            )
            arrival = (
                Airport.objects.filter(icao_code__iexact=arr_icao).first()
                if arr_icao
                else None
            )

            if not dep_icao or not departure:
                hint = (
                    " Revise el XML (nodos «origin»/«icao_code»…) o cargue otro archivo."
                    if is_xml
                    else " Revise las etiquetas de salida del OFP o use el archivo .xml oficial."
                )
                import_errors.append(
                    "No se pudo relacionar la salida con un aeropuerto conocido "
                    "(ICAO detectado / base de datos). Compruebe el plan y que el ICAO exista."
                    + hint
                )
            if not arr_icao or not arrival:
                hint = (
                    " Revise el XML («destination», «icao_code»…)."
                    if is_xml
                    else " Revise las etiquetas de llegada del OFP o use el archivo .xml oficial."
                )
                import_errors.append(
                    "No se pudo relacionar la llegada con un aeropuerto conocido "
                    "(ICAO detectado / base de datos). Compruebe el plan y que el ICAO exista."
                    + hint
                )

            ac_icao_raw = parsed.get("aircraft_icao")
            ac_code = (ac_icao_raw or "").strip().upper()
            aircraft = None
            if not ac_code:
                msg = (
                    "No aparece un tipo OACI de aeronave reconocible en el XML "
                    "(busque etiquetas tipo «icao_code» dentro de «aircraft»)."
                    if is_xml
                    else (
                        "No se detectó el tipo OACI en el texto (etiquetas AIRCRAFT / TYPE…). "
                    )
                )
                import_errors.append(
                    msg + "Los vuelos requieren una aeronave del catálogo."
                )
            else:
                aircraft = Aircraft.objects.filter(icao_code__iexact=ac_code).first()
                if not aircraft:
                    import_errors.append(
                        f'No existe ninguna aeronave con código OACI «{ac_code}» en '
                        "el sistema. Cree o edite tipos desde administración antes de importar."
                    )

            alternate = None
            alt_missing_note = ""
            alt_icao = (parsed.get("alternate_icao") or "").strip().upper()
            if alt_icao:
                alternate = Airport.objects.filter(icao_code__iexact=alt_icao).first()
                if not alternate:
                    alt_missing_note = (
                        f"No se encontró el aeropuerto alternativo OACI «{alt_icao}» "
                        "(el vuelo se guardará sin alternativo)."
                    )

            if import_errors:
                return render(
                    request,
                    "logbook/flight_import.html",
                    {"form": form, "import_errors": import_errors},
                )

            fn = parsed.get("flight_number") or ""
            flight_number = str(fn).strip()[:20]

            summary = []
            if is_xml:
                summary.append("Importación desde SimBrief (XML Datafile).")
            else:
                summary.append("Importación desde OFP texto (fallback heurístico).")

            if flight_number:
                summary.append(f"N.º vuelo detectado: {flight_number}.")
            summary.append(f"Aeronave OACI: {ac_code}.")
            summary.append(f"Ruta ICAO: {dep_icao} → {arr_icao}.")
            for fk, label in (
                ("ofp_fuel_ramp_kg", "Comb. rampa OFP"),
                ("ofp_fuel_takeoff_kg", "Comb. despegue OFP"),
                ("ofp_fuel_landing_kg", "Comb. llegada OFP"),
            ):
                v = parsed.get(fk)
                if v is not None:
                    summary.append(f"{label}: {v} kg.")
            if parsed.get("planned_departure_time"):
                summary.append(
                    f"Hora salida prevista (UTC): {parsed['planned_departure_time']}"
                )
            if parsed.get("route"):
                preview = (parsed["route"][:280] + "…") if len(parsed["route"]) > 280 else parsed["route"]
                summary.append(f"Ruta textual (extracto): {preview}")
            if alternate:
                summary.append(f"Alternativo: {alternate.icao_code}.")
            elif alt_missing_note:
                summary.append(alt_missing_note)

            route_text = parsed.get("route") or ""

            flight = FlightLog.objects.create(
                pilot=request.user,
                status=FlightLog.Status.PLANNED,
                planned_date=timezone.localdate(),
                aircraft=aircraft,
                departure_airport=departure,
                arrival_airport=arrival,
                alternate_airport=alternate,
                planned_departure_time=parsed.get("planned_departure_time"),
                estimated_flight_time=parsed.get("estimated_flight_time"),
                ofp_fuel_ramp_kg=parsed.get("ofp_fuel_ramp_kg"),
                ofp_fuel_takeoff_kg=parsed.get("ofp_fuel_takeoff_kg"),
                ofp_fuel_landing_kg=parsed.get("ofp_fuel_landing_kg"),
                flight_number=flight_number,
                route=route_text,
                imported_source="SIMBRIEF",
                imported_at=timezone.now(),
                remarks="\n".join(summary),
            )
            return redirect("logbook:flight_detail", pk=flight.pk)
    else:
        form = SimBriefImportForm()

    return render(
        request,
        "logbook/flight_import.html",
        {"form": form, "import_errors": import_errors},
    )


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

    total_all = qs.count()
    status_counts = {
        "planned": qs.filter(status=FlightLog.Status.PLANNED).count(),
        "in_progress": qs.filter(status=FlightLog.Status.IN_PROGRESS).count(),
        "completed": completed_count,
        "cancelled": qs.filter(status=FlightLog.Status.CANCELLED).count(),
    }
    next_planned = (
        qs.filter(
            status=FlightLog.Status.PLANNED,
            planned_date__gte=today,
        )
        .select_related("aircraft", "departure_airport", "arrival_airport")
        .order_by("planned_date", "id")
        .first()
    )
    next_planned_is_today = (
        bool(next_planned) and next_planned.planned_date == today
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
            "total_all": total_all,
            "status_counts": status_counts,
            "next_planned": next_planned,
            "next_planned_is_today": next_planned_is_today,
        },
    )


@login_required
@require_GET
def flight_list(request):
    """Lista vuelos con búsqueda, paginación y métricas de bitácora."""
    qs = (
        FlightLog.objects.filter(pilot=request.user)
        .select_related(
            "aircraft",
            "departure_airport",
            "arrival_airport",
        )
        .order_by("-planned_date", "-id")
    )

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(aircraft__registration__icontains=q)
            | Q(aircraft__manufacturer__icontains=q)
            | Q(aircraft__model__icontains=q)
            | Q(departure_airport__icao_code__icontains=q)
            | Q(departure_airport__city__icontains=q)
            | Q(arrival_airport__icao_code__icontains=q)
            | Q(arrival_airport__city__icontains=q)
            | Q(flight_number__icontains=q)
        )

    completed_for_user = FlightLog.objects.filter(
        pilot=request.user,
        status=FlightLog.Status.COMPLETED,
    )
    agg = completed_for_user.aggregate(s=Sum("total_time"))
    total_td = agg["s"]
    total_hours = (total_td.total_seconds() / 3600.0) if total_td else 0.0

    today = timezone.localdate()
    month_start = today.replace(day=1)
    month_agg = completed_for_user.filter(
        planned_date__gte=month_start,
        planned_date__lte=today,
    ).aggregate(s=Sum("total_time"))["s"]
    hours_this_month = (month_agg.total_seconds() / 3600.0) if month_agg else 0.0

    ninety_days_ago = today - timedelta(days=90)
    landings_90d = completed_for_user.filter(planned_date__gte=ninety_days_ago).count()

    paginator = Paginator(qs, 10)
    page_param = request.GET.get("page")
    try:
        flights_page = paginator.page(page_param)
    except PageNotAnInteger:
        flights_page = paginator.page(1)
    except EmptyPage:
        flights_page = paginator.page(paginator.num_pages)

    return render(
        request,
        "logbook/flight_list.html",
        {
            "flights": flights_page,
            "page_obj": flights_page,
            "paginator": paginator,
            "search_q": q,
            "total_hours": total_hours,
            "hours_this_month": hours_this_month,
            "landings_90d": landings_90d,
        },
    )


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


def _chart_attachment_count(dep_queryset, arr_queryset):
    n = 0
    for c in dep_queryset:
        if c.pdf_file or c.external_url:
            n += 1
    for c in arr_queryset:
        if c.pdf_file or c.external_url:
            n += 1
    return n


def _airport_lat_lon(airport):
    """Par [lat, lon] como float si el aeródromo tiene coordenadas, si no ``None``."""
    if airport is None or airport.latitude is None or airport.longitude is None:
        return None
    return [float(airport.latitude), float(airport.longitude)]


@login_required
@require_GET
def flight_detail(request, pk):
    """Detalle del vuelo: estado, acciones, cartas de aeropuertos de salida y llegada."""
    flight = get_object_or_404(
        FlightLog.objects.select_related(
            "aircraft",
            "departure_airport",
            "arrival_airport",
            "alternate_airport",
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

    last_completed = (
        FlightLog.objects.filter(
            pilot=request.user,
            status=FlightLog.Status.COMPLETED,
        )
        .exclude(pk=flight.pk)
        .select_related("aircraft", "departure_airport", "arrival_airport")
        .order_by("-planned_date", "-id")
        .first()
    )

    dep_ll = _airport_lat_lon(flight.departure_airport)
    arr_ll = _airport_lat_lon(flight.arrival_airport)
    alt_ll = _airport_lat_lon(flight.alternate_airport)
    route_map_json = None
    if dep_ll and arr_ll:
        route_map_json = mark_safe(
            json.dumps(
                {
                    "dep": dep_ll,
                    "arr": arr_ll,
                    "alt": alt_ll,
                    "dep_icao": flight.departure_airport.icao_code,
                    "arr_icao": flight.arrival_airport.icao_code,
                    "alt_icao": flight.alternate_airport.icao_code if flight.alternate_airport_id else None,
                }
            )
        )

    return render(
        request,
        "logbook/flight_detail.html",
        {
            "flight": flight,
            "departure_charts_by_type": _group_charts_by_type(dep_qs),
            "arrival_charts_by_type": _group_charts_by_type(arr_qs),
            "elapsed_in_progress_display": elapsed_in_progress_display,
            "last_completed": last_completed,
            "chart_attachment_count": _chart_attachment_count(dep_qs, arr_qs),
            "route_map_json": route_map_json,
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
        fb = _optional_decimal_from_post(request.POST, "fuel_on_board_start_kg")
        if fb is not None:
            flight.fuel_on_board_start_kg = fb
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
        fe = _optional_decimal_from_post(request.POST, "fuel_on_board_end_kg")
        if fe is not None:
            flight.fuel_on_board_end_kg = fe
        flight.save()
    return redirect("logbook:flight_detail", pk=pk)
