"""Correu de la plataforma (spec 00, annex A; decisions 004, 012, 019, 042 i 061).

Tots els mòduls envien correus amb `queue_email`; cap no parla amb el proveïdor. El transport
és el `EMAIL_BACKEND` de Django configurat per entorn (SMTP a producció): canviar de Brevo a
Scaleway Transactional Email, o a qualsevol altre, és canviar la configuració.

- Els correus que el club pot editar (T-M00-08) no tenen plantilla: els genera `texts`.
- Plantilles pròpies a `templates/emails/`, una per llengua: `<nom>.<llengua>.subject.txt`,
  `<nom>.<llengua>.txt` i, opcional, `<nom>.<llengua>.html`. Es tria la llengua de
  `persons.language_for(persona)` i, si no hi ha la plantilla, la catalana (061, punt 7).
- Cada plantilla declara la seva prioritat a `TEMPLATE_PRIORITIES` (RN-A8, V-07). Sense
  prioritat declarada, `queue_email` la rebutja.
- El correu es genera en posar-lo a la cua, dins de `translation.override`: la cua no té cap
  petició ni cap `Accept-Language`. El missatge guarda la llengua amb què s'ha generat.
- L'enviament el fa la cua de tasques (RN-A13) dins la mateixa transacció: si l'acció es desfà,
  no queda ni el correu ni la tasca.
- Mai contrasenyes ni adjunts (RN-A12). Res d'això va al registre d'activitat.
- Les persones anonimitzades no reben correus (RN-A14). Es comprova en posar-lo a la cua: un
  correu posat abans d'anonimitzar (la confirmació d'un esborrat RGPD) surt igualment.
- En anonimitzar una persona (T-M01-22), l'adreça dels seus enviaments se substitueix
  (`anonymise_recipient`); la dels que encara esperen, quan es tanquen (`_close`).

Límit diari (T-M00-06; RN-A3, RN-A4 i RN-A6; V-07). El dia és el de l'hora local.
- Compta en enviar, no en posar a la cua: el primer intent d'un correu gasta un enviament del
  dia (`EmailDailyUsage`, amb la fila bloquejada) i els reintents no en gasten cap altre
  (CA-A9). Un intent que falla el gasta igualment: el comptador mai no queda per sota del que
  ha pogut rebre el proveïdor.
- Amb el límit ple (`EMAIL_DAILY_LIMIT`), el correu queda «ajornat» (CA-A4). Torna a la cua
  quan hi ha lloc, que és l'endemà, per l'ordre de V-07 i abans que cap correu nou (CA-A5): ho
  fan `release_deferred`, que la cua crida cada hora, i el primer enviament del dia.
- El butlletí només pot gastar el límit menys `EMAIL_TRANSACTIONAL_RESERVE` (RN-A4).
- Un sol avís al dia en arribar al `EMAIL_ALERT_THRESHOLD_PCT` del límit (CA-A3): una entrada
  al registre d'activitat i un correu a `EMAIL_ALERT_TO`, l'adreça de l'administrador (Q-26,
  decisió 081). Si és buida, l'avís no és operatiu i `check --deploy` ho marca (`core.W001`).

Fora d'abast ara: tandes i consentiment del butlletí i avisos del proveïdor (RN-A5, RN-A9 i
RN-A10); s'hi afegeixen quan calguin.
"""

import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.template import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string
from django.utils import timezone, translation

from . import audit, texts
from .models import EmailDailyUsage, OutgoingEmail, Person
from .persons import anonymous_email, language_for

_TEMPLATE_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
# RN-A12: res que sembli una contrasenya o un secret entra al context d'una plantilla. Els
# enllaços d'un sol ús sí que hi poden anar (verificació, recuperació, convidat).
_FORBIDDEN_CONTEXT_PARTS = ("password", "contrasenya", "secret", "totp", "recovery_code")

