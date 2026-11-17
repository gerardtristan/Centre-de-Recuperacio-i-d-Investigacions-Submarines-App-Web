"""Com vol pagar la quota el soci (T-M05a-11; P-M05a-A; RN-M05a-01; CA-M05a-01).

- Les opcions surten de `capabilities()` del proveïdor: sense tokenització no hi ha targeta
  guardada ([P-196](docs/decisions/pendents.md)).
- Domiciliació només amb un mandat actiu, i targeta guardada només amb una targeta activa (les
  comprovacions de la base de dades ho tornen a exigir). Sense, la pantalla porta a signar-lo o a
  guardar-la; aquí no es desa res.
- «Pagar cada vegada» amb un mandat actiu el deixa actiu (P-134, opció per defecte A).
- Signar un mandat des del compte personal passa la preferència a la domiciliació amb aquest
  mandat (P-125, decisió 095); ho fa la vista de signatura.
"""

from django.db import transaction
from django.utils import timezone

from apps.core import audit

from . import campaigns
from .models import FeeMethod, FeePaymentPreference, SavedCard, SepaMandate
from .providers import get_provider
from .providers.base import ProviderError


class PreferenceError(Exception):
    pass


class MethodNotOffered(PreferenceError):
    pass


class NeedsMandate(PreferenceError):
    pass


class NeedsSavedCard(PreferenceError):
    pass


def offered_methods() -> list[str]:
    """Les opcions que veu el soci, en ordre (P-M05a-A, pas 2)."""
    try:
        tokenization = get_provider().capabilities().tokenization
    except ProviderError:
        tokenization = False
    saved_card = [FeeMethod.SAVED_CARD] if tokenization else []
    return [FeeMethod.DIRECT_DEBIT, *saved_card, FeeMethod.PAY_EACH_TIME]


def current(member) -> FeePaymentPreference | None:
    return FeePaymentPreference.objects.filter(member=member).first()


def fee_payment_method(member) -> str | None:
    """Servei de M05a-8: `direct_debit`, `saved_card`, `pay_each_time` o `None` (sense resposta)."""
    preference = current(member)
    if preference is None:
        return None
    if (
        preference.method == FeeMethod.DIRECT_DEBIT
        and preference.mandate.status != SepaMandate.Status.ACTIVE
    ):
        return None  # un mandat caducat o bloquejat no serveix per cobrar (P-195; L-M05a-06)
    return preference.method


def active_mandate(member) -> SepaMandate | None:
    return SepaMandate.objects.filter(member=member, status=SepaMandate.Status.ACTIVE).first()


def active_card(member) -> SavedCard | None:
    cards = SavedCard.objects.filter(person=member.person, status=SavedCard.Status.ACTIVE)
    return cards.order_by("-pk").first()


@transaction.atomic
def set_preference(member, method: str, *, by) -> FeePaymentPreference:
    """Desa la preferència amb data i compte i la registra (P-M05a-A, pas 4). Si no canvia res,
    no es desa ni es registra de nou."""
    if method not in offered_methods():
        raise MethodNotOffered(method)
    mandate = active_mandate(member) if method == FeeMethod.DIRECT_DEBIT else None
    card = active_card(member) if method == FeeMethod.SAVED_CARD else None
    if method == FeeMethod.DIRECT_DEBIT and mandate is None:
        raise NeedsMandate
    if method == FeeMethod.SAVED_CARD and card is None:
        raise NeedsSavedCard
    preference = FeePaymentPreference.objects.select_for_update().filter(member=member).first()
    old = preference.method if preference else None
    if preference and (old, preference.mandate, preference.saved_card) == (method, mandate, card):
        return preference
    preference = preference or FeePaymentPreference(member=member)
    preference.method, preference.mandate, preference.saved_card = method, mandate, card
    preference.since, preference.set_by = timezone.now(), by
    preference.save()
    campaigns.record_answer(member, method)
    audit.record(
        "payments.fee_preference.set",
        actor=by,
        target=preference,
        field="method",
        old=old,
        new=method,
        details={"mandate": mandate.reference if mandate else None},
    )
    return preference
