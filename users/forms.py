from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class FlightlogAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Correo electrónico"
        self.fields["username"].widget.attrs.update(
            {
                "class": "auth-input-field",
                "placeholder": "piloto@flightlog.com",
                "autocomplete": "username",
            }
        )
        self.fields["password"].label = "Contraseña"
        self.fields["password"].widget.attrs.update(
            {
                "class": "auth-input-field",
                "placeholder": "Tu contraseña",
                "autocomplete": "current-password",
            }
        )


class FlightlogUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Correo electrónico"
        self.fields["username"].widget.attrs.update(
            {
                "class": "auth-input-field",
                "placeholder": "piloto@flightlog.com",
                "autocomplete": "username",
            }
        )
        self.fields["password1"].label = "Contraseña"
        self.fields["password1"].help_text = ""
        self.fields["password1"].widget.attrs.update(
            {
                "class": "auth-input-field",
                "placeholder": "Mínimo 8 caracteres",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].label = "Confirmar contraseña"
        self.fields["password2"].help_text = ""
        self.fields["password2"].widget.attrs.update(
            {
                "class": "auth-input-field",
                "placeholder": "Repite tu contraseña",
                "autocomplete": "new-password",
            }
        )
