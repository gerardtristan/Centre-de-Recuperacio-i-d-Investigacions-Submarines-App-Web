"""El meu carnet, amb el compte personal (T-M01-19; P13, P-M01-E pas 2; RN-M01-18 a RN-M01-21).

Tot surt de la persona de la sessió: la ruta no porta cap identificador. Sense soci, «no trobat»
(P13, «propi si és soci»), com les quotes (T-M01-16).

Darrere del carnet (Q-065 de la 072): el contingut del wireframe aprovat (tipus, alta, quota,
llicència i text legal). Un exempt per edat té el carnet vàlid fins al 31/12 de l'últim any
exempt (Q-002).

Decisió 079 (RN-M01-85 i 92):
- **QR:** es torna a calcular a cada visita amb la clau del servidor (`cards.qr_svg`) i porta
  l'adreça de verificació pública. El testimoni no es desa ni surt al registre. La resposta és
  `no-store` (`never_cache`); la còpia sense connexió la desa el service worker (CA-M01-17).
- **PDF:** la impressió del navegador («Desa com a PDF»), amb estils d'impressió; cap generador
  al servidor.
- **Carnet nou a petició del soci** (RN-M01-25): POST a `card_renew`; revoca l'actual i n'emet
  un amb una versió nova. També serveix quan el QR ja no es pot mostrar (carnet anterior a la
  079 o clau retirada) o quan la secretaria l'ha revocat.
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .. import cards, services
from ..cards import CardNotAllowed
from ..fee_rules import local_today
from .personal import _own_member_or_404


@never_cache
@require_GET
def card_view(request):
    member = _own_member_or_404(request)
    loaded = cards.load_member(member.pk)
    card = cards.active_card(loaded)
    today = local_today()
    svg = cards.qr_svg(card)
    context = {
        "member": loaded,
        "person": loaded.person,
        "card": card,
        "validity": cards.validity(loaded, card, today) if card else None,
        "years": cards.years_of_membership(loaded, today),
        "exempt": cards.is_exempt(loaded),
        "licence": services.licence_record(loaded.person),
        # SVG generat pel servidor (qrcode), sense cap dada escrita per l'usuari.
        "qr_svg": mark_safe(svg) if svg else "",  # noqa: S308
        "can_request": cards.may_request_new_card(loaded),
    }
    return render(request, "members/personal_card.html", context)


@never_cache
@require_POST
def card_renew_view(request):
    """Carnet nou a petició del soci (RN-M01-25): només el del soci de la sessió."""
    member = _own_member_or_404(request)
    try:
        cards.request_new_card(member, by=request.user, request=request)
    except CardNotAllowed as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Tens un carnet nou. El codi QR de l'anterior ja no és vàlid."))
    response = redirect("members:card")
    response.status_code = 303
    return response
