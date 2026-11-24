"""RGPD del 07 (T-M07-15; M07-8 `website.export_personal_data` i `website.anonymise`; M07-12;
CA-M07-21). Es registra a la base comuna des de `WebsiteConfig.ready`; la 00 no importa el mòdul.

Els missatges de contacte i les subscripcions al butlletí no són d'una persona de la 00 (P-492):
es troben pel correu. Les adreces d'una persona són la de contacte i les dels seus comptes.

- **Exportació:** els seus missatges (motiu, nom, correu, text, estat, resposta i dates) i les
  seves subscripcions (correu, estat, versió del text i dates).
- **Anonimització** (amb la persona ja anonimitzada, dins la transacció de la 00; opció
  conservadora, P-623): dels missatges, el nom passa a la referència, el correu a l'adreça
  anonimitzada i el text, la resposta i el motiu del tancament es buiden; un missatge nou es
  tanca, i la purga diària (T-M07-12) l'esborra passat el termini. Les subscripcions es donen de
  baixa i en queda només la traça (M07-12): l'estat, la versió del text i els esborrats.

La 00 buida el correu de contacte de la persona abans de cridar els mòduls: `remember_email` el
desa a la mateixa instància just abans (torn del nucli: passar les adreces als mòduls; vegeu
`docs/estat/M07.md`).
"""

from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from apps.accounts import privacy as accounts_privacy
from apps.core.models import Person
from apps.core.persons import anonymous_email

from . import newsletter
from .models import ContactMessage, NewsletterSubscription

_ERASED_EMAIL = "_website_erased_email"


def remember_email(sender, instance, **kwargs):
    """`pre_save` de la persona: en passar a anonimitzada, el correu de contacte que tenia."""
    if instance.pk and instance.status == Person.Status.ANONYMISED:
        old = (
            Person.objects.filter(pk=instance.pk, status=Person.Status.ACTIVE)
            .values_list("contact_email", flat=True)
            .first()
        )
        if old:
            setattr(instance, _ERASED_EMAIL, old)


def _addresses(person) -> set[str]:
    found = {person.contact_email, getattr(person, _ERASED_EMAIL, "")}
    return {a.strip().lower() for a in found | accounts_privacy.addresses(person)} - {""}


def _messages(person):
    match = Q(pk__in=[])
    for address in _addresses(person):
        match |= Q(email__iexact=address)
    return ContactMessage.objects.filter(match).select_related("reason")


def _subscriptions(person):
    return NewsletterSubscription.objects.filter(email__in=_addresses(person)).select_related(
        "legal_text"
    )


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
    return [str(line) for line in lines]


def anonymise(person, *, by, request=None) -> None:
    ref = person.anonymous_ref
    for message in _messages(person):
        message.name, message.email = ref, anonymous_email(ref)
        message.body = message.answer = ""
        if message.closed_reason or message.status == ContactMessage.Status.NEW:
            message.closed_reason = _("Esborrat RGPD de la persona.")
        if message.status == ContactMessage.Status.NEW:
            message.status = ContactMessage.Status.CLOSED
        message.finished_at = message.finished_at or timezone.now()
        message.save()
    for subscription in _subscriptions(person):
        newsletter.forget(subscription)


def audit_targets(person) -> dict:
    """Els missatges ja anonimitzats (el nom és la referència): el motiu del tancament que surt
    al registre també passa a la referència."""
    ids = [str(pk) for pk in ContactMessage.objects.filter(name=person.anonymous_ref).values_list(
        "pk", flat=True
    )]  # fmt: skip
    return {"website.contactmessage": ids} if ids else {}
