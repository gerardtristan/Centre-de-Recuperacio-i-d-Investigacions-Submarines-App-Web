"""Homologacions a la federació a l'administració (T-M02-44b; vistes de `filings.py`; RN-M02-50,
51 i 53; CA-M02-53 i 54).

- **«Homologacions pendents»** (AC26): les obertes (`requested` i `filed`), la fitxa de cadascuna
  amb «Marca tramitada», «Marca feta» (nivell, número i data) i «Rebutja» (amb motiu), i el CSV per
  a la federació de les demanades.
- **«Demana una homologació»** (AC25): la secretaria la demana en nom d'una persona, triant una
  titulació d'una altra agència sense cap homologació oberta.
- **«Titulacions i llicències per tramitar»** (AC26; T-M02-45b; RN-M02-52, CA-M02-55): les
  tramitacions de la primera estrella obertes, amb la llicència de cada persona o «Cal
  llicència» i «Demana la primera llicència» (LC5, amb el càrrec habitual) quan el curs no
  la inclou (RN-M02-58). La fitxa de cada una és la de l'homologació.
- **Dades personals:** el nom de la persona i la seva titulació, només a qui té AC25 o AC26. El
  CSV porta la data de naixement i no es desa: la descàrrega queda al registre amb l'empremta.
  Cap foto ni document d'identitat. Sense permís, sempre «no trobat».
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.permissions import has_perm, permission_required
from apps.licences.filing import FILE_PERMISSION
from apps.licences.models import LicenceType
from apps.licences.services import LicenceRequestError

from .. import catalogue, filings
from ..models import CertificationFiling, CertificationLevel, DiverCertification
from ..permissions import CARD_PHOTOS_MANAGE, FILINGS
from . import see_other

F = CertificationFiling
LIST = "administration:filings"
COURSE_LIST = "administration:course_filings"


class DoneForm(forms.Form):
    target_level = forms.ModelChoiceField(
        label=_("Nivell de destinació"),
        queryset=CertificationLevel.objects.none(),
        empty_label=_("Tria…"),
    )
    number = forms.CharField(label=_("Número de la titulació nova"), max_length=40)
    issued_on = forms.DateField(
        label=_("Data"), widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        target = catalogue.target_agency()
        levels = CertificationLevel.objects.filter(agency=target) if target else None
        if levels is None:
            levels = CertificationLevel.objects.none()
        self.fields["target_level"].queryset = levels.order_by("rank", "name")


class RejectForm(forms.Form):
    reason = forms.CharField(
        label=_("Motiu del rebuig"), max_length=500, widget=forms.Textarea(attrs={"rows": 2})
    )


def eligible_certifications():
    """Titulacions d'una agència que no és la de destinació i sense cap homologació oberta."""
    target = catalogue.target_agency()
    open_filing = F.objects.filter(source_certification=OuterRef("pk"), status__in=F.OPEN)
    rows = DiverCertification.objects.filter(agency__isnull=False).exclude(Exists(open_filing))
    if target is not None:
        rows = rows.exclude(agency=target)
    return rows.select_related("person", "agency", "level", "speciality").order_by(
        "person__last_name", "person__first_name", "pk"
    )


