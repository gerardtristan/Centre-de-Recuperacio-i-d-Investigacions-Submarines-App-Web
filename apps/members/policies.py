"""Polítiques a la primera entrada dels importats de Cluber (T-M01-25; decisió 079, A-27 punt 4;
P-62 punt 4; RN-M01-95, CA-M01-109).

La plataforma no té cap prova de quina versió dels textos van acceptar a Cluber. Per això, a
qualsevol persona importada de Cluber (`Person.origin == CLUBER_IMPORT`) que entra amb el seu
compte personal se li demana que accepti les polítiques vigents (`GENERAL_TEXTS`: privacitat i
condicions de soci) abans de poder fer res més a l'àrea de socis. L'acceptació és un
`core.Consent` amb el canal web i la versió exacta, registrat amb el compte de la persona.

- Només el compte personal: l'administració no queda afectada.
- Es pot sortir sense acceptar. Les pàgines públiques i els fitxers estàtics no queden afectats.
- Si encara no hi ha cap text publicat d'un tipus, aquell tipus no es demana: no es pot acceptar
  un text que no existeix (la publicació és de M12).
- Q-029 continua oberta (si una versió nova obliga a tornar a acceptar): aquí n'hi ha prou amb
  un consentiment donat de qualsevol versió, com a `consents.has_consent`.
"""

from django.shortcuts import redirect
from django.urls import reverse

from apps.accounts.models import Account
from apps.core import consents
from apps.core.models import Consent, Person

from .forms import GENERAL_TEXTS, LEGAL_LABELS

SESSION_FLAG = "imported_policies_ok"
ALLOWED_URL_NAMES = {"members:accept_policies", "accounts:logout", "core:service_worker"}


def applies(account) -> bool:
    return (
        isinstance(account, Account)
        and account.kind == Account.Kind.PERSONAL
        and account.person.origin == Person.Origin.CLUBER_IMPORT
    )


def pending_texts(person) -> list:
    """(tipus, etiqueta, text vigent) dels textos que la persona encara no ha acceptat."""
    pending = []
    for kind in GENERAL_TEXTS:
        text = consents.current_text(kind)
        if text is not None and not consents.has_consent(person, kind):
            pending.append((kind, LEGAL_LABELS.get(kind, kind), text))
    return pending


def accept(person, kinds, *, by, request=None) -> int:
    """Registra l'acceptació dels textos vigents indicats. Torna quants n'ha registrat."""
    for kind in kinds:
        consents.grant(person, kind, channel=Consent.Channel.WEB, by=by, request=request)
    return len(kinds)


class ImportedPoliciesMiddleware:
    """Desvia a «Accepta les polítiques» qualsevol petició de l'àrea de socis d'un importat de
    Cluber que encara no les ha acceptades. Quan ja no en falta cap, la sessió ho recorda i no
    torna a consultar res."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or request.session.get(SESSION_FLAG):
            return None
        match = request.resolver_match
        if not getattr(view_func, "login_required", True) or match is None:
            return None
        if match.view_name in ALLOWED_URL_NAMES or "administration" in match.namespaces:
            return None
        if not applies(user):
            request.session[SESSION_FLAG] = True
            return None
        if pending_texts(user.person):
            return redirect(f"{reverse('members:accept_policies')}?next={request.path}")
        request.session[SESSION_FLAG] = True
        return None
