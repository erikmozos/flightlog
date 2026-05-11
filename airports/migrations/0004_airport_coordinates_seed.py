# Approximate airport coordinates for European seed catalog (straight-line maps).

from decimal import Decimal

from django.db import migrations

# ICAO codes must match airports/migrations/0002_airport_icao_unique_seed_european.py
AIRPORT_COORDINATES = {
    "LEMD": (Decimal("40.471926"), Decimal("-3.562640")),
    "LEBL": (Decimal("41.297100"), Decimal("2.078500")),
    "LEPA": (Decimal("39.551700"), Decimal("2.738800")),
    "LEMG": (Decimal("36.674900"), Decimal("-4.499100")),
    "GCLP": (Decimal("27.931900"), Decimal("-15.386600")),
    "EGLL": (Decimal("51.470600"), Decimal("-0.461941")),
    "EGKK": (Decimal("51.148100"), Decimal("-0.190200")),
    "EGSS": (Decimal("51.884800"), Decimal("0.235000")),
    "EGCC": (Decimal("53.353700"), Decimal("-2.275000")),
    "EIDW": (Decimal("53.421300"), Decimal("-6.270100")),
    "LFPG": (Decimal("49.009691"), Decimal("2.547925")),
    "LFPO": (Decimal("48.726243"), Decimal("2.365247")),
    "LFMN": (Decimal("43.658400"), Decimal("7.215872")),
    "LFML": (Decimal("43.439269"), Decimal("5.221424")),
    "LFLL": (Decimal("45.725639"), Decimal("5.081119")),
    "EDDF": (Decimal("50.037932"), Decimal("8.562152")),
    "EDDM": (Decimal("48.353896"), Decimal("11.786077")),
    "EDDB": (Decimal("52.366703"), Decimal("13.503333")),
    "EDDH": (Decimal("53.630403"), Decimal("9.988228")),
    "EDDL": (Decimal("51.289454"), Decimal("6.766775")),
    "LIRF": (Decimal("41.794594"), Decimal("12.246238")),
    "LIMC": (Decimal("45.630606"), Decimal("8.728111")),
    "LIML": (Decimal("45.445099"), Decimal("9.276739")),
    "LIPZ": (Decimal("45.505279"), Decimal("12.351947")),
    "LIRN": (Decimal("40.886033"), Decimal("14.290781")),
    "EHAM": (Decimal("52.310539"), Decimal("4.768274")),
    "EBBR": (Decimal("50.901389"), Decimal("4.484444")),
    "ELLX": (Decimal("49.626574"), Decimal("6.211517")),
    "LSZH": (Decimal("47.458056"), Decimal("8.548056")),
    "LOWW": (Decimal("48.110278"), Decimal("16.569722")),
    "LPPT": (Decimal("38.781273"), Decimal("-9.135730")),
    "LPPR": (Decimal("41.248055"), Decimal("-8.681389")),
    "LPFR": (Decimal("37.014425"), Decimal("-7.965911")),
    "EKCH": (Decimal("55.618056"), Decimal("12.655833")),
    "ESSA": (Decimal("59.651901"), Decimal("17.918581")),
    "ENGM": (Decimal("60.197550"), Decimal("11.100361")),
    "EFHK": (Decimal("60.317222"), Decimal("24.963333")),
    "BIKF": (Decimal("63.985044"), Decimal("-22.608528")),
    "EPWA": (Decimal("52.165694"), Decimal("20.967122")),
    "LKPR": (Decimal("50.100833"), Decimal("14.426667")),
    "LHBP": (Decimal("47.436928"), Decimal("19.255592")),
    "LROP": (Decimal("44.571111"), Decimal("26.085000")),
    "LBSF": (Decimal("42.694722"), Decimal("23.395278")),
    "LGAV": (Decimal("37.936358"), Decimal("23.946486")),
    "LTAI": (Decimal("36.915125"), Decimal("30.794528")),
    "LTBA": (Decimal("41.974444"), Decimal("28.814722")),
    "LTFM": (Decimal("41.276667"), Decimal("28.738056")),
    "LCLK": (Decimal("34.875089"), Decimal("33.624919")),
}


def seed_coordinates(apps, schema_editor):
    Airport = apps.get_model("airports", "Airport")
    for icao, (lat, lon) in AIRPORT_COORDINATES.items():
        Airport.objects.filter(icao_code=icao).update(latitude=lat, longitude=lon)


def unseed_coordinates(apps, schema_editor):
    Airport = apps.get_model("airports", "Airport")
    icaos = list(AIRPORT_COORDINATES.keys())
    Airport.objects.filter(icao_code__in=icaos).update(latitude=None, longitude=None)


class Migration(migrations.Migration):

    dependencies = [
        ("airports", "0003_airport_latitude_longitude"),
    ]

    operations = [
        migrations.RunPython(seed_coordinates, unseed_coordinates),
    ]
