"""L-M05a-06 (T-M05a-17b): un mandat revocat que després es bloqueja per l'esborrat de les dades
personals conserva la data i el motiu de la revocació. Tornar enrere falla si ja hi ha mandats
bloquejats amb data de revocació: és el que es vol (no es perd la història)."""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0037_payments_campaign_send_permission"),
        ("members", "0020_fee_exemption"),
        ("payments", "0008_anullacio_de_rebut"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="sepamandate",
            name="sepa_mandate_revoked_has_date_and_reason",
        ),
        migrations.AddConstraint(
            model_name="sepamandate",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("status", "revoked"),
                        ("revoked_at__isnull", False),
                        models.Q(("revoked_reason", ""), _negated=True),
                    ),
                    ("status", "blocked"),
                    models.Q(
                        models.Q(("status__in", ["revoked", "blocked"]), _negated=True),
                        ("revoked_at__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="sepa_mandate_revoked_has_date_and_reason",
            ),
        ),
    ]
