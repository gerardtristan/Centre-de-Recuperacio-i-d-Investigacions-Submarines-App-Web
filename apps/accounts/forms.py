from django import forms

from .security import AREA_ADMIN


class LoginForm(forms.Form):
    login = forms.CharField(max_length=254, strip=True)
    password = forms.CharField(
        label="Contrasenya",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, area, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["login"]
        if area == AREA_ADMIN:
            field.label = "Nom d'usuari"
            field.widget.attrs.update(autocomplete="username", autocapitalize="none")
        else:
            field.label = "Correu electrònic"
            field.widget = forms.EmailInput(attrs={"autocomplete": "email"})


class CodeForm(forms.Form):
    code = forms.CharField(
        label="Codi",
        max_length=24,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "none"}),
    )
