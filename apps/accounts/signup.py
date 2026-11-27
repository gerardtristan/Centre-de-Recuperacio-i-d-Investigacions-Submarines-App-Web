"""Compte personal ràpid (T-M01-53; decisió 108, D.1 i D.4; spec 00, «Compte personal»).

- Una sola pantalla: nom, cognoms, correu, contrasenya, la casella del butlletí (no marcada) i
  l'acceptació de la política de privacitat. Res més: les dades de soci es demanen a «Fer-se
  soci» (o a l'activitat), quan calen.
- Crea la persona i el compte personal **pendent** fins que es confirma el correu (RN-18); el
  compte no obté sessió abans. La privacitat i, si es marca, el butlletí queden com a
  consentiments de la 00 amb la versió exacta mostrada (`text_versions`). Amb la casella marcada,
  el 07 la subscriu en confirmar el correu (T-M07-32, senyal `email_verified`; darrere de
  `website.newsletter_enabled`).
- La resposta és la mateixa en tots els casos (no revela si el correu té compte), i fa la mateixa
  feina de càlcul (la contrasenya sempre es resumeix):
  - adreça amb un compte actiu: un avís sense enllaç que deixi entrar;
  - adreça amb un compte pendent: l'enllaç de verificació de nou, que des d'un altre navegador
    obliga a triar una contrasenya nova (revisió A: ningú no ocupa l'adreça d'una altra persona);
  - una persona activa amb aquest correu i sense compte personal (un soci importat, un
    convidat): cap persona nova; rep la invitació per crear el compte (revisió C).
- La verificació d'un compte creat aquí només l'activa amb la contrasenya de l'alta si es fa des
  del mateix navegador; si no, cal triar-ne una de nova (`email_links.confirm_email`).
- Els comptes pendents d'aquesta pantalla que no es confirmen en el termini de la verificació
  s'anonimitzen amb la persona (`purge_expired`, cada dia) i l'adreça queda lliure.
- Límits per origen i per destinatari amb el mecanisme del «Fer-se soci» (comptadors propis).
"""

import logging

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone

from apps.core import audit, consents, mail
from apps.core import privacy as core_privacy
from apps.core.models import AuditEntry, Consent, Person
from apps.core.normalization import normalize_email

from . import email_links, invitations, limits, tokens
from .models import Account
from .security import client_ip

logger = logging.getLogger("cris.security")
CREATED = "accounts.signup.created"
LIMITED = "accounts.signup.limited"
EXISTING_TEMPLATE = "compte-existent"
TEXT_KINDS = ("privacy", "newsletter")  # el butlletí, només si n'hi ha un text vigent
# Compte creat en aquest navegador: la seva verificació no demana contrasenya nova (revisió A).
SESSION_KEY = "signup_account"


def current_texts() -> dict | None:
    """Versió vigent de la privacitat (obligatòria) i del butlletí (opcional). Sense privacitat
    publicada, no es pot crear cap compte."""
    texts = {kind: consents.current_text(kind) for kind in TEXT_KINDS}
    if texts["privacy"] is None:
        return None
    return {kind: text for kind, text in texts.items() if text}


def created_here(account) -> bool:
    return AuditEntry.objects.filter(
        action=CREATED, target_type="accounts.account", target_id=str(account.pk)
    ).exists()


def _person_without_account(email: str):
    """Una sola persona activa amb aquest correu i sense compte personal, o None."""
    people = [
        person
        for person in Person.objects.filter(
            status=Person.Status.ACTIVE, contact_email__iexact=email
        )
        if not invitations.has_personal_account(person)
    ]
    return people[0] if len(people) == 1 else None


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
        existing = Account.objects.select_for_update().filter(login=email).first()
        known = _person_without_account(email) if existing is None else None
        if existing is not None or known is not None:
            make_password(data["password"])  # revisió B: la mateixa feina que crear el compte
            if not allowed:
                return True
            if known is not None:
                invitations.send(known, request=request)
            elif existing.status == Account.Status.PENDING:
                email_links.send_verification(existing)
            else:
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
        request.session[SESSION_KEY] = account.pk
        if allowed:
            email_links.send_verification(account)
    return True


def purge_expired(now=None) -> int:
    """Cada dia: els comptes pendents creats aquí que no s'han confirmat en el termini de la
    verificació s'anonimitzen amb la persona (l'adreça queda lliure). Els consentiments, que
    només s'afegeixen, queden lligats a la persona anonimitzada. Si la persona té res més (un
    altre compte o un bloqueig de l'esborrat), no es toca i queda al registre de l'aplicació."""
    limit = (now or timezone.now()) - tokens.VERIFY_EMAIL.max_age
    ids = AuditEntry.objects.filter(action=CREATED).values_list("target_id", flat=True)
    expired = Account.objects.filter(
        kind=Account.Kind.PERSONAL,
        status=Account.Status.PENDING,
        created_at__lt=limit,
        pk__in=[int(pk) for pk in ids if pk.isdigit()],
    ).select_related("person")
    done = 0
    for account in expired:
        person = account.person
        if person.accounts.count() > 1 or core_privacy.blockers(person):
            logger.info("signup_purge_skipped account=%s", account.pk)
            continue
        core_privacy.anonymise_person(person, by=None)
        done += 1
    return done
