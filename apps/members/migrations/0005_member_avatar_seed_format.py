"""Format de la llavor de l'avatar: 64 caràcters hexadecimals en minúscula, com `token_hex(32)`.

Rebutja valors mal formats; no demostra que la llavor sigui aleatòria. Només afecta
`avatar_seed`: no impedeix anonimitzar cap altra dada. Desfer-la treu la restricció i no
esborra res.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("members", "0004_member_avatar_seed")]

    operations = [
        migrations.AddConstraint(
            model_name="member",
            constraint=models.CheckConstraint(
                condition=models.Q(("avatar_seed__regex", "^[0-9a-f]{64}$")),
                name="member_avatar_seed_hex64",
            ),
        ),
    ]
