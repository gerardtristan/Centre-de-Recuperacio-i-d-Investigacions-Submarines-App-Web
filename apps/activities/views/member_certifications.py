"""«Les meves titulacions» a l'àrea personal (T-M02-44c; RN-M02-50): la persona veu les seves
titulacions i, d'una titulació d'una agència que no és la de destinació, demana l'homologació.

- Àrea personal: només un compte personal, i la persona és sempre la del compte; cap
  identificador de persona a la URL. La titulació es busca entre les seves: una d'una altra
  persona dona «no trobat». El servei (`filings.request_homologation`) ho torna a comprovar.
- Es mostra l'estat de l'última homologació de cada titulació; mai el número d'una altra persona
  ni cap foto (les fotos són de la T-M02-42).
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts.models import Account

from .. import catalogue, certifications, filings
from ..models import CertificationFiling, DiverCertification
from . import see_other

F = CertificationFiling


def _person(request):
    account = request.user
    if getattr(account, "kind", None) != Account.Kind.PERSONAL or account.person_id is None:
        raise Http404
    return account.person


def _rows(person):
    target = catalogue.target_agency()
    latest = {}
    for filing in F.objects.filter(person=person, kind=F.Kind.HOMOLOGATION).order_by(
        "requested_at", "pk"
    ):
        latest[filing.source_certification_id] = filing  # l'última de cada titulació
    rows = []
    for cert in certifications.of(person).select_related("agency").order_by("pk"):
        filing = latest.get(cert.pk)
        can_request = (
            target is not None
            and cert.agency_id not in (None, target.pk)
            and (filing is None or filing.status not in F.OPEN)
        )
        rows.append({
            "certification": cert,
            "origin": certifications.ORIGIN_LABELS[certifications.origin(cert)],
            "filing": filing,
            "can_request": can_request,
        })  # fmt: skip
    return rows, target


@never_cache
@require_http_methods(["GET", "POST"])
def my_certifications_view(request):
    person = _person(request)
    if request.method == "POST":
        pk = request.POST.get("titulacio", "")
        if not pk.isdigit():
            raise Http404
        cert = get_object_or_404(DiverCertification, pk=pk, person=person)
        try:
            filings.request_homologation(cert, by=request.user, request=request)
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(
                request, _("Homologació demanada. La secretaria la tramitarà a la federació.")
            )
        return see_other("activities:my_certifications")
    rows, target = _rows(person)
    return render(request, "activities/my_certifications.html", {"rows": rows, "target": target})
