from django import forms
from django.contrib.auth.forms import SetPasswordForm
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


class NewPasswordForm(SetPasswordForm):
    """Contrasenya nova, dues vegades, amb les regles de V-01 (AUTH_PASSWORD_VALIDATORS)."""

    error_messages = {"password_mismatch": _("Les dues contrasenyes no coincideixen.")}

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["new_password1"].label = gettext("Contrasenya nova")
        self.fields["new_password2"].label = gettext("Torna-la a escriure")
        self.fields["new_password2"].help_text = ""


class CodeForm(forms.Form):
    code = forms.CharField(
        label=_("Codi"),
        max_length=24,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "none"}),
    )
