from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("logbook", "0005_flightlog_simbrief_and_route_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="flightlog",
            name="ofp_fuel_landing_kg",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Combustible previsto en llegada según OFP (kg).",
                max_digits=12,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="ofp_fuel_ramp_kg",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Combustible en rampa según OFP importado (kg).",
                max_digits=12,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="ofp_fuel_takeoff_kg",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Combustible al despegue previsto según OFP (kg).",
                max_digits=12,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="fuel_on_board_end_kg",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Combustible a bordo al apagar motores (kg).",
                max_digits=12,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="flightlog",
            name="fuel_on_board_start_kg",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Combustible a bordo al encender motores (kg).",
                max_digits=12,
                null=True,
            ),
        ),
    ]
