from django.shortcuts import redirect, render

from .forms import FlightlogUserCreationForm


def register(request):
    """Alta de usuario estándar; redirige al login tras éxito."""
    if request.method == "POST":
        form = FlightlogUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:login")
    else:
        form = FlightlogUserCreationForm()
    return render(request, "users/register.html", {"form": form})
