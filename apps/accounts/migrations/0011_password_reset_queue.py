"""T-M01-39b (072, Q-084 i Q-085): «He oblidat la contrasenya» amb una cua. L'empremta del
correu d'entrada dels comptes personals (`Account.login_hash`), l'estat de la petició i la IP
que es pot buidar. Les empremtes dels comptes que ja hi ha es calculen aquí, amb la mateixa
fórmula que `login_fingerprint` (no s'importa el model: ha de valer encara que canviï)."""

from django.db import migrations, models
from django.utils.crypto import salted_hmac


def _fingerprint(login):
    normalized = (login or "").strip().lower()  # `normalize_email`
    return salted_hmac("apps.accounts.limits.recipient", normalized, algorithm="sha256").hexdigest()


def fill(apps, schema_editor):
    Account = apps.get_model("accounts", "Account")
    for account in Account.objects.filter(kind="personal").only("pk", "login"):
        Account.objects.filter(pk=account.pk).update(login_hash=_fingerprint(account.login))


class Migration(migrations.Migration):
    # Després de la core/0056 (ordre de les migracions de nucli del 20/11/2026).
    dependencies = [
        ("accounts", "0010_guest_link_purposes"),
        ("core", "0056_erasure_in_person"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="login_hash",
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=64),
        ),
        migrations.AddField(
            model_name="emaillinkrequest",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Sense estat"),
                    ("pending", "Pendent"),
                    ("sent", "Enviada"),
                    ("not_sent", "No enviada"),
                    ("limited", "Limitada per destinatari"),
                    ("expired", "Caducada"),
                ],
                default="",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="emaillinkrequest",
            name="ip_address",
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.RunPython(fill, migrations.RunPython.noop),
    ]
