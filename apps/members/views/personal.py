"""Àrea del soci amb el compte personal (T-M01-16; P12, P13; CA-M01-12, CA-M01-25).

Totes les dades surten de la persona de la sessió (`request.user.person`): cap ruta no porta
l'identificador d'una persona ni d'un soci. L'única que porta un identificador, el detall d'una
quota, el busca només entre les quotes pròpies; si no hi és (no existeix o és d'un altre), la
resposta és «no trobat» en tots dos casos i l'intent queda al registre (CA-M01-25).

El compte personal no hereta cap rol (059, punt 4.2); el middleware ja no deixa entrar-hi una
sessió d'administració.
"""

from decimal import Decimal

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.formats import number_format
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core import audit, persons
from apps.core.models import Charge

from .. import roster
from ..forms import LEGAL_LABELS, ProfileForm
from ..models import AnnualFee, Member


def euros(cents: int) -> str:
    return f"{number_format(Decimal(cents) / 100, decimal_pos=2)} €"


def masked_document(person) -> str:
    """Document emmascarat fora de la secretaria (M01-12): només els quatre últims caràcters."""
    number = person.id_document_number
    return "·" * max(len(number) - 4, 0) + number[-4:] if number else ""


def own_member(request) -> Member | None:
    return Member.objects.select_related("type").filter(person=request.user.person).first()


def own_consents(person):
    """Últim estat de cada text de la persona, com a la fitxa (T-M01-15). Només lectura: quins
    es poden retirar des del perfil depèn de Q-16."""
    latest = {}
    for consent in person.consents.select_related("legal_text").order_by("created_at", "id"):
        latest[consent.legal_text.kind] = consent
    return [(LEGAL_LABELS.get(kind, kind), consent) for kind, consent in sorted(latest.items())]


@never_cache
@require_http_methods(["GET", "POST"])
def profile_view(request):
    person = request.user.person
    initial = {
        "phone": person.phone,
        "address": person.address,
        "preferred_language": person.preferred_language,
    }
    form = ProfileForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        changed = persons.update_profile(
            person, actor=request.user, request=request, **form.cleaned_data
        )
        messages.success(request, _("Canvis desats.") if changed else _("No has canviat cap dada."))
        return redirect("members:profile")
    context = {
        "person": person,
        "member": own_member(request),
        "document": masked_document(person),
        "form": form,
        "consents": own_consents(person),
        "requests": person.member_requests.order_by("-created_at", "-id"),
    }
    return render(request, "members/personal_profile.html", context)


def _fee_row(fee):
    payments = list(fee.charge.payments.all())
    paid_on = None
    # Data del pagament només si n'hi ha exactament un, com a l'estat de la quota (T-M01-15).
    if fee.charge.status == Charge.Status.PAID and len(payments) == 1:
        paid_on = payments[0].paid_at
    return {"fee": fee, "amount": euros(fee.charge.amount_cents), "paid_on": paid_on}


def _own_member_or_404(request):
    """Les quotes són «pròpies si és soci» (P13): sense soci, no hi ha res a veure."""
    member = own_member(request)
    if member is None:
        raise Http404
    return member


@never_cache
@require_GET
def fees_view(request):
    """Les meves quotes (CA-M01-12, L-M01-09). El rebut és del 05b (RN-M05b-19)."""
    member = _own_member_or_404(request)
    loaded = roster.with_fee_data(Member.objects.filter(pk=member.pk)).get()
    fees = (
        AnnualFee.objects.filter(member=member)
        .select_related("charge")
        .prefetch_related("charge__payments")
        .order_by("-period", "-id")
    )
    context = {
        "member": member,
        "fee": roster.fee_state(loaded),
        "rows": [_fee_row(fee) for fee in fees],
    }
    return render(request, "members/personal_fees.html", context)


@never_cache
@require_GET
def fee_detail_view(request, fee_id):
    """Una quota pròpia. Una d'un altre o una que no existeix: «no trobat» i registre."""
    fee = (
        AnnualFee.objects.select_related("charge")
        .prefetch_related("charge__payments")
        .filter(pk=fee_id, member__person=request.user.person)
        .first()
    )
    if fee is None:
        audit.record(
            audit.Action.PERSONAL_AREA_NOT_FOUND,
            actor=request.user,
            target=AnnualFee.objects.filter(pk=fee_id).first(),
            details={"object": "members.annualfee", "id": fee_id},
            request=request,
        )
        raise Http404
    row = _fee_row(fee)
    payment = fee.charge.payments.all()[0] if row["paid_on"] else None
    return render(request, "members/personal_fee_detail.html", {**row, "payment": payment})