ALERT_TEMPLATE = "avis-limit-correu"
_Priority = OutgoingEmail.Priority
# RN-A8: la prioritat de cada plantilla de `templates/emails/`, en un sol lloc. És l'ordre en
# què surten els correus ajornats (V-07). Una plantilla nova s'hi afegeix abans de fer-la
# servir: una prova compara aquesta llista amb la carpeta.
TEMPLATE_PRIORITIES = {
    # Recuperació i verificació de comptes (porten l'enllaç que deixa entrar).
    "recuperacio-contrasenya": _Priority.ACCOUNT,
    "verificacio-correu": _Priority.ACCOUNT,
    "canvi-correu": _Priority.ACCOUNT,
    "invitacio-compte": _Priority.ACCOUNT,  # fa de verificació (079, A-11)
    # Enllaços de convidat (T-M00-02; V-07, segona posició).
    "enllac-convidat": _Priority.GUEST_LINK,
    # Confirmacions i avisos d'una cosa que ja ha passat.
    "alta-aprovada": _Priority.CONFIRMATION,
    "alta-rebutjada": _Priority.CONFIRMATION,
    "baixa-efectiva": _Priority.CONFIRMATION,
    "rebut-sollicitud-alta": _Priority.CONFIRMATION,
    "avis-canvi-correu": _Priority.CONFIRMATION,
    "restabliment-acces": _Priority.CONFIRMATION,
    "avis-canvi-diners": _Priority.CONFIRMATION,
    "avis-canvi-metodes-pagament": _Priority.CONFIRMATION,
    "avis-quota-tresorer": _Priority.CONFIRMATION,
    "pagament-confirmat": _Priority.CONFIRMATION,  # CA-M05b-03 (T-M05b-07; P-84)
    "mandat-signat": _Priority.CONFIRMATION,  # G3, CA-M05a-04 (T-M05a-09)
    "mandat-caducat": _Priority.CONFIRMATION,  # RN-M05a-08 (T-M05a-09)
    "mandat-revocat": _Priority.CONFIRMATION,  # P-M05a-C (T-M05a-10)
    "avis-mandat-revocat-remesa": _Priority.CONFIRMATION,  # RN-M05a-09, al tresorer (T-M05a-10b)
    "avis-previ-remesa": _Priority.CONFIRMATION,  # RN-M05b-11, CA-M05b-14 (T-M05b-09)
    "alternativa-pagament": _Priority.CONFIRMATION,  # P-M05b-F, CA-M05b-19 i 20 (T-M05b-12)
    "avis-pagament-revisar": _Priority.CONFIRMATION,  # CA-M05b-05 (T-M05b-07; P-84)
    "quota-targeta-revisar": _Priority.CONFIRMATION,  # T-M05b-15b, al tresorer
    "avis-despesa-sense-factura": _Priority.CONFIRMATION,  # CA-M09-01, al tresorer (T-M09-04b)
    "avis-salt-serie-factures": _Priority.CONFIRMATION,  # CA-M09-17, al tresorer (T-M09-19)
    "avis-marge-baix": _Priority.CONFIRMATION,  # CA-M09-12, al responsable i al tresorer (T-M09-13)
    "avis-reobertura-periode": _Priority.CONFIRMATION,  # S-M09-13, al tresorer i a la junta
    "avis-ajut-paquet": _Priority.CONFIRMATION,  # RN-M09A-11 i 18, al responsable i al tresorer
    "avis-document-illegible": _Priority.CONFIRMATION,  # CA-M09-28, a qui el va pujar (T-M09-25b)
    "avis-missatge-contacte": _Priority.CONFIRMATION,  # RN-M07-07, CA-M07-11 (T-M07-13b)
    "resposta-contacte": _Priority.CONFIRMATION,  # P-M07-D, al visitant (T-M07-13b)
    "confirmacio-butlleti": _Priority.CONFIRMATION,  # P-M07-E, CA-M07-06 (T-M07-13b)
    "confirmacio-inscripcio": _Priority.CONFIRMATION,  # RN-M02-19 (T-M02-21b)
    "termini-pagament": _Priority.CONFIRMATION,  # RN-M02-08 i 19 (T-M02-21b)
    "oferta-placa": _Priority.CONFIRMATION,  # RN-M02-09 i 19 (T-M02-21b)
    "cancellacio-inscripcio": _Priority.CONFIRMATION,  # RN-M02-12, 13 i 19 (T-M02-21b)
    "canvi-programa": _Priority.CONFIRMATION,  # RN-M02-18, CA-M02-20 (T-M02-21b)
    "missatge-activitat": _Priority.CONFIRMATION,  # AC15, als inscrits (T-M02-21b)
    "resultat-curs": _Priority.CONFIRMATION,  # P-M02-F pas 5, a l'alumne (T-M02-21)
    "certificat-emes": _Priority.CONFIRMATION,  # P-M02-F pas 6, RN-M02-16 (T-M02-21)
    "reforc-confirmat": _Priority.CONFIRMATION,  # P-M02-F pas 4, dates i preu (T-M02-21)
    "avis-llicencia-pagada": _Priority.CONFIRMATION,  # CA-M06-07, a la secretaria (T-M06-05)
    "avis-devolucio-llicencia": _Priority.CONFIRMATION,  # CA-M06-13, al tresorer (T-M06-12)
    "avis-llicencia-no-tramitada": _Priority.CONFIRMATION,  # CA-M06-23, a qui tramita (T-M06-19)
    "avis-liquidacio-rebutjada": _Priority.CONFIRMATION,  # P-227 (095; T-M05b-14)
    "avis-compte-emergencia": _Priority.CONFIRMATION,  # CA-10.2 (T-M00-03)
    "avis-canvi-rol": _Priority.CONFIRMATION,  # RN-RP-09 (T-RP-02)
    "avis-canvi-permisos": _Priority.CONFIRMATION,  # RN-RP-09 (T-RP-03)
    "avis-desactivacio-admin": _Priority.CONFIRMATION,  # RN-RP-20 (T-RP-02d)
    "restabliment-doble-factor": _Priority.CONFIRMATION,  # P-52 (081, punt 24; T-M01-51)
    "esborrat-fet": _Priority.CONFIRMATION,  # RGPD (T-M01-22)
    "esborrat-rebutjat": _Priority.CONFIRMATION,
    ALERT_TEMPLATE: _Priority.CONFIRMATION,
    # Recordatoris.
    "recordatori-quota": _Priority.REMINDER,
    "avis-renovacio": _Priority.REMINDER,  # 073, CA-M01-70 (T-M01-43)
    "campanya-mandats-invitacio": _Priority.REMINDER,  # P-M05a-E, pas 3 (T-M05a-13)
    "campanya-mandats-recordatori": _Priority.REMINDER,  # RN-M05a-14 (T-M05a-13)
    "campanya-mandats-darrer-recordatori": _Priority.REMINDER,  # RN-M05a-14 (T-M05a-13c)
    "recordatori-transferencia": _Priority.REMINDER,  # RN-M05b-09 (T-M05b-22c)
    "recordatori-activitat": _Priority.REMINDER,  # RN-M02-19, VC-23 (T-M02-21)
    "avis-revisio-material": _Priority.REMINDER,  # RN-M03-15, CA-M03-11 (T-M03-14)
    "avis-venciment-llicencia": _Priority.REMINDER,  # RN-M06-12, al titular (T-M06-11)
    "resum-venciments-llicencies": _Priority.REMINDER,  # RN-M06-12, a qui tramita (T-M06-11)
    "avis-ajut-tancament": _Priority.REMINDER,  # RN-M09A-04, CA-M09A-01 (T-M09A-06)
    "avis-ajut-resposta": _Priority.REMINDER,  # RN-M09A-05, CA-M09A-03 (T-M09A-06)
    "avis-ajut-justificacio": _Priority.REMINDER,  # RN-M09A-04 i 20, S-M09A-04 (T-M09A-06)
    "avis-ajut-requeriment": _Priority.REMINDER,  # RN-M09A-19, CA-M09A-17 i 18 (T-M09A-15)
    "prova": _Priority.REMINDER,  # correu de prova de l'ordre `send_test_email`
    # Butlletí: la prioritat més baixa, dins del comptador i sense la reserva dels transaccionals.
    "butlleti": _Priority.NEWSLETTER,  # RN-M07-06, CA-M07-08 (T-M07-14b)
}


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
    if template not in TEMPLATE_PRIORITIES:
        raise ValueError(
            f"La plantilla «{template}» no té prioritat declarada a TEMPLATE_PRIORITIES (RN-A8)."
        )
    if person is not None and person.status == Person.Status.ANONYMISED:
        return None
    context = dict(context or {})
    _check_context(context)

    wanted = language_for(person) if person is not None else settings.LANGUAGE_CODE
    if template in texts.TEMPLATES:  # correu editable (T-M00-08): text pla, sense plantilla
        subject, body_text, language = texts.render_email(template, context, wanted)
        body_html = ""
    else:
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
            priority=TEMPLATE_PRIORITIES[template],
            subject=subject[:255],
            body_text=body_text,
            body_html=body_html,
        )
        send_email.defer(email_id=email.pk)
    return email


