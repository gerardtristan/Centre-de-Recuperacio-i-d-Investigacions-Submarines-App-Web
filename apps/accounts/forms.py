from django import forms
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from .security import AREA_ADMIN


class LoginForm(forms.Form):
    login = forms.CharField(max_length=254, strip=True)
    password = forms.CharField(
        label=_("Contrasenya"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, area, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["login"]
        if area == AREA_ADMIN:
            field.label = gettext("Nom d'usuari")
            field.widget.attrs.update(autocomplete="username", autocapitalize="none")
        else:
            field.label = gettext("Correu electrònic")
            field.widget = forms.EmailInput(attrs={"autocomplete": "email"})


class CodeForm(forms.Form):
    code = forms.CharField(
        label=_("Codi"),
        max_length=24,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "none"}),
    )
