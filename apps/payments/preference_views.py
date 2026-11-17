"""`/socis/pagaments/metode/`: «Com pago la quota» (T-M05a-11; P-M05a-A; CA-M05a-01; wireframe
`socis.html#pagaments-metode`).

Només el soci de la sessió (cap identificador a la ruta), actiu o impagat i amb número: qualsevol
altra persona rep «no trobat», com a la pàgina del mandat. Cap rol de l'administració no tria per
un soci. Les opcions que no ofereix el proveïdor no arriben a l'HTML i el servidor les rebutja.
"""

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.members.models import Member

from . import preferences
from .models import FeeMethod

OPTIONS = {
    FeeMethod.SAVED_CARD: (
        gettext_lazy("Targeta guardada"),
        gettext_lazy(
            "La guardes una vegada al camp segur del proveïdor i la quota es cobra sola cada any."
        ),
    ),
    FeeMethod.DIRECT_DEBIT: (
        gettext_lazy("Domiciliació bancària"),
        gettext_lazy(
            "Signes un mandat SEPA amb el teu IBAN i el banc paga la quota cada any. "
            "El pots revocar quan vulguis."
        ),
    ),
    FeeMethod.PAY_EACH_TIME: (
        gettext_lazy("Pagar cada vegada"),
        gettext_lazy("Quan es generi la quota, la pagues amb targeta, Bizum o transferència."),
    ),
}


def _own_member(request) -> Member:
    member = Member.objects.filter(
        person=request.user.person,
        status__in=[Member.Status.ACTIVE, Member.Status.UNPAID],
        member_number__isnull=False,
    ).first()
    if member is None:
        raise Http404
    return member


def _mandate_url() -> str | None:
    # La pàgina del mandat (T-M05a-09) va apagada fins que la junta n'aprovi el text.
    return reverse("payments:mandate") if settings.MANDATE_SIGNING_ENABLED else None


def _save(request, member):
    try:
        preferences.set_preference(member, request.POST.get("method", ""), by=request.user)
    except preferences.NeedsMandate:
        if url := _mandate_url():
            return redirect(url)
        messages.error(
            request,
            _(
                "Per domiciliar la quota cal signar el mandat SEPA, i encara no es pot fer "
                "des de l'app."
            ),
        )
    except preferences.NeedsSavedCard:
        return redirect("payments:saved_card")
    except preferences.MethodNotOffered:
        messages.error(request, _("Tria una de les opcions."))
    else:
        messages.success(request, _("Hem desat com vols pagar la quota."))
    return redirect("payments:fee_method")


@never_cache
@require_http_methods(["GET", "POST"])
def fee_method_view(request):
    member = _own_member(request)
    if request.method == "POST":
        return _save(request, member)
    offered = preferences.offered_methods()
    recommended = (
        FeeMethod.SAVED_CARD if FeeMethod.SAVED_CARD in offered else FeeMethod.DIRECT_DEBIT
    )
    preference = preferences.current(member)
    chosen = preference.method if preference else None
    options = [
        {
            "value": method,
            "label": OPTIONS[method][0],
            "help": OPTIONS[method][1],
            "recommended": method == recommended,
            "checked": method == chosen,
        }
        for method in sorted(offered, key=list(OPTIONS).index)
    ]
    context = {
        "preference": preference,
        "mandate": preferences.active_mandate(member),
        "options": options,
    }
    return render(request, "payments/fee_method.html", context)
