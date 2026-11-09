"""El meu carnet, amb el compte personal (T-M01-19; P13, P-M01-E pas 2; RN-M01-18 a RN-M01-21).

Tot surt de la persona de la sessió: la ruta no porta cap identificador. Sense soci, «no trobat»
(P13, «propi si és soci»), com les quotes (T-M01-16).

Darrere del carnet (Q-065 de la 072): el contingut del wireframe aprovat (tipus, alta, quota,
llicència i text legal). Un exempt per edat té el carnet vàlid fins al 31/12 de l'últim any
exempt (Q-002). No es mostra el QR ni es descarrega el PDF: continuen oberts (diari de la
T-M01-19).
"""

from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .. import cards, services
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
        "exempt": cards.is_exempt(loaded),
        "licence": services.licence_record(loaded.person),
    }
    return render(request, "members/personal_card.html", context)
