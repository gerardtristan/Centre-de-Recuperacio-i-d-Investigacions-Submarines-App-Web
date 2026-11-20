"""La part dels pagaments de l'esborrat RGPD i de l'exportació (L-M05a-06; decisions 044, 028 i
058). Es registra a `apps.core.privacy` des de `apps.py`: ni el nucli ni el M01 importen els
pagaments.

- **Esborrat:** els mandats de la persona passen a «bloquejat», amb una entrada al registre per a
  cadascun. No s'esborra res: el mandat i l'IBAN xifrat es conserven fins al final del termini
  (044). Un mandat bloquejat no es fa servir, no es revoca ni es reactiva (cap servei no treballa
  amb mandats que no siguin actius).
- **Exportació:** els mandats amb l'IBAN emmascarat i el mètode de la quota; mai l'IBAN sencer.
"""

from django.db import transaction
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.models import AuditEntry, Charge

from . import processing
from .models import FeePaymentPreference, ReviewClosure, SepaMandate

REASON = "esborrat de dades personals (L-M05a-06)"


def _mandates(person):
    return SepaMandate.objects.filter(member__person=person).order_by("signed_at", "pk")


def export(person) -> dict:
    preference = FeePaymentPreference.objects.filter(member__person=person).first()
    return {
        "metode_quota": preference.get_method_display() if preference else None,
        "mandats": [
            {
                "referencia": mandate.reference,
                "estat": mandate.get_status_display(),
                "titular": mandate.holder_name,
                "compte": str(mandate.bank_account),  # «ES … 1234»
                "signat_el": mandate.signed_at,
                "revocat_el": mandate.revoked_at,
            }
            for mandate in _mandates(person).select_related("bank_account")
        ],
    }


@transaction.atomic
def anonymise(person, *, by, request=None) -> None:
    for mandate in _mandates(person).select_for_update().exclude(status=SepaMandate.Status.BLOCKED):
        old = mandate.status
        mandate.status = SepaMandate.Status.BLOCKED
        mandate.save(update_fields=["status"])
        audit.record(
            "payments.mandate.blocked",
            actor=by,
            target=mandate,
            field="status",
            old=old,
            new=SepaMandate.Status.BLOCKED,
            reason=REASON,
            details={"reference": mandate.reference},
            request=request,
        )


def audit_targets(person) -> dict:
    """Els tancaments d'«a revisar» dels seus càrrecs (T-M05b-16b i P-406): la nota és text
    lliure. Els mandats no: es bloquegen, no s'anonimitzen, i les seves entrades només porten la
    referència."""
    closures = ReviewClosure.objects.filter(attempt__charge__person=person)
    # P-406: els tancaments dels càrrecs «a revisar» sense intent són sobre l'entrada que tanquen.
    reviews = AuditEntry.objects.filter(
        action=processing.TO_REVIEW,
        target_type=Charge._meta.label_lower,
        target_id__in=[str(pk) for pk in person.charges.values_list("pk", flat=True)],
    )
    return {
        ReviewClosure._meta.label_lower: list(closures.values_list("pk", flat=True)),
        AuditEntry._meta.label_lower: list(reviews.values_list("pk", flat=True)),
    }


def describe(person) -> list[str]:
    if _mandates(person).exclude(status=SepaMandate.Status.BLOCKED).exists():
        return [_("Els mandats de domiciliació es bloquegen: no es fan servir ni s'esborren.")]
    return []
