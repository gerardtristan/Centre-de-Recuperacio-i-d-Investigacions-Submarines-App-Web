# T-M01-43 (073): quota de renovació a preu de simpatitzant d'un pas acceptat.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0020_fee_exemption"),
    ]

    operations = [
        migrations.AddField(
            model_name="memberrequest",
            name="renewal_fee",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="downgrade_request",
                to="members.annualfee",
                verbose_name="quota de renovació",
            ),
        ),
    ]
