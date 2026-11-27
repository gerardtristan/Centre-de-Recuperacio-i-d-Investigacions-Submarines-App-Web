"""Compte personal ràpid (T-M01-53; decisió 108, D.1 i D.4; spec 00, «Compte personal»).

- Una sola pantalla: nom, cognoms, correu, contrasenya, la casella del butlletí (no marcada) i
  l'acceptació de la política de privacitat. Res més: les dades de soci es demanen a «Fer-se
  soci» (o a l'activitat), quan calen.
- Crea la persona i el compte personal **pendent** fins que es confirma el correu (RN-18); el
  compte no obté sessió abans. La privacitat i, si es marca, el butlletí queden com a
  consentiments de la 00 amb la versió exacta mostrada. La casella només desa l'elecció: la
  subscripció és de la T-M07-32 (darrere de `website.newsletter_enabled`).
- La resposta és la mateixa tant si el correu ja té compte com si no (no ho revela): si ja en té,
  aquella adreça rep un avís sense enllaç que deixi entrar i no es crea res.
- Límits per origen i per destinatari amb el mecanisme del «Fer-se soci» (comptadors propis).
"""

from django.db import transaction

from apps.core import audit, consents, mail
from apps.core.models import Consent, Person
from apps.core.normalization import normalize_email

from . import email_links, limits
from .models import Account
from .security import client_ip

CREATED = "accounts.signup.created"
LIMITED = "accounts.signup.limited"
EXISTING_TEMPLATE = "compte-existent"
TEXT_KINDS = ("privacy", "newsletter")  # el butlletí, només si n'hi ha un text vigent


def current_texts() -> dict | None:
    """Versió vigent de la privacitat (obligatòria) i del butlletí (opcional). Sense privacitat
    publicada, no es pot crear cap compte."""
    texts = {kind: consents.current_text(kind) for kind in TEXT_KINDS}
    if texts["privacy"] is None:
        return None
    return {kind: text for kind, text in texts.items() if text}


def create_account(request, data: dict, texts: dict) -> bool:
    """`data` és el `cleaned_data` de `SignupForm`. Torna False si l'origen està limitat (no es
    desa res); True en tots els altres casos, amb compte nou o sense."""
    email = normalize_email(data["email"])
    with transaction.atomic():
        accepted = limits.start_join(client_ip(request), limits.SIGNUP)
        if accepted is None:
            audit.record(LIMITED, actor=audit.ANONYMOUS, request=request)
            return False
        # Bloqueja l'adreça: dues altes alhora amb el mateix correu no en creen dues.
        allowed = limits.join_receipt_allowed(accepted, email)
        if Account.objects.filter(login=email).exists():
            if allowed:
                mail.queue_email(EXISTING_TEMPLATE, to=email)
            return True
        person = Person.objects.create(
            origin=Person.Origin.WEB,
            first_name=data["first_name"],
            last_name=data["last_name"],
            contact_email=email,
        )
        account = Account.objects.create_personal(person, email, data["password"])
        wanted = ["privacy"] + (["newsletter"] if data.get("accept_newsletter") else [])
        for kind in wanted:
            consents.grant_accepted(
                person, texts[kind], channel=Consent.Channel.WEB, by=account, request=request
            )
        audit.record(
            CREATED,
            actor=account,
            target=account,
            details={"newsletter": "newsletter" in wanted},
            request=request,
        )
        if allowed:
            email_links.send_verification(account)
    return True
