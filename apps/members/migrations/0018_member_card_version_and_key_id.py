"""QR del carnet calculat amb una clau del servidor (T-M01-19; decisió 079, RN-M01-85):
`version` (un número per soci que puja a cada emissió) i `key_id` (amb quina clau s'ha calculat).

Els carnets que ja existeixen es numeren per soci en l'ordre en què es van emetre i queden
sense `key_id`: es continuen verificant per l'empremta, però el seu QR no es pot tornar a
mostrar fins que el soci en demani un de nou.

Desfer-la treu les dues columnes i les restriccions.
"""

from django.db import migrations, models


def number_existing_cards(apps, schema_editor):
    MemberCard = apps.get_model("members", "MemberCard")
    last_member, version = None, 0
    for card in MemberCard.objects.order_by("member_id", "issued_at", "id"):
        version = version + 1 if card.member_id == last_member else 1
        last_member = card.member_id
        if card.version != version:
            MemberCard.objects.filter(pk=card.pk).update(version=version)


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0017_member_request_guardian_contact"),
    ]

    operations = [
        migrations.AddField(
            model_name="membercard",
            name="key_id",
            field=models.CharField(
                blank=True, default="", max_length=8, verbose_name="identificador de la clau"
            ),
        ),
        migrations.AddField(
            model_name="membercard",
            name="version",
            field=models.PositiveIntegerField(default=1, verbose_name="versió"),
        ),
        migrations.RunPython(number_existing_cards, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="membercard",
            constraint=models.UniqueConstraint(
                fields=("member", "version"), name="membercard_unique_version_per_member"
            ),
        ),
        migrations.AddConstraint(
            model_name="membercard",
            constraint=models.CheckConstraint(
                condition=models.Q(("version__gte", 1), ("key_id__regex", "^[a-z0-9]{0,8}$")),
                name="membercard_version_and_key_id_valid",
            ),
        ),
    ]