# --- Límit diari ----------------------------------------------------------------------------


def _lock_usage(day) -> EmailDailyUsage:
    """Dins d'una transacció: el comptador del dia, bloquejat fins que s'acaba. Tot el que
    compta, ajorna o avisa passa amb aquesta fila bloquejada, d'un en un."""
    EmailDailyUsage.objects.get_or_create(day=day)
    return EmailDailyUsage.objects.select_for_update().get(day=day)


def _take_slot(usage: EmailDailyUsage, priority: int) -> bool:
    """Gasta un enviament del dia, si en queda. El butlletí no pot gastar la reserva dels
    transaccionals (RN-A4)."""
    limit = settings.EMAIL_DAILY_LIMIT
    if usage.used >= limit:
        return False
    if priority == _Priority.NEWSLETTER:
        if usage.newsletter >= limit - settings.EMAIL_TRANSACTIONAL_RESERVE:
            return False
        usage.newsletter += 1
    usage.used += 1
    return True


def _release(usage: EmailDailyUsage) -> int:
    """Els correus ajornats que caben al dia tornen a la cua, per l'ordre de V-07 (CA-A5)."""
    from .tasks import send_email

    room = max(settings.EMAIL_DAILY_LIMIT - usage.used, 0)
    deferred = (
        OutgoingEmail.objects.select_for_update()
        .filter(status=OutgoingEmail.Status.DEFERRED)
        .order_by("priority", "created_at", "pk")
    )
    released = 0
    for email in deferred[:room]:
        # El primer que no hi cap atura la resta: els que venen darrere tenen menys prioritat.
        if not _take_slot(usage, email.priority):
            break
        email.status = OutgoingEmail.Status.QUEUED
        email.counted_on = usage.day
        email.save(update_fields=["status", "counted_on"])
        send_email.defer(email_id=email.pk)
        released += 1
    return released


