from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import SetPasswordForm
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from .models import Account
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


class RecoveryRequestForm(forms.Form):
    email = forms.EmailField(
        label=_("Correu electrònic"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )


class NewPasswordForm(SetPasswordForm):
    """Contrasenya nova, dues vegades, amb les regles de V-01 (AUTH_PASSWORD_VALIDATORS)."""

    error_messages = {"password_mismatch": _("Les dues contrasenyes no coincideixen.")}

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["new_password1"].label = gettext("Contrasenya nova")
        self.fields["new_password2"].label = gettext("Torna-la a escriure")
        self.fields["new_password2"].help_text = ""


class OneTimeCodeInput(forms.TextInput):
    """Un codi TOTP o de recuperació: com la contrasenya, mai no es torna a mostrar després d'un
    error del formulari (V23, revisió final T-F1-01)."""

    def format_value(self, value):
        return None


class CodeForm(forms.Form):
    code = forms.CharField(
        label=_("Codi"),
        max_length=24,
        widget=OneTimeCodeInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "none"}),
    )


class ReauthForm(forms.Form):
    """Contrasenya i, només si el compte té TOTP actiu, el codi, per a `reauth.require_recent_auth`
    (T-M00-05). La contrasenya no és obligatòria al formulari: una de buida es comprova igualment
    i compta com a intent fallit (V-01). Abans era a `apps.members.forms`, que encara l'exporta."""

    password = forms.CharField(
        label=_("Contrasenya"),
        required=False,
        strip=False,
        help_text=_("Torna-la a escriure per confirmar que ets tu, encara que acabis d'entrar."),
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    code = forms.CharField(
        label=_("Codi de l'aplicació d'autenticació"),
        required=False,
        max_length=24,
        help_text=_("Les 6 xifres que mostra ara l'aplicació."),
        widget=OneTimeCodeInput(
            attrs={"autocomplete": "one-time-code", "inputmode": "numeric", "maxlength": "6"}
        ),
    )

    def __init__(self, *args, has_totp: bool, **kwargs):
        super().__init__(*args, **kwargs)
        if not has_totp:
            del self.fields["code"]


class ResetCredentialsForm(forms.Form):
    """Restabliment per un altre administrador (HU-08; RN-M01-60): què, per què i un codi
    TOTP nou de qui ho fa."""

    PASSWORD = "password"  # noqa: S105 (opció del formulari, no cap contrasenya)
    TOTP = "totp"

    what = forms.ChoiceField(
        label=_("Què vols restablir"),
        choices=[(PASSWORD, _("La contrasenya")), (TOTP, _("El doble factor (TOTP)"))],
        widget=forms.RadioSelect,
    )
    note = forms.CharField(
        label=_("Motiu"),
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Queda al registre d'activitat. No hi escriguis cap contrasenya ni codi."),
    )
    code = forms.CharField(
        label=_("El teu codi TOTP"),
        max_length=24,
        help_text=_("Un codi nou de la teva aplicació d'autenticació, per confirmar que ets tu."),
        widget=OneTimeCodeInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "none"}),
    )


class PersonalTotpResetForm(forms.Form):
    """Restabliment presencial del doble factor d'un compte personal (P-52; decisió 081, punt 24):
    comprovació de la identitat, motiu i un codi TOTP nou de qui ho fa."""

    document = forms.CharField(
        label=_("Número del document que t'ha mostrat"),
        max_length=30,
        help_text=_("Ha de coincidir amb el de la fitxa. No es desa ni surt al registre."),
        widget=forms.TextInput(attrs={"autocomplete": "off", "autocapitalize": "characters"}),
    )
    identity_checked = forms.BooleanField(
        label=_("He comprovat en persona la identitat del titular amb el seu document original."),
    )
    note = forms.CharField(
        label=_("Motiu"),
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Queda al registre d'activitat. No hi escriguis cap contrasenya ni codi."),
    )
    code = forms.CharField(
        label=_("El teu codi TOTP"),
        max_length=24,
        help_text=_("Un codi nou de la teva aplicació d'autenticació, per confirmar que ets tu."),
        widget=OneTimeCodeInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "none"}),
    )


class DisableTotpForm(CodeForm):
    """CA-05.2: per desactivar el doble factor cal la contrasenya i un codi vàlid."""

    password = forms.CharField(
        label=_("Contrasenya"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    field_order = ["password", "code"]


class SignupForm(forms.Form):
    """Compte personal ràpid (T-M01-53; decisió 108, D.1): res més que això. La contrasenya, una
    sola vegada, amb les regles de V-01 (AUTH_PASSWORD_VALIDATORS). Sense text vigent del
    butlletí, la casella no existeix."""

    accept_newsletter = forms.BooleanField(
        label=_("Vull rebre les sortides, els cursos i les novetats del C.R.I.S."),
        required=False,
    )
    first_name = forms.CharField(
        label=_("Nom"), max_length=100, widget=forms.TextInput(attrs={"autocomplete": "given-name"})
    )
    last_name = forms.CharField(
        label=_("Cognoms"),
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        label=_("Correu electrònic"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password = forms.CharField(
        label=_("Contrasenya"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    accept_privacy = forms.BooleanField(
        label=_("Política de privacitat"),  # surt al resum d'errors (Errata, T-DX-06)
        error_messages={
            "required": _("Cal acceptar la política de privacitat per crear el compte.")
        },
    )

    def __init__(self, *args, texts, **kwargs):
        super().__init__(*args, **kwargs)
        self.texts = texts
        if "newsletter" not in texts:
            del self.fields["accept_newsletter"]
        self.fields["password"].help_text = password_validation.password_validators_help_text_html()

    def clean(self):
        data = super().clean()
        password, email = data.get("password"), data.get("email")
        if password:
            # Les regles de V-01, comparades també amb el correu escrit.
            probe = Account(login=email or "")
            try:
                password_validation.validate_password(password, probe)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return data
