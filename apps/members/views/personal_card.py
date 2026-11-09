"""El meu carnet, amb el compte personal (T-M01-19; P13, P-M01-E pas 2; RN-M01-18 a RN-M01-21).

Tot surt de la persona de la sessió: la ruta no porta cap identificador. Sense soci, «no trobat»
(P13, «propi si és soci»), com les quotes (T-M01-16).

No es mostra el QR ni es descarrega el PDF: només es desa l'empremta del testimoni i no hi ha
cap llibreria de PDF al projecte (vegeu el diari de la T-M01-19).
"""

from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .. import cards
from ..fee_rules import local_today
from .personal import _own_member_or_404


@never_cache
@require_GET
def card_view(request):
    member = _own_member_or_404(request)
    loaded = cards.load_member(member.pk)
    card = cards.active_card(loaded)
    today = local_today()
    context = {
        "member": loaded,
        "person": loaded.person,
        "card": card,
        "validity": cards.validity(loaded, card, today) if card else None,
        "years": cards.years_of_membership(loaded, today),
    }
    return render(request, "members/personal_card.html", context)
