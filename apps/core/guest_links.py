"""Enllaços de convidat (T-M00-02; spec 00, HU-02, RN-30 a RN-33, V-02; decisió 021).

Una persona sense compte veu (i, amb el 05b, paga) un càrrec amb un enllaç secret de durada
limitada. Aquest mòdul és l'únic que crea, substitueix i revoca enllaços.

Contracte per als altres mòduls (05b, 06 i 02):
- `create(person, obj, purpose, by=...)`: genera l'enllaç d'un càrrec pendent i l'envia al correu
  de contacte de la persona. Un enllaç nou deixa sense efecte l'anterior del mateix càrrec.
- `resend(link, by=...)` i `revoke(link, by=...)`.
- `resolve(token)`: l'enllaç d'un testimoni, només si encara funciona. No compta intents.
- `for_request(request)`: l'enllaç obert en aquest navegador, si encara funciona. És el que han
  de fer servir les vistes del convidat: l'objecte surt sempre de l'enllaç, mai d'un
  identificador de l'adreça.
- `can_pay(link)`: el càrrec encara es pot pagar (CA-02.4). `actor(link)`: l'actor «convidat»
  per al registre d'activitat (CA-14.6).

Regles:
- Testimoni aleatori de 256 bits. Només se'n desa l'empremta SHA-256 (RN-32): el testimoni en
  clar només existeix dins del correu i no va al registre d'activitat, a la sessió ni als
  registres de l'aplicació.
- Durada (V-02): 7 dies. Deixa de funcionar abans si es revoca, si se substitueix, si el càrrec
  s'anul·la o si la persona s'anonimitza. Amb el càrrec pagat continua obrint-se fins que
  caduca, només per veure'n l'estat.
- Qui el genera, el reenvia i el revoca: un compte amb M5 (`core.guest_links.manage`), o un
  mòdul que actua com a «sistema» (`audit.system(...)`), per exemple la inscripció d'un convidat.
- Intents (V-02): 10 testimonis que no funcionen des d'un mateix origen en 15 minuts → 15 minuts
  de bloqueig (`apps.accounts.limits`). Un testimoni desconegut, caducat, revocat o substituït
  compta igual i rep la mateixa resposta.
- Demanar un enllaç nou amb el correu (CA-02.6): la resposta no depèn de l'adreça. Només es
  renova l'enllaç d'un càrrec pendent que ja en tenia i que no s'ha revocat.
"""

import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts import limits
from apps.accounts.models import Account
from apps.accounts.security import client_ip

from . import audit, mail
from .models import AuditEntry, Charge, GuestLink, Person
from .normalization import normalize_email
from .permissions import has_perm

logger = logging.getLogger("cris.security")

MANAGE = "core.guest_links.manage"  # M5
PAYMENT = GuestLink.Purpose.PAYMENT
VALIDITY = timedelta(days=7)  # V-02
TOKEN_BYTES = 32  # 256 bits (V-02)
EMAIL_TEMPLATE = "enllac-convidat"
SESSION_KEY = "guest_link"
CREATED = "guest_links.created"
REVOKED = "guest_links.revoked"
ORIGIN_BLOCKED = "guest_links.origin_blocked"
REQUEST_LIMITED = "guest_links.request_limited"
# Els bloquejos i la petició d'un enllaç nou no els fa cap compte: al registre, «sistema».
LIMIT_ACTOR = audit.system("guest-link-attempt-limit")
REQUEST_ACTOR = audit.system("guest-link-request")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _ensure_can_manage(by) -> None:
    if isinstance(by, audit.Actor) and by.kind == AuditEntry.ActorKind.SYSTEM:
        return
    if not has_perm(by, MANAGE):
        raise Http404


def _usable(link: GuestLink) -> bool:
    return (
        link.is_live()
        and link.charge.status != Charge.Status.CANCELLED
        and link.person.status == Person.Status.ACTIVE
    )


