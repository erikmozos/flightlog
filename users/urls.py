from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import FlightlogAuthenticationForm

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        LoginView.as_view(
            template_name="users/login.html",
            authentication_form=FlightlogAuthenticationForm,
        ),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
]
