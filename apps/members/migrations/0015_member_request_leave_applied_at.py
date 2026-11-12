# T-M01-17 (074, RN-M01-74): marca d'aplicada de les baixes. Les baixes ja validades abans
# d'aquesta migració s'aplicaven en validar-les: reben la mateixa hora que la resolució.

from django.db import migrations, models
from django.db.models import F


def mark_existing_leaves_applied(apps, schema_editor):
    MemberRequest = apps.get_model("members", "MemberRequest")
    MemberRequest.objects.filter(kind="leave", status="approved").update(
        applied_at=F("resolved_at")
    )


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0014_imported_without_join_date_and_history_origin"),
    ]

    operations = [
        migrations.AddField(
            model_name="memberrequest",
            name="applied_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="baixa aplicada el"),
        ),
        migrations.RunPython(mark_existing_leaves_applied, migrations.RunPython.noop),
    ]