def _issue(charge: Charge, *, by, request=None) -> GuestLink:
    """Dins d'una transacció, amb el càrrec bloquejat: dues peticions alhora deixen un sol
    enllaç que funciona. El testimoni en clar no surt d'aquí: només va al correu."""
    charge = (
        Charge.objects.select_for_update(of=("self",)).select_related("person").get(pk=charge.pk)
    )
    person = charge.person
    if charge.status != Charge.Status.PENDING:
        raise ValidationError(_("Només es pot enviar un enllaç d'un càrrec pendent."))
    if person.status != Person.Status.ACTIVE or not person.contact_email:
        raise ValidationError(_("La persona no té cap correu de contacte on enviar l'enllaç."))
    token = secrets.token_urlsafe(TOKEN_BYTES)
    link = GuestLink.objects.create(
        person=person,
        charge=charge,
        purpose=PAYMENT,
        token_hash=_hash(token),
        expires_at=timezone.now() + VALIDITY,
        created_by=by if isinstance(by, Account) else None,
    )
    previous = GuestLink.objects.filter(charge=charge, replaced_by__isnull=True).exclude(pk=link.pk)
    replaced = list(previous.values_list("pk", flat=True))
    previous.update(replaced_by=link)
    audit.record(
        CREATED,
        actor=by,
        target=link,
        details={"charge": charge.pk, "replaces": replaced},
        request=request,
    )
    mail.queue_email(
        EMAIL_TEMPLATE,
        to=person.contact_email,
        person=person,
        context={
            "link": settings.PUBLIC_SITE_URL + reverse("core:guest_link", args=[token]),
            "days": VALIDITY.days,
        },
    )
    return link


def create(person, obj, purpose=PAYMENT, *, by, request=None) -> GuestLink:
    """Genera l'enllaç de convidat del càrrec pendent `obj` i l'envia al correu de contacte de
    `person` (CA-02.1). Si el càrrec ja en tenia un, el nou el deixa sense efecte (CA-02.5).

    `by`: un compte amb M5 o un actor `audit.system(...)`; si no, Http404. ValidationError si
    `obj` no és un càrrec pendent de `person` o si la persona no té correu de contacte. De
    moment l'únic objecte és un càrrec i l'única finalitat, el pagament."""
    _ensure_can_manage(by)
    if not isinstance(obj, Charge) or purpose != PAYMENT:
        raise ValidationError(_("De moment només hi ha enllaços de pagament d'un càrrec."))
    if obj.person_id != person.pk:
        raise ValidationError(_("El càrrec no és d'aquesta persona."))
    with transaction.atomic():
        return _issue(obj, by=by, request=request)


def resend(link: GuestLink, *, by, request=None) -> GuestLink:
    """Reenviar (V-02, L9): un enllaç nou per al mateix càrrec; `link` deixa de funcionar."""
    return create(link.person, link.charge, link.purpose, by=by, request=request)


def revoke(link: GuestLink, *, by, request=None) -> bool:
    """Revoca l'enllaç (RN-31). Torna False si ja estava revocat o substituït. No toca el
    càrrec: un pagament ja iniciat es processa igualment si arriba confirmat (L10)."""
    _ensure_can_manage(by)
    with transaction.atomic():
        locked = GuestLink.objects.select_for_update().get(pk=link.pk)
        if locked.revoked_at is not None or locked.replaced_by_id is not None:
            return False
        locked.revoked_at = timezone.now()
        locked.save(update_fields=["revoked_at"])
        audit.record(
            REVOKED, actor=by, target=locked, details={"charge": locked.charge_id}, request=request
        )
    return True


def resolve(token: str) -> GuestLink | None:
    """L'enllaç del testimoni (amb `charge` i `person`), només si encara funciona. Un testimoni
    desconegut, caducat, revocat, substituït, d'un càrrec anul·lat o d'una persona anonimitzada
    dona None, sense distingir-los (CA-02.3). No compta intents: això ho fa `start_session`."""
    link = (
        GuestLink.objects.select_related("charge", "person")
        .filter(token_hash=_hash(str(token or "")))
        .first()
    )
    return link if link is not None and _usable(link) else None


def can_pay(link: GuestLink) -> bool:
    """El càrrec de l'enllaç encara es pot pagar: només si és pendent (CA-02.4, L8)."""
    return link.charge.status == Charge.Status.PENDING


