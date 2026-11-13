"""Centre de cost al càrrec (T-M04-02; M04-6: «Al càrrec: `cost_centre` (FK null)»; RN-T10).

Càrrecs que ja hi eren: les quotes, que sempre són de «General» (CA-15.8), passen a «General /
Quotes de socis» (S-M04-06). La resta queda sense centre de cost: cap regla no diu quin li toca
(P-81). Reversible: desfer-la treu el camp, i amb ell el valor."""

import django.db.models.deletion
from django.db import migrations, models

GENERAL = "General"
FEES_COST_CENTRE = "Quotes de socis"


def fees_to_their_cost_centre(apps, schema_editor):
    fees = (
        apps.get_model("treasury", "CostCentre")
        .objects.filter(department__name=GENERAL, name=FEES_COST_CENTRE)
        .first()
    )
    if fees is None:  # Sense les dades inicials de la 04 no hi ha res a assignar.
        return
    apps.get_model("core", "Charge").objects.filter(
        kind="fee", department=fees.department, cost_centre__isnull=True
    ).update(cost_centre=fees)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0028_p22_exempt_fee"),
        ("treasury", "0004_initial_cost_centres"),
    ]

    operations = [
        migrations.AddField(
            model_name="charge",
            name="cost_centre",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="charges",
                to="treasury.costcentre",
                verbose_name="centre de cost",
            ),
        ),
        migrations.RunPython(fees_to_their_cost_centre, migrations.RunPython.noop),
    ]
