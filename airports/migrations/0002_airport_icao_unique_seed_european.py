# European airport catalog seed (matches bundled JSON list).

from django.db import migrations, models

EUROPEAN_AIRPORTS = [
    {"icao_code": "LEMD", "name": "Adolfo Suárez Madrid-Barajas", "city": "Madrid", "country": "Spain"},
    {"icao_code": "LEBL", "name": "Josep Tarradellas Barcelona-El Prat", "city": "Barcelona", "country": "Spain"},
    {"icao_code": "LEPA", "name": "Palma de Mallorca", "city": "Palma de Mallorca", "country": "Spain"},
    {"icao_code": "LEMG", "name": "Málaga-Costa del Sol", "city": "Málaga", "country": "Spain"},
    {"icao_code": "GCLP", "name": "Gran Canaria", "city": "Las Palmas", "country": "Spain"},
    {"icao_code": "EGLL", "name": "London Heathrow", "city": "London", "country": "United Kingdom"},
    {"icao_code": "EGKK", "name": "London Gatwick", "city": "London", "country": "United Kingdom"},
    {"icao_code": "EGSS", "name": "London Stansted", "city": "London", "country": "United Kingdom"},
    {"icao_code": "EGCC", "name": "Manchester", "city": "Manchester", "country": "United Kingdom"},
    {"icao_code": "EIDW", "name": "Dublin", "city": "Dublin", "country": "Ireland"},
    {"icao_code": "LFPG", "name": "Paris Charles de Gaulle", "city": "Paris", "country": "France"},
    {"icao_code": "LFPO", "name": "Paris Orly", "city": "Paris", "country": "France"},
    {"icao_code": "LFMN", "name": "Nice Côte d'Azur", "city": "Nice", "country": "France"},
    {"icao_code": "LFML", "name": "Marseille Provence", "city": "Marseille", "country": "France"},
    {"icao_code": "LFLL", "name": "Lyon-Saint Exupéry", "city": "Lyon", "country": "France"},
    {"icao_code": "EDDF", "name": "Frankfurt am Main", "city": "Frankfurt", "country": "Germany"},
    {"icao_code": "EDDM", "name": "Munich", "city": "Munich", "country": "Germany"},
    {"icao_code": "EDDB", "name": "Berlin Brandenburg", "city": "Berlin", "country": "Germany"},
    {"icao_code": "EDDH", "name": "Hamburg", "city": "Hamburg", "country": "Germany"},
    {"icao_code": "EDDL", "name": "Düsseldorf", "city": "Düsseldorf", "country": "Germany"},
    {"icao_code": "LIRF", "name": "Rome Fiumicino", "city": "Rome", "country": "Italy"},
    {"icao_code": "LIMC", "name": "Milan Malpensa", "city": "Milan", "country": "Italy"},
    {"icao_code": "LIML", "name": "Milan Linate", "city": "Milan", "country": "Italy"},
    {"icao_code": "LIPZ", "name": "Venice Marco Polo", "city": "Venice", "country": "Italy"},
    {"icao_code": "LIRN", "name": "Naples", "city": "Naples", "country": "Italy"},
    {"icao_code": "EHAM", "name": "Amsterdam Schiphol", "city": "Amsterdam", "country": "Netherlands"},
    {"icao_code": "EBBR", "name": "Brussels", "city": "Brussels", "country": "Belgium"},
    {"icao_code": "ELLX", "name": "Luxembourg", "city": "Luxembourg", "country": "Luxembourg"},
    {"icao_code": "LSZH", "name": "Zurich", "city": "Zurich", "country": "Switzerland"},
    {"icao_code": "LOWW", "name": "Vienna", "city": "Vienna", "country": "Austria"},
    {"icao_code": "LPPT", "name": "Lisbon Humberto Delgado", "city": "Lisbon", "country": "Portugal"},
    {"icao_code": "LPPR", "name": "Porto", "city": "Porto", "country": "Portugal"},
    {"icao_code": "LPFR", "name": "Faro", "city": "Faro", "country": "Portugal"},
    {"icao_code": "EKCH", "name": "Copenhagen", "city": "Copenhagen", "country": "Denmark"},
    {"icao_code": "ESSA", "name": "Stockholm Arlanda", "city": "Stockholm", "country": "Sweden"},
    {"icao_code": "ENGM", "name": "Oslo Gardermoen", "city": "Oslo", "country": "Norway"},
    {"icao_code": "EFHK", "name": "Helsinki-Vantaa", "city": "Helsinki", "country": "Finland"},
    {"icao_code": "BIKF", "name": "Keflavík", "city": "Reykjavík", "country": "Iceland"},
    {"icao_code": "EPWA", "name": "Warsaw Chopin", "city": "Warsaw", "country": "Poland"},
    {"icao_code": "LKPR", "name": "Václav Havel Prague", "city": "Prague", "country": "Czech Republic"},
    {"icao_code": "LHBP", "name": "Budapest Ferenc Liszt", "city": "Budapest", "country": "Hungary"},
    {"icao_code": "LROP", "name": "Bucharest Henri Coandă", "city": "Bucharest", "country": "Romania"},
    {"icao_code": "LBSF", "name": "Sofia", "city": "Sofia", "country": "Bulgaria"},
    {"icao_code": "LGAV", "name": "Athens Eleftherios Venizelos", "city": "Athens", "country": "Greece"},
    {"icao_code": "LTAI", "name": "Antalya", "city": "Antalya", "country": "Turkey"},
    {"icao_code": "LTBA", "name": "Istanbul Atatürk", "city": "Istanbul", "country": "Turkey"},
    {"icao_code": "LTFM", "name": "Istanbul", "city": "Istanbul", "country": "Turkey"},
    {"icao_code": "LCLK", "name": "Larnaca", "city": "Larnaca", "country": "Cyprus"},
]


def seed_european_airports(apps, schema_editor):
    Airport = apps.get_model("airports", "Airport")
    for row in EUROPEAN_AIRPORTS:
        Airport.objects.update_or_create(
            icao_code=row["icao_code"],
            defaults={
                "name": row["name"],
                "city": row["city"],
                "country": row["country"],
            },
        )


def unseed_european_airports(apps, schema_editor):
    Airport = apps.get_model("airports", "Airport")
    codes = [r["icao_code"] for r in EUROPEAN_AIRPORTS]
    Airport.objects.filter(icao_code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("airports", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="airport",
            name="icao_code",
            field=models.CharField(max_length=4, unique=True),
        ),
        migrations.RunPython(seed_european_airports, unseed_european_airports),
    ]
