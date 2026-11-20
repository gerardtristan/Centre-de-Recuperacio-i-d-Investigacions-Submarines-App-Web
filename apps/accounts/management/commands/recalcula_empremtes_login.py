"""Recalcula l'empremta del correu d'entrada de tots els comptes personals (T-M01-39b).

L'empremta (`Account.login_hash`) depèn de SECRET_KEY: si es canvia la clau, cal executar
aquesta ordre o «He oblidat la contrasenya» deixarà de trobar els comptes. Les peticions de les
últimes 24 hores perden l'empremta antiga: es perden els límits per destinatari d'aquest temps,
com fins ara. No mostra cap adreça."""

from django.core.management.base import BaseCommand

from apps.accounts.models import Account, login_fingerprint


class Command(BaseCommand):
    help = "Recalcula l'empremta del correu d'entrada dels comptes personals."

    def handle(self, *args, **options):
        changed = 0
        for account in Account.objects.filter(kind=Account.Kind.PERSONAL).only("pk", "login"):
            fingerprint = login_fingerprint(account.login)
            changed += (
                Account.objects.filter(pk=account.pk)
                .exclude(login_hash=fingerprint)
                .update(login_hash=fingerprint)
            )
        self.stdout.write(f"Empremtes recalculades: {changed}.")
