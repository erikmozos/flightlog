from datetime import datetime, timedelta

from django.db import migrations, models


def migrate_block_times_to_engine(apps, schema_editor):
    """Antes de borrar block_off/block_on, pasa tiempos a engine_* y deja vuelo como COMPLETED."""
    django_timezone = __import__("django.utils.timezone", fromlist=["timezone"]).timezone
    FlightLog = apps.get_model("logbook", "FlightLog")
    for fl in FlightLog.objects.order_by("pk"):
        b_off = getattr(fl, "block_off", None)
        b_on = getattr(fl, "block_on", None)
        if b_off is None or b_on is None:
            continue
        d = fl.planned_date
        start = datetime.combine(d, b_off)
        end = datetime.combine(d, b_on)
        if b_on < b_off:
            end += timedelta(days=1)
        if django_timezone.is_naive(start):
            start = django_timezone.make_aware(start)
            end = django_timezone.make_aware(end)
        fl.engine_start_time = start
        fl.engine_stop_time = end
        fl.status = "COMPLETED"
        fl.total_time = end - start
        fl.save()


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("logbook", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="flightlog",
            old_name="date",
            new_name="planned_date",
        ),
        migrations.AddField(
            model_name="flightlog",
            name="status",
            field=models.CharField(
                choices=[
                    ("PLANNED", "Planificado"),
                    ("IN_PROGRESS", "En curso"),
                    ("COMPLETED", "Completado"),
                    ("CANCELLED", "Cancelado"),
                ],
                default="PLANNED",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="planned_departure_time",
            field=models.TimeField(
                blank=True,
                help_text="Hora de salida prevista (opcional).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="engine_start_time",
            field=models.DateTimeField(
                blank=True,
                help_text="Momento en que se inician motores (al pasar a en curso).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="engine_stop_time",
            field=models.DateTimeField(
                blank=True,
                help_text="Momento en que se apagan motores al finalizar.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="flightlog",
            name="total_time",
            field=models.DurationField(
                blank=True,
                help_text="Tiempo de motor: se rellena al completar (engine_stop - engine_start).",
                null=True,
            ),
        ),
        migrations.RunPython(migrate_block_times_to_engine, reverse_noop),
        migrations.RemoveField(
            model_name="flightlog",
            name="block_off",
        ),
        migrations.RemoveField(
            model_name="flightlog",
            name="block_on",
        ),
    ]
