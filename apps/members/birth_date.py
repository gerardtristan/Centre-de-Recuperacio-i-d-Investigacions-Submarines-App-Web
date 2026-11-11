"""Data de naixement que falta (T-M01-35; RN-M01-55, RN-M01-97; CA-M01-43; decisió 079, A-10).

- **El soci la completa al perfil**, només si encara no en té (`complete_own`). Un cop desada,
  només la corregeix la secretaria: el perfil no la torna a oferir.
- **La secretaria la completa o la corregeix** des de l'edició del soci, amb C1
  (`members.field.birth_date`, protegit) a més de P5 (`member_edit`).
- **Avís:** qui és soci i no té data veu un avís a l'inici i al perfil (`missing_for`).
- Una data futura es rebutja (A-10). El registre d'activitat diu que ha canviat i d'on ve, mai
  la data (RN-M01-48; `persons.set_birth_date`).
- Mentre no hi sigui, no es bloqueja res que el soci ja feia (RN-M01-55).

**No fet, pendent de decisió:** l'avís per correu de RN-M01-55 (quan s'envia: en importar, en
crear el compte o periòdicament; vegeu pendents.md). La data dels convidats (RN-M01-53) és dels
mòduls 02 i 06, que encara no existeixen.
"""

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import persons

from . import fee_rules
from .models import Member

SOURCE_PROFILE = "profile"
SOURCE_MEMBER_EDIT = "member_edit"


def missing_for(person) -> bool:
    """Cert si la persona és sòcia (no de baixa) i no té data de naixement."""
    if person.birth_date is not None:
        return False
    return Member.objects.filter(person=person).exclude(status=Member.Status.LEFT).exists()


def complete_own(person, birth_date, *, by, request=None) -> bool:
    """La persona completa la seva data. Només si encara no en té: si ja n'hi ha, no canvia res
    i torna False (la correcció és de la secretaria)."""
    if person.birth_date is not None:
        return False
    return persons.set_birth_date(person, birth_date, by=by, request=request, source=SOURCE_PROFILE)


class BirthDateForm(forms.Form):
    birth_date = forms.DateField(
        label=_("Data de naixement"),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        widget=forms.DateInput(attrs={"type": "date", "autocomplete": "bday"}, format="%Y-%m-%d"),
        error_messages={"invalid": _("Escriu una data vàlida, per exemple 12/03/1987.")},
        help_text=_("La fem servir per tramitar la llicència i per a l'edat mínima dels cursos."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].widget.attrs["max"] = timezone.localdate().isoformat()

    def clean_birth_date(self):
        value = self.cleaned_data["birth_date"]
        if value > timezone.localdate():
            raise forms.ValidationError(persons.BIRTH_DATE_IN_FUTURE)
        if fee_rules.age_today(value) > fee_rules.MAX_AGE:  # la mateixa regla que l'alta
            raise forms.ValidationError(_("Revisa la data de naixement."))
        return value
