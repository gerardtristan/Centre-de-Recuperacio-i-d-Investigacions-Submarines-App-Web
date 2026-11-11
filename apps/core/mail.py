"""Correu de la plataforma, versió mínima (spec 00, annex A; decisions 004, 012, 019, 042 i 061).

Tots els mòduls envien correus amb `queue_email`; cap no parla amb el proveïdor. El transport
és el `EMAIL_BACKEND` de Django configurat per entorn (SMTP a producció): canviar de Brevo a
Scaleway Transactional Email, o a qualsevol altre, és canviar la configuració.

- Plantilles pròpies a `templates/emails/`, una per llengua: `<nom>.<llengua>.subject.txt`,
  `<nom>.<llengua>.txt` i, opcional, `<nom>.<llengua>.html`. Es tria la llengua de
  `persons.language_for(persona)` i, si no hi ha la plantilla, la catalana (061, punt 7).
- El correu es genera en posar-lo a la cua, dins de `translation.override`: la cua no té cap
  petició ni cap `Accept-Language`. El missatge guarda la llengua amb què s'ha generat.
- L'enviament el fa la cua de tasques (RN-A13) dins la mateixa transacció: si l'acció es desfà,
  no queda ni el correu ni la tasca.
- Mai contrasenyes ni adjunts (RN-A12). Res d'això va al registre d'activitat.
- Les persones anonimitzades no reben correus (RN-A14). Es comprova en posar-lo a la cua: un
  correu posat abans d'anonimitzar (la confirmació d'un esborrat RGPD) surt igualment.
- En anonimitzar una persona (T-M01-22), l'adreça dels seus enviaments se substitueix
  (`anonymise_recipient`); la dels que encara esperen, quan es tanquen (`_close`).

Fora d'abast ara: comptador diari, reserva i tandes, avís del 80 %, butlletí i avisos del
proveïdor (RN-A3 a RN-A6, RN-A9 i RN-A10); s'hi afegeixen quan calguin.
"""

import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.template import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string
from django.utils import timezone, translation

from .models import OutgoingEmail, Person
from .persons import anonymous_email, language_for

_TEMPLATE_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
# RN-A12: res que sembli una contrasenya o un secret entra al context d'una plantilla. Els
# enllaços d'un sol ús sí que hi poden anar (verificació, recuperació, convidat).
_FORBIDDEN_CONTEXT_PARTS = ("password", "contrasenya", "secret", "totp", "recovery_code")


class EmailDeliveryError(Exception):
    """El proveïdor no ha acceptat el correu; la cua ho tornarà a provar."""


def _check_context(context) -> None:
    for key in context:
        lowered = str(key).lower()
        if any(part in lowered for part in _FORBIDDEN_CONTEXT_PARTS):
            raise ValueError(f"Un correu no porta mai contrasenyes ni secrets: «{key}» (RN-A12).")


def _template_language(name: str, language: str) -> str:
    """La llengua demanada si en té plantilla; si no, la de reserva (el català)."""
    for candidate in dict.fromkeys([language, settings.LANGUAGE_CODE]):
        try:
            get_template(f"emails/{name}.{candidate}.txt")
        except TemplateDoesNotExist:
            continue
        return candidate
    raise TemplateDoesNotExist(f"emails/{name}.{settings.LANGUAGE_CODE}.txt")


def _render(name: str, language: str, context) -> tuple[str, str, str]:
    base = f"emails/{name}.{language}"
    with translation.override(language):
        # Una sola línia: les capçaleres no admeten salts de línia.
        subject = " ".join(render_to_string(f"{base}.subject.txt", context).split())
        body_text = render_to_string(f"{base}.txt", context)
        try:
            body_html = render_to_string(f"{base}.html", context)
        except TemplateDoesNotExist:
            body_html = ""
    return subject, body_text, body_html


