"""Torna a xifrar l'IBAN de cada mandat amb la clau activa (decisió 044; CA-M05a-13; checklist C13).

Primer s'afegeix la clau nova a `MANDATE_ENCRYPTION_KEYS` amb una versió més alta; després
s'executa aquesta ordre; quan acaba, cap mandat no fa servir cap altra versió i es treu la vella
de l'entorn (i se'n guarda la còpia mentre hi hagi còpies de la base de dades xifrades amb ella).

    python manage.py rota_clau_mandats
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core import audit
from apps.payments import crypto
from apps.payments.models import MandateBankAccount

ORIGIN = "payments.rota_clau_mandats"


class Command(BaseCommand):
    help = "Torna a xifrar l'IBAN de cada mandat amb la clau de versió més alta."

    def handle(self, *args, **options):
        active = crypto.active_version()
        with transaction.atomic():
            rows = MandateBankAccount.objects.select_for_update().exclude(key_version=active)
            changed = crypto.rotate(rows)
            audit.record(
                "payments.mandate_key.rotated",
                actor=audit.system(ORIGIN),
                details={"version": active, "rows": changed},
            )
        # Tot dins la mateixa transacció: si arriba aquí, cap fila no té una altra versió.
        self.stdout.write(f"Mandats tornats a xifrar amb la versió {active}: {changed}.")
        self.stdout.write("Cap mandat no fa servir cap altra versió: ja es pot treure la vella.")