def _save_usage(usage: EmailDailyUsage) -> None:
    """Desa el comptador i, la primera vegada del dia que arriba al llindar, avisa (RN-A6).

    Qui rep l'avís (Q-26, resolta a la decisió 081, punt 21): **només l'administrador**, a
    l'adreça configurada a `EMAIL_ALERT_TO`. Sempre queda al registre d'activitat, amb el nombre
    de destinataris; si no n'hi ha cap («recipients»: 0), l'avís no és operatiu (la
    comprovació de desplegament `core.W001` ho marca). Cap dada personal ni al registre ni al
    correu: només el dia i els números.
    """
    limit = settings.EMAIL_DAILY_LIMIT
    reached = usage.used * 100 >= limit * settings.EMAIL_ALERT_THRESHOLD_PCT
    if usage.used and reached and usage.warned_at is None:
        usage.warned_at = timezone.now()
        audit.record(
            audit.Action.EMAIL_LIMIT_ALERT,
            actor=audit.system("core.mail"),
            target=usage,
            details={
                "day": usage.day.isoformat(),
                "used": usage.used,
                "limit": limit,
                "recipients": len(settings.EMAIL_ALERT_TO),
            },
        )
        for address in settings.EMAIL_ALERT_TO:
            queue_email(
                ALERT_TEMPLATE,
                to=address,
                context={"day": usage.day, "used": usage.used, "limit": limit},
            )
    usage.save()


def release_deferred(today=None) -> int:
    """Torna a la cua els correus ajornats que caben al comptador d'avui i en torna el nombre
    (CA-A4, CA-A5). Idempotent: mentre el límit és ple no en surt cap, i el que no hi cap un
    dia espera el següent."""
    with transaction.atomic():
        usage = _lock_usage(today or timezone.localdate())
        released = _release(usage)
        _save_usage(usage)
    return released


def _admit(email_id: int, today) -> bool:
    """Diu si el correu es pot enviar ara. El primer intent gasta un enviament del dia o, amb
    el límit ple, deixa el correu ajornat (CA-A4); un reintent ja té el seu (CA-A9)."""
    with transaction.atomic():
        email = OutgoingEmail.objects.select_for_update().filter(pk=email_id).first()
        if email is None or email.status != OutgoingEmail.Status.QUEUED:
            return False
        if email.counted_on is not None:
            return True
        usage = _lock_usage(today or timezone.localdate())
        # V-07: els ajornats «surten primer»; passen al davant de qualsevol correu nou.
        _release(usage)
        admitted = _take_slot(usage, email.priority)
        if admitted:
            email.counted_on = usage.day
        else:
            email.status = OutgoingEmail.Status.DEFERRED
        email.save(update_fields=["status", "counted_on"])
        _save_usage(usage)
    return admitted


# --- Enviament ------------------------------------------------------------------------------


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
    # Els ajornats pel límit diari (T-M00-06) encara han de sortir: com els de la cua.
    queued = Q(status__in=[OutgoingEmail.Status.QUEUED, OutgoingEmail.Status.DEFERRED])
    loose.filter(queued).update(person=person)
    return OutgoingEmail.objects.filter(
        ~queued, Q(person=person) | Q(pk__in=loose.values("pk"))
    ).update(to_address=replacement, last_error="")


def deliver(email_id: int, *, today=None) -> None:
    """Envia un correu de la cua. Idempotent: si ja no espera, no fa res. Amb el límit diari
    ple, el deixa ajornat i no l'envia.

    Si el proveïdor falla, compta l'intent i aixeca `EmailDeliveryError` perquè la cua el torni
    a provar. En arribar a `EMAIL_MAX_ATTEMPTS`, el dona per fallit i no el reintenta més.
    """
    # En una transacció pròpia i curta: el comptador no queda bloquejat mentre dura l'enviament.
    if not _admit(email_id, today):
        return
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
