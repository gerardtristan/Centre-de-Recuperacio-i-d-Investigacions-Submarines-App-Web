"""La part de la tresoreria de l'esborrat RGPD (T-M04-14c). Es registra a `apps.core.privacy` des
de `apps.py`. La 04 no guarda dades personals pròpies: l'únic text lliure que pot citar una persona
és la nota d'un tancament de liquidació «a revisar», que és al registre d'activitat."""

from django.db.models import Q

from apps.core.models import Payment

from .models import SettlementReviewClosure


def export(person) -> dict:
    return {}  # cap dada personal pròpia: els moviments no porten noms (RNF-T4)


def anonymise(person, *, by, request=None) -> None:
    """Res a anonimitzar a la 04: la nota del tancament la substitueix el registre."""


def audit_targets(person) -> dict:
    """Els tancaments de liquidacions «a revisar» que citen un cobrament de la persona: el
    registre en substitueix la nota. Límit conegut: una referència que no és de cap cobrament no
    porta a ningú, i per això l'ajuda demana no posar-hi dades personals."""
    payments = Payment.objects.filter(charge__person=person).exclude(provider_reference="")
    references = [r for r in payments.values_list("provider_reference", flat=True) if r]
    if not references:
        return {}
    cited = Q()
    for reference in references:
        cited |= Q(settlement__review_notes__contains=[{"reference": reference}])
    closures = SettlementReviewClosure.objects.filter(cited).values_list("pk", flat=True)
    return {SettlementReviewClosure._meta.label_lower: list(closures)}
