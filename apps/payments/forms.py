"""Formulari de la signatura del mandat (T-M05a-09; P-M05a-B; wireframe
`socis.html#pagaments-mandat`).

L'IBAN es valida al servidor (RN-M05a-05) i l'error no el repeteix mai; la vista buida el camp
abans de tornar a dibuixar el formulari, de manera que la resposta no porta l'IBAN rebutjat."""

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.forms import ReauthForm

from . import mandates


class RecentAuthForm(ReauthForm):
    """La contrasenya (i el codi) només si la sessió no és recent (RN-M05a-12). Sol, és el
    formulari de revocar (T-M05a-10)."""

    def __init__(self, *args, has_totp: bool, ask_password: bool, **kwargs):
        super().__init__(*args, has_totp=has_totp, **kwargs)
        self.fields["password"].help_text = _(
            "Fa una estona que has entrat: torna-la a escriure per confirmar que ets tu."
        )
        if not ask_password:
            # La sessió és recent: el servidor no demana res (es torna a comprovar en desar).
            del self.fields["password"]
            self.fields.pop("code", None)


class MandateForm(RecentAuthForm):
    field_order = ["holder_name", "other_holder", "iban", "accept", "password", "code"]

    holder_name = forms.CharField(
        label=_("Titular del compte"),
        max_length=70,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
        error_messages={"required": _("Escriu el nom del titular del compte.")},
    )
    other_holder = forms.BooleanField(
        label=_("El titular del compte és una altra persona i m'ha autoritzat"),
        required=False,
    )
    iban = forms.CharField(
        label=_("IBAN"),
        max_length=42,
        help_text=_("Es desa xifrat. Després només en veuràs els quatre últims caràcters."),
        widget=forms.TextInput(
            attrs={"autocomplete": "off", "spellcheck": "false", "autocapitalize": "characters"}
        ),
        error_messages={"required": _("Escriu l'IBAN.")},
    )
    accept = forms.BooleanField(
        label=_("Accepto el mandat SEPA amb aquest text."),
        error_messages={"required": _("Marca la casella per acceptar el mandat.")},
    )

    def clean_iban(self):
        return mandates.validate_mandate_iban(self.cleaned_data["iban"])
