"""T-M05b-30: els pagaments que ja havien sortit d'una decisió del tresorer (un intent «a revisar»
tancat amb «Pagat», T-M05b-16c) passen a l'origen «treasurer_decision», amb qui i el motiu del
tancament, com els nous (`reviews.close`). El pagament és el primer del càrrec de l'intent creat
a partir del tancament."""

from django.db import migrations


def fill(apps, schema_editor):
    ReviewClosure = apps.get_model("payments", "ReviewClosure")
    Payment = apps.get_model("core", "Payment")
    for closure in ReviewClosure.objects.filter(outcome="paid").select_related("attempt"):
        payment = (
            Payment.objects.filter(
                charge_id=closure.attempt.charge_id,
                origin="provider",
                created_at__gte=closure.closed_at,
            )
            .order_by("created_at", "pk")
            .first()
        )
        if payment is not None:
            Payment.objects.filter(pk=payment.pk).update(
                origin="treasurer_decision",
                recorded_by_id=closure.closed_by_id,
                reason=f"Decisió del tresorer (tancament {closure.pk})",
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0058_payment_origin"),
        ("payments", "0027_transaccio_del_proveidor"),
    ]

    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