def actor(link: GuestLink) -> audit.Actor:
    """L'actor de les accions fetes amb l'enllaç: la persona i l'identificador intern de
    l'enllaç, mai el testimoni (CA-14.6)."""
    return audit.guest(link.person, link.pk)


def start_session(request, token: str) -> bool:
    """Primera petició de l'enllaç del correu. Torna False si l'origen està bloquejat pels
    intents fallits de V-02 (CA-02.7); aleshores no es mira el testimoni. Si no, desa a la
    sessió l'identificador intern de l'enllaç quan el testimoni funciona (mai el testimoni) i
    compta un intent fallit quan no."""
    ip = client_ip(request)
    with transaction.atomic():
        if limits.guest_link_blocked(ip):
            return False
        link = resolve(token)
        request.session.pop(SESSION_KEY, None)
        if link is None:
            limits.record_guest_link_failure(ip)
            if limits.guest_link_blocked(ip):
                logger.warning("guest_link_origin_blocked ip=%s", ip)
                audit.record(ORIGIN_BLOCKED, actor=LIMIT_ACTOR, request=request)
            return True
    # Identificador de sessió nou: el que hi hagués abans de rebre l'accés ja no val.
    request.session.cycle_key()
    request.session[SESSION_KEY] = link.pk
    return True


def for_request(request) -> GuestLink | None:
    """L'enllaç obert en aquest navegador, si encara funciona (es torna a comprovar a cada
    petició: un enllaç revocat o substituït deixa de valer a l'instant)."""
    pk = request.session.get(SESSION_KEY)
    if pk is None:
        return None
    link = GuestLink.objects.select_related("charge", "person").filter(pk=pk).first()
    if link is None or not _usable(link):
        request.session.pop(SESSION_KEY, None)
        return None
    return link


def request_new(request, email: str) -> None:
    """Petició pública d'un enllaç nou amb una adreça (CA-02.6). No torna res: qui la crida
    respon sempre el mateix. Renova l'enllaç de cada càrrec pendent d'una persona amb aquest
    correu de contacte que ja en tenia un i que no s'ha revocat. Límits per origen i per
    destinatari (`limits.py`)."""
    ip = client_ip(request)
    email = normalize_email(email)
    with transaction.atomic():
        accepted = limits.start_guest_link_request(ip)
        if accepted is None:
            audit.record(
                REQUEST_LIMITED, actor=audit.ANONYMOUS, details={"scope": "origin"}, request=request
            )
            return
        current = list(
            GuestLink.objects.filter(
                replaced_by__isnull=True,
                revoked_at__isnull=True,
                charge__status=Charge.Status.PENDING,
                person__status=Person.Status.ACTIVE,
                person__contact_email=email,
            ).select_related("charge")
        )
        if not email or not current:
            return
        if not limits.guest_link_request_allowed(accepted, email):
            audit.record(
                REQUEST_LIMITED,
                actor=audit.ANONYMOUS,
                details={"scope": "recipient"},
                request=request,
            )
            return
        for link in current:
            _issue(link.charge, by=REQUEST_ACTOR, request=request)


def manageable_charges():
    """Càrrecs de la pantalla d'administració (M5), amb l'enllaç actual a `current_links` (cap o
    un): els pendents d'una persona activa sense compte personal (CA-02.1) i els que tenen un
    enllaç que encara funciona, per poder-lo revocar."""
    current = GuestLink.objects.filter(replaced_by__isnull=True)
    personal = Account.objects.filter(person=OuterRef("person"), kind=Account.Kind.PERSONAL)
    live = current.filter(
        charge=OuterRef("pk"), revoked_at__isnull=True, expires_at__gt=timezone.now()
    )
    return (
        Charge.objects.filter(person__status=Person.Status.ACTIVE)
        .exclude(status=Charge.Status.CANCELLED)
        .filter(Q(Exists(live)) | (Q(status=Charge.Status.PENDING) & ~Exists(personal)))
        .select_related("person")
        .prefetch_related(Prefetch("guest_links", queryset=current, to_attr="current_links"))
        .order_by("-created_at", "-pk")
    )