def queue_email(
    template: str, *, to: str, person: Person | None = None, context=None
) -> OutgoingEmail | None:
    """Genera el correu i el posa a la cua. Torna el registre de l'enviament, o `None` si la
    persona és anonimitzada (RN-A14).

    `person` decideix la llengua; sense persona (p. ex. un correu de prova), el català.
    """
    if not _TEMPLATE_NAME.match(template):
        raise ValueError(f"Nom de plantilla no vàlid: «{template}».")
    if person is not None and person.status == Person.Status.ANONYMISED:
        return None
    context = dict(context or {})
    _check_context(context)

    wanted = language_for(person) if person is not None else settings.LANGUAGE_CODE
    language = _template_language(template, wanted)
    subject, body_text, body_html = _render(template, language, context)

    # La tasca s'importa aquí: `tasks` importa aquest mòdul.
    from .tasks import send_email

    with transaction.atomic():
        email = OutgoingEmail.objects.create(
            template=template,
            language=language,
            to_address=to,
            person=person,
            subject=subject[:255],
            body_text=body_text,
            body_html=body_html,
        )
        send_email.defer(email_id=email.pk)
    return email


def _close(email: OutgoingEmail, status: str) -> None:
    email.status = status
    email.body_text = ""
    email.body_html = ""
    if status == OutgoingEmail.Status.SENT:
        email.sent_at = timezone.now()
    # El correu ja era a la cua quan la persona es va anonimitzar: ha sortit (RN-A14), però
    # l'adreça no es queda al registre d'enviaments (028), tampoc dins del missatge d'error.
    if email.person_id and email.person.status == Person.Status.ANONYMISED:
        email.to_address = anonymous_email(email.person.anonymous_ref)
        email.last_error = ""


def anonymise_recipient(person, addresses) -> int:
    """Treu l'adreça del destinatari dels enviaments d'una persona ja anonimitzada (028; risc
    anotat a la T-M01-10). `addresses` són les adreces que tenia: també cobreix els correus que
    hi van anar sense lligar-los a la persona (el rebut d'una alta). Els que encara esperen
    conserven l'adreça fins que surten (RN-A14) i queden lligats a la persona perquè `_close`
    la substitueixi llavors. El missatge d'error del servidor pot repetir l'adreça: també es
    buida. Torna quants enviaments ha tocat."""
    replacement = anonymous_email(person.anonymous_ref)
    loose = OutgoingEmail.objects.filter(person__isnull=True, to_address__in=list(addresses))
    queued = Q(status=OutgoingEmail.Status.QUEUED)
    loose.filter(queued).update(person=person)
    return OutgoingEmail.objects.filter(
        ~queued, Q(person=person) | Q(pk__in=loose.values("pk"))
    ).update(to_address=replacement, last_error="")


def deliver(email_id: int) -> None:
    """Envia un correu de la cua. Idempotent: si ja no espera, no fa res.

    Si el proveïdor falla, compta l'intent i aixeca `EmailDeliveryError` perquè la cua el torni
    a provar. En arribar a `EMAIL_MAX_ATTEMPTS`, el dona per fallit i no el reintenta més.
    """
    error = None
    with transaction.atomic():
        email = OutgoingEmail.objects.select_for_update().filter(pk=email_id).first()
        if email is None or email.status != OutgoingEmail.Status.QUEUED:
            return
        email.attempts += 1
        message = EmailMultiAlternatives(
            subject=email.subject,
            body=email.body_text,
            from_email=settings.EMAIL_FROM_TRANSACCIONAL,
            to=[email.to_address],
            reply_to=[settings.EMAIL_REPLY_TO],
        )
        if email.body_html:
            message.attach_alternative(email.body_html, "text/html")
        try:
            message.send()
        except Exception as exc:  # Qualsevol error del transport: es reintenta.
            error = exc
            email.last_error = f"{type(exc).__name__}: {exc}"[:255]
            if email.attempts >= settings.EMAIL_MAX_ATTEMPTS:
                _close(email, OutgoingEmail.Status.FAILED)
                error = None
        else:
            email.last_error = ""
            _close(email, OutgoingEmail.Status.SENT)
        email.save()
    # Fora de la transacció: l'intent comptat queda desat abans del reintent.
    if error is not None:
        raise EmailDeliveryError(email.last_error) from error