class CertificationChoice(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        what = obj.level or obj.speciality
        number = f" ({obj.number})" if obj.number else ""
        return f"{obj.person.last_name}, {obj.person.first_name} · {obj.agency} {what}{number}"


class RequestForm(forms.Form):
    certification = CertificationChoice(
        label=_("Titulació"), queryset=DiverCertification.objects.none(), empty_label=_("Tria…")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["certification"].queryset = eligible_certifications()


@never_cache
@permission_required(FILINGS)
@require_GET
def filings_view(request):
    context = {
        "rows": filings.pending(by=request.user),
        "can_request": has_perm(request.user, CARD_PHOTOS_MANAGE, write=True),
        "can_export": has_perm(request.user, FILINGS, write=True),
    }
    return render(request, "activities/filings.html", context)


class FirstLicenceForm(forms.Form):
    filing = forms.IntegerField(widget=forms.HiddenInput)
    licence_type = forms.ModelChoiceField(
        label=_("Tipus de llicència"), queryset=LicenceType.objects.none(), empty_label=_("Tria…")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["licence_type"].queryset = LicenceType.objects.filter(active=True)
        self.fields["licence_type"].initial = filings.included_licence_type()


@never_cache
@permission_required(FILINGS)
@require_http_methods(["GET", "POST"])
def course_filings_view(request):
    """T-M02-45b: «Titulacions i llicències per tramitar». POST: «Demana la primera llicència»
    d'una tramitació oberta (el servei rebutja un curs que la inclou; el 06 comprova LC5)."""
    if request.method == "POST":
        form = FirstLicenceForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Tria un tipus de llicència."))
            return see_other(COURSE_LIST)
        filing = get_object_or_404(
            F, pk=form.cleaned_data["filing"], kind=F.Kind.COURSE, status__in=F.OPEN
        )
        try:
            filings.request_first_licence(
                filing, form.cleaned_data["licence_type"], by=request.user
            )
        except LicenceRequestError as error:
            messages.error(request, str(error.message))
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(request, _("Primera llicència demanada, amb el seu càrrec."))
        return see_other(COURSE_LIST)
    context = {
        "rows": filings.course_pending(by=request.user),
        "can_request": has_perm(request.user, FILE_PERMISSION, write=True),
        "form": FirstLicenceForm(),
    }
    return render(request, "activities/course_filings.html", context)


@never_cache
@permission_required(FILINGS, write=True)
@require_POST
def filings_csv_view(request):
    """RN-M02-53: el CSV de les demanades. POST: la descàrrega queda al registre."""
    content = filings.federation_csv(by=request.user, request=request)
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    name = f"homologacions-{timezone.localdate():%Y-%m-%d}.csv"
    response["Content-Disposition"] = f'attachment; filename="{name}"'
    return response


def _filing(pk):
    related = (
        "person",
        "source_certification__level",
        "source_certification__agency",
        "source_certification__speciality",
        "target_level",
    )
    return get_object_or_404(F.objects.select_related(*related), pk=pk)


def _detail(request, filing, *, done_form=None, reject_form=None):
    can_change = filing.status in F.OPEN and has_perm(request.user, FILINGS, write=True)
    context = {
        "filing": filing,
        "can_change": can_change,
        "can_file": can_change and filing.status == F.Status.REQUESTED,
        "done_form": (done_form or DoneForm()) if can_change else None,
        "reject_form": (reject_form or RejectForm()) if can_change else None,
    }
    return render(request, "activities/filing_detail.html", context)


@never_cache
@permission_required(FILINGS)
@require_GET
def filing_detail_view(request, pk):
    return _detail(request, _filing(pk))


@never_cache
@permission_required(FILINGS, write=True)
@require_POST
def filing_filed_view(request, pk):
    filing = _filing(pk)
    try:
        filings.mark_filed(filing, by=request.user, request=request)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Homologació marcada com a tramitada."))
    return see_other("administration:filing_detail", filing.pk)


@never_cache
@permission_required(FILINGS, write=True)
@require_POST
def filing_done_view(request, pk):
    filing = _filing(pk)
    form = DoneForm(request.POST)
    if form.is_valid():
        try:
            filings.mark_done(filing, by=request.user, request=request, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Homologació feta: la titulació nova ja és a la fitxa."))
            return see_other(LIST)
    return _detail(request, filing, done_form=form)


@never_cache
@permission_required(FILINGS, write=True)
@require_POST
def filing_reject_view(request, pk):
    filing = _filing(pk)
    form = RejectForm(request.POST)
    if form.is_valid():
        try:
            filings.reject(filing, by=request.user, request=request, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Homologació rebutjada amb el motiu."))
            return see_other(LIST)
    return _detail(request, filing, reject_form=form)


@never_cache
@permission_required(CARD_PHOTOS_MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def filing_request_view(request):
    """RN-M02-50: la secretaria (AC25) demana l'homologació en nom d'una persona."""
    form = RequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            filings.request_homologation(
                form.cleaned_data["certification"], by=request.user, request=request
            )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Homologació demanada: ja surt a les pendents."))
            return see_other(LIST)
    return render(request, "activities/filing_request.html", {"form": form})
