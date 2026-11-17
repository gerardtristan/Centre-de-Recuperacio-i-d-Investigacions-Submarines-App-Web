"""T-M05b-24 (RN-M05b-27; CA-M05b-29): quants reintents té el cobrament d'una quota amb la targeta
guardada i quants dies s'espera entre un i l'altre, com a ajustos. Valors inicials de la P-304
(opció per defecte): 2 reintents, cada 3 dies [A validar: tresorer]. El permís per editar-los
encara no és al catàleg (cal una migració de `core`)."""

from django.db import migrations

SETTINGS = {
    "payments.saved_card_retries": (2, 0, 5),
    "payments.saved_card_retry_days": (3, 1, 30),
}


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, (initial, low, high) in SETTINGS.items():
        Setting.objects.get_or_create(
            key=key,
            defaults={"module": "payments", "value_type": "integer", "initial_value": initial,
                      "min_value": low, "max_value": high},
        )  # fmt: skip


def unload(apps, schema_editor):
    """Els ajustos es queden, com els de la 0004 i la 0013: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("payments", "0018_avis_targeta_notificat")]

    operations = [migrations.RunPython(load, unload)]
