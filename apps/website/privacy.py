"""RGPD del 07 (T-M07-15; M07-8 `website.export_personal_data` i `website.anonymise`; M07-12;
CA-M07-21). Es registra a la base comuna des de `WebsiteConfig.ready`; la 00 no importa el mòdul.

Els missatges de contacte i les subscripcions al butlletí no són d'una persona de la 00 (P-492):
es troben pel correu. Les adreces d'una persona són la de contacte i la d'entrada dels seus comptes
personals, menys les que també té una altra persona activa (P-624): una adreça de família o una
bústia de rol no s'exporta ni s'esborra, i el resum de qui aprova diu quantes coses cal revisar.

- **Exportació:** els seus missatges (motiu, nom, correu, text, estat, resposta i dates) i les
  seves subscripcions (correu, estat, versió del text i dates).
- **Anonimització** (amb la persona ja anonimitzada, dins la transacció de la 00; opció
  conservadora, P-623): dels missatges, el nom passa a la referència, el correu a l'adreça
  anonimitzada i el text, la resposta i el motiu del tancament es buiden; un missatge nou es
  tanca, i la purga diària (T-M07-12) l'esborra passat el termini. Les subscripcions es donen de
  baixa i en queda només la traça (M07-12): l'estat, la versió del text i els esborrats.

La 00 buida el correu de contacte de la persona abans de cridar els mòduls: `anonymise` el rep a
`known_addresses` (el mòdul es registra amb `addresses=True`), on també hi ha els correus dels
comptes; el de notificació d'un compte d'administrador no hi compta.
"""

from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from apps.accounts.models import Account
from apps.core.models import Person
from apps.core.persons import anonymous_email

from . import newsletter
from .models import ContactMessage, NewsletterSubscription


def _own_addresses(person, known=()) -> set[str]:
    """El correu de contacte i el d'entrada dels comptes personals (únic), i les adreces que la 00
    ha pres abans de buidar la persona. Mai el de notificació d'un compte d'administrador, que pot
    ser una bústia de rol (P-624)."""
    found = {person.contact_email, *known}
    found -= set(
        person.accounts.filter(kind=Account.Kind.ADMIN).values_list("notification_email", flat=True)
    )
    found |= set(person.accounts.filter(kind=Account.Kind.PERSONAL).values_list("login", flat=True))
    return {a.strip().lower() for a in found} - {""}


def _shared(addresses: set[str], person) -> set[str]:
    """Les que també té una altra persona activa, com a correu de contacte o de compte (P-624)."""
    shared = set()
    for address in addresses:
        others = Q(contact_email__iexact=address) | Q(accounts__login__iexact=address)
        others |= Q(accounts__notification_email__iexact=address)
        if Person.objects.filter(others, status=Person.Status.ACTIVE).exclude(pk=person.pk):
            shared.add(address)
    return shared


def _addresses(person, known=()) -> set[str]:
    own = _own_addresses(person, known)
    return own - _shared(own, person)


def _matching(addresses):
    match = Q(pk__in=[])
    for address in addresses:
        match |= Q(email__iexact=address)
    return match


def _messages(person, addresses=None):
    addresses = _addresses(person) if addresses is None else addresses
    return ContactMessage.objects.filter(_matching(addresses)).select_related("reason")


def _subscriptions(person, addresses=None):
    addresses = _addresses(person) if addresses is None else addresses
    return NewsletterSubscription.objects.filter(email__in=addresses).select_related("legal_text")


def export(person) -> dict:
    return {
        "missatges_de_contacte": [
            {
                "motiu": m.reason.name,
                "nom": m.name,
                "correu": m.email,
                "missatge": m.body,
                "estat": m.get_status_display(),
                "resposta": m.answer,
                "rebut_el": m.created_at,
                "respost_o_tancat_el": m.finished_at,
            }
            for m in _messages(person).order_by("created_at", "pk")
        ],
        "butlleti": [
            {
                "correu": s.email,
                "estat": s.get_status_display(),
                "versio_del_text": s.legal_text.version,
                "demanada_el": s.requested_at,
                "confirmada_el": s.confirmed_at,
                "de_baixa_el": s.unsubscribed_at,
            }
            for s in _subscriptions(person).order_by("requested_at", "pk")
        ],
    }


def describe(person) -> list[str]:
    lines = []
    if count := _messages(person).count():
        lines.append(
            ngettext(
                "Té %(count)s missatge de contacte: se n'esborraran el nom, el correu i el text.",
                "Té %(count)s missatges de contacte: se n'esborraran el nom, el correu i el text.",
                count,
            )
            % {"count": count}
        )
    if _subscriptions(person).exclude(status=NewsletterSubscription.Status.UNSUBSCRIBED).exists():
        lines.append(_("Està subscrita al butlletí: es donarà de baixa."))
    shared = _shared(_own_addresses(person), person)
    messages, subscriptions = _messages(person, shared).count(), _subscriptions(person, shared)
    subscriptions = subscriptions.exclude(status=NewsletterSubscription.Status.UNSUBSCRIBED).count()
    if messages or subscriptions:
        lines.append(_shared_line(messages, subscriptions))
    return [str(line) for line in lines]


def _shared_line(messages: int, subscriptions: int) -> str:
    parts = []
    if messages:
        parts.append(
            ngettext("%(n)s missatge de contacte", "%(n)s missatges de contacte", messages)
            % {"n": messages}
        )
    if subscriptions:
        parts.append(
            ngettext(
                "%(n)s subscripció al butlletí", "%(n)s subscripcions al butlletí", subscriptions
            )
            % {"n": subscriptions}
        )
    return ngettext(
        "%(what)s és d'una adreça que també té una altra persona: no es tocarà; "
        "cal revisar-ho a mà.",
        "%(what)s són d'una adreça que també té una altra persona: no es tocaran; "
        "cal revisar-los a mà.",
        messages + subscriptions,
    ) % {"what": _(" i ").join(parts)}


def anonymise(person, *, by, request=None, known_addresses=()) -> None:
    ref = person.anonymous_ref
    addresses = _addresses(person, known_addresses)
    for message in _messages(person, addresses):
        message.name, message.email = ref, anonymous_email(ref)
        message.body = message.answer = ""
        if message.closed_reason or message.status == ContactMessage.Status.NEW:
            message.closed_reason = _("Esborrat RGPD de la persona.")
        if message.status == ContactMessage.Status.NEW:
            message.status = ContactMessage.Status.CLOSED
        message.finished_at = message.finished_at or timezone.now()
        message.save()
    for subscription in _subscriptions(person, addresses):
        newsletter.forget(subscription)


def audit_targets(person) -> dict:
    """Els missatges ja anonimitzats (el nom és la referència): el motiu del tancament que surt
    al registre també passa a la referència."""
    ids = [str(pk) for pk in ContactMessage.objects.filter(name=person.anonymous_ref).values_list(
        "pk", flat=True
    )]  # fmt: skip
    return {"website.contactmessage": ids} if ids else {}
