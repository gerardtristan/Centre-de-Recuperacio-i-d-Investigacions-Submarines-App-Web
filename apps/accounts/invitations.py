"""Invitació per crear el compte personal en aprovar una alta (T-M01-14; decisió 079, A-11;
RN-M01-87, CA-M01-90 i 91; especificació a docs/planning.md#M01-079-invitacio).

- Testimoni aleatori de 256 bits. Només se'n desa l'empremta SHA-256, la caducitat i si s'ha
  fet servir: el testimoni en clar només existeix dins del correu i no surt mai al registre.
- Un sol ús i una de viva per persona: crear-ne una de nova invalida les anteriors.
- Qui la rep (`eligible`): la persona, al seu correu de contacte, si té 14 anys o més i no té
  compte personal. Mai el representant (Q-012). Si ja té compte personal, rep un avís sense
  enllaç (`send_for_approved_join`).
- En fer-la servir es crea el compte personal **actiu** amb el correu de la persona: rebre
  l'enllaç verifica l'adreça (P-M01-A, pas 6). No s'obre cap sessió.
- La pàgina respon igual per a un enllaç desconegut, caducat, ja fet servir, d'una persona que
  ja té compte o amb un correu que ja és d'un altre compte (`invitation_for_token` torna None).
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from apps.core import audit, mail
from apps.core.models import Person
from apps.core.normalization import normalize_email
from apps.core.persons import age_on

from .forms import NewPasswordForm
from .models import Account, AccountInvitation

# 079: la mateixa caducitat que l'enllaç de verificació del correu (V-01), perquè la invitació
# fa de verificació [A confirmar: responsable].
VALIDITY = timedelta(hours=48)
MIN_AGE = 14  # per sota, cap compte personal (Q-012)
TOKEN_BYTES = 32
SESSION_KEY = "link_invitation"
INVITATION_TEMPLATE = "invitacio-compte"
NOTICE_TEMPLATE = "alta-aprovada"
CREATED = "accounts.invitation.created"
ACCEPTED = "accounts.invitation.accepted"

SENT_INVITATION = "invitation"
SENT_NOTICE = "notice"


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hours() -> int:
    return int(VALIDITY.total_seconds() // 3600)


def has_personal_account(person) -> bool:
    return Account.objects.filter(person=person, kind=Account.Kind.PERSONAL).exists()


def eligible(person, *, today=None) -> bool:
    """Pot rebre una invitació: persona activa, amb correu propi, de 14 anys o més (amb l'edat
    desconeguda no es bloqueja, RN-M01-55) i sense compte personal."""
    if person.status != Person.Status.ACTIVE or not person.contact_email:
        return False
    today = today or timezone.localdate()
    birth = person.birth_date
    if birth is not None and birth <= today and age_on(birth, today) < MIN_AGE:
        return False
    return not has_personal_account(person)


def invalidate(person) -> int:
    """Invalida les invitacions vives de la persona (també en anonimitzar-la, T-M01-22)."""
    return AccountInvitation.objects.filter(
        person=person, used_at__isnull=True, invalidated_at__isnull=True
    ).update(invalidated_at=timezone.now())


@transaction.atomic
def create(person, *, by=None, request=None) -> str:
    """Crea la invitació i torna el testimoni en clar (l'únic moment en què existeix)."""
    Person.objects.select_for_update().get(pk=person.pk)
    invalidate(person)
    token = secrets.token_urlsafe(TOKEN_BYTES)
    invitation = AccountInvitation.objects.create(
        person=person,
        token_hash=_hash(token),
        expires_at=timezone.now() + VALIDITY,
        created_by=by if isinstance(by, Account) else None,
    )
    audit.record(CREATED, actor=by, target=invitation, request=request)
    return token


def send(person, *, by=None, request=None) -> bool:
    """Crea una invitació i n'envia l'enllaç al correu de la persona. Torna si s'ha enviat."""
    if not eligible(person):
        return False
    with transaction.atomic():
        token = create(person, by=by, request=request)
        link = settings.PUBLIC_SITE_URL + reverse("accounts:invitation_link", args=[token])
        mail.queue_email(
            INVITATION_TEMPLATE,
            to=person.contact_email,
            person=person,
            context={"link": link, "hours": hours()},
        )
    return True


def send_for_approved_join(person, *, by=None, request=None) -> str | None:
    """En aprovar una alta: invitació si la persona no té compte, o un avís sense enllaç si ja en
    té. Torna què s'ha enviat (`SENT_INVITATION`, `SENT_NOTICE`) o None (menor de 14 anys o
    sense correu propi). Qui crida no ho ensenya a la pantalla (especificació, punt 8)."""
    if send(person, by=by, request=request):
        return SENT_INVITATION
    if person.contact_email and has_personal_account(person):
        login = reverse("accounts:login")
        mail.queue_email(
            NOTICE_TEMPLATE,
            to=person.contact_email,
            person=person,
            context={"link": settings.PUBLIC_SITE_URL + login},
        )
        return SENT_NOTICE
    return None


def invitation_for_token(token: str, *, lock: bool = False) -> AccountInvitation | None:
    """La invitació del testimoni, només si encara es pot fer servir."""
    invitations = AccountInvitation.objects.filter(
        token_hash=_hash(str(token or "")),
        used_at__isnull=True,
        invalidated_at__isnull=True,
        expires_at__gt=timezone.now(),
    ).select_related("person")
    if lock:
        invitations = invitations.select_for_update(of=("self",))
    invitation = invitations.first()
    if invitation is None:
        return None
    person = invitation.person
    email = normalize_email(person.contact_email)
    if (
        person.status != Person.Status.ACTIVE
        or not email
        or has_personal_account(person)
        or Account.objects.filter(login=email).exists()
    ):
        return None
    return invitation


@dataclass
class AcceptResult:
    form: NewPasswordForm | None = None
    done: bool = False


def accept(token: str, data=None, *, request=None) -> AcceptResult:
    """Sense `data`, comprova l'enllaç i torna el formulari. Amb `data`, crea el compte amb la
    invitació bloquejada: dues peticions alhora en creen un de sol."""
    with transaction.atomic():
        invitation = invitation_for_token(token, lock=data is not None)
        if invitation is None:
            return AcceptResult()
        person = invitation.person
        account = Account(
            person=person,
            kind=Account.Kind.PERSONAL,
            login=normalize_email(person.contact_email),
            status=Account.Status.ACTIVE,
        )
        form = NewPasswordForm(account, data)
        if data is None or not form.is_valid():
            return AcceptResult(form=form)
        account.set_password(form.cleaned_data["new_password1"])
        try:
            account.full_clean(exclude=["password"])
            with transaction.atomic():
                account.save()
        except (ValidationError, IntegrityError):  # el correu ha passat a ser d'un altre compte
            return AcceptResult()
        invitation.used_at = timezone.now()
        invitation.save(update_fields=["used_at"])
        audit.record(ACCEPTED, actor=account, target=account, request=request)
        return AcceptResult(done=True)
