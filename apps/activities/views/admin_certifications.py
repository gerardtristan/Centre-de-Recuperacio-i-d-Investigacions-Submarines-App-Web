"""Titulacions d'una persona a l'administració (T-M02-52b; RN-M02-32; AC29, P-459). S'hi arriba
des de la fitxa del soci (P-572: només socis fins que hi hagi una fitxa de persona a
l'administració). AC29 de consulta veu la llista; amb «Sí», carrega i verifica. Ningú no ho fa
amb les seves pròpies. Els serveis (`certification_records`) ho tornen a comprovar tot.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.models import Person
from apps.core.permissions import has_perm, permission_required

from .. import certification_records as records
from .. import certifications
from ..models import (
    CertificationAgency,
    CertificationLevel,
    DiverCertification,
    TrainingCatalogueEntry,
)
from ..permissions import CERTIFICATIONS
from . import see_other

S = DiverCertification.Source


class LoadForm(forms.Form):
    source = forms.ChoiceField(
        label=_("Origen"),
        choices=[(S.DECLARED, _("Declarada per la persona")), (S.IMPORTED, _("Importada"))],
    )
    level = forms.ModelChoiceField(
        label=_("Nivell"), queryset=CertificationLevel.objects.order_by("rank"), required=False
    )
    speciality = forms.ModelChoiceField(
        label=_("O bé una especialitat"),
        queryset=TrainingCatalogueEntry.objects.filter(kind="speciality").order_by("name"),
        required=False,
    )
    agency = forms.ModelChoiceField(
        label=_("Agència de l'especialitat"),
        queryset=CertificationAgency.objects.filter(active=True).order_by("name"),
        required=False,
        help_text=_("La d'un nivell és la del nivell."),
    )
    number = forms.CharField(label=_("Número de la titulació"), max_length=40, required=False)
    issued_on = forms.DateField(
        label=_("Data"), required=False, widget=forms.DateInput(attrs={"type": "date"})
    )


@never_cache
@permission_required(CERTIFICATIONS)
@require_http_methods(["GET", "POST"])
def person_certifications_view(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    can_write = person.pk != request.user.person_id and has_perm(
        request.user, CERTIFICATIONS, write=True
    )
    form = LoadForm(request.POST if request.POST.get("accio") == "carrega" else None)
    if request.method == "POST":
        if request.POST.get("accio") == "verifica":
            certification = get_object_or_404(
                DiverCertification, pk=request.POST.get("titulacio"), person=person
            )
            try:
                records.verify(certification, by=request.user, request=request)
            except ValidationError as error:
                messages.error(request, error.messages[0])
            else:
                messages.success(request, _("Titulació verificada."))
            return see_other("administration:person_certifications", person.pk)
        if form.is_valid():
            try:
                records.load(person, by=request.user, request=request, **form.cleaned_data)
            except ValidationError as error:
                form.add_error(None, error)
            else:
                messages.success(request, _("Titulació carregada: queda sense verificar."))
                return see_other("administration:person_certifications", person.pk)
    rows = [
        {"certification": c, "origin": certifications.ORIGIN_LABELS[certifications.origin(c)],
         "can_verify": can_write and not c.is_verified and c.source in records.MANUAL_SOURCES}
        for c in certifications.of(person).select_related("agency")
    ]  # fmt: skip
    context = {"person": person, "rows": rows, "form": form if can_write else None}
    return render(request, "activities/person_certifications.html", context)
