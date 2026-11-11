"""Revoca i reemet tots els carnets vigents emesos amb una clau del QR (T-M01-19; decisió 079,
RN-M01-85; especificació del QR, punt 7).

Per a quan una clau s'ha filtrat o es retira: primer s'afegeix la clau nova a `CARD_QR_KEYS` i es
posa com a activa (`CARD_QR_ACTIVE_KEY`); després s'executa aquesta ordre amb l'identificador de
la clau vella, i finalment la clau vella es treu de la configuració. Cada carnet es revoca amb el
motiu i se n'emet un de nou amb la clau activa; tot queda al registre d'activitat, amb el sistema
com a autor. Els socis que ja no poden tenir carnet es queden amb el carnet revocat.

    python manage.py reemet_carnets --clau k1 --motiu "Rotació de la clau k1"
    python manage.py reemet_carnets --sense-clau --motiu "Carnets anteriors al QR calculat"
"""

from django.core.management.base import BaseCommand, CommandError

from apps.core import audit
from apps.members import card_keys, cards

ORIGIN = "members.reemet_carnets"


class Command(BaseCommand):
    help = "Revoca i reemet els carnets vigents d'una clau del QR, amb la clau activa."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--clau", help="Identificador de la clau dels carnets que es reemeten.")
        group.add_argument(
            "--sense-clau",
            action="store_true",
            help="Els carnets anteriors al QR calculat (sense identificador de clau).",
        )
        parser.add_argument("--motiu", required=True, help="Motiu, per al registre d'activitat.")

    def handle(self, *args, clau, sense_clau, motiu, **options):
        key_id = "" if sense_clau else clau
        if not motiu.strip():
            raise CommandError("Cal un motiu.")
        if key_id == card_keys.active_key_id():
            raise CommandError(
                "Aquesta és la clau activa: els carnets nous tornarien a sortir amb la mateixa "
                "clau. Posa primer una altra clau com a activa."
            )
        count = cards.reissue_for_key(key_id, by=audit.system(ORIGIN), reason=motiu.strip())
        self.stdout.write(f"Carnets reemesos: {count}.")
