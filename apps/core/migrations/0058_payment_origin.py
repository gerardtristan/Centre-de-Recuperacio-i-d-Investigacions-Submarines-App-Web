"""T-M05b-30: l'origen del pagament, al pagament mateix. Fins ara només constava al registre
d'activitat del càrrec («charges.status_changed», detall `origin`). Els que ja hi ha: «manual»
els del mètode manual i «reconciliation» els que el registre diu que van entrar per una
conciliació; la resta, «provider». Les decisions del tresorer les marca `payments/0028`."""

from django.conf import settings
from django.db import migrations, models


def fill(apps, schema_editor):
    Payment = apps.get_model("core", "Payment")
    AuditEntry = apps.get_model("core", "AuditEntry")
    Payment.objects.filter(method="manual").update(origin="manual")
    reconciled = AuditEntry.objects.filter(
        action="charges.status_changed", details__origin="reconciliation"
    ).values_list("details__payment", flat=True)
    Payment.objects.filter(pk__in=[pk for pk in reconciled if pk]).update(origin="reconciliation")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0057_renewal_notice_months_permission"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="origin",
            field=models.CharField(
                choices=[
                    ("provider", "Proveïdor"),
                    ("reconciliation", "Conciliació"),
                    ("manual", "Registrat a mà"),
                    ("treasurer_decision", "Decisió del tresorer"),
                ],
                default="provider",
                max_length=20,
                verbose_name="origen",
            ),
        ),
        migrations.RunPython(fill, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("origin__in", ["provider", "reconciliation", "manual", "treasurer_decision"])
                ),
                name="payment_origin_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("method", "manual"), ("origin", "manual")),
                    models.Q(
                        models.Q(("method", "manual"), _negated=True),
                        models.Q(("origin", "manual"), _negated=True),
                    ),
                    _connector="OR",
                ),
                name="payment_manual_method_and_origin",
            ),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("origin__in", ["manual", "treasurer_decision"]), _negated=True),
                    models.Q(
                        ("recorded_by__isnull", False), models.Q(("reason", ""), _negated=True)
                    ),
                    _connector="OR",
                ),
                name="payment_person_origin_has_who_and_why",
            ),
        ),
    ]
