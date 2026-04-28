from django.urls import path

from . import views

app_name = "logbook"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.flight_list, name="flight_list"),
    path("new/", views.flight_create, name="flight_create"),
    path("<int:pk>/", views.flight_detail, name="flight_detail"),
    path("<int:pk>/start/", views.flight_start, name="flight_start"),
    path("<int:pk>/finish/", views.flight_finish, name="flight_finish"),
]
