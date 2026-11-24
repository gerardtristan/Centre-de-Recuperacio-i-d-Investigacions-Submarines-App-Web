"""T-M08-10 (M08-6, «Valors configurables»): els ajustos del 08 que falten.
- `dashboard.low_occupancy_pct`: 50 d'inici (S-M08-02, [A validar: responsable de cursos i
  sortides]), de 0 a 100 (RN-M08-07; CA-M08-07).
- `dashboard.default_period`: el període per defecte del dashboard (RN-M08-08), l'any natural.
- `dashboard.help_text.low_occupancy`: el text d'ajuda de l'indicador nou de l'avís
  d'ocupació baixa (els altres, a la 0001). `dashboard.min_group_size` és a la 0002. L'apartat el
pot editar l'administrador (`settings.section.dashboard` «Sí», T-M07-02); el permís propi perquè
el responsable de cursos i sortides canviï l'ocupació baixa és del catàleg del nucli (P-645)."""

from django.db import migrations

PERIODS = ["month", "quarter", "year", "last_12_months"]
CODES = ["low_occupancy"]  # indicadors nous: el seu text d'ajuda buit, com a la 0001
SETTINGS = {
    "dashboard.low_occupancy_pct": {
        "value_type": "integer",
        "initial_value": 50,
        "min_value": 0,
        "max_value": 100,
    },
    "dashboard.default_period": {"value_type": "choice", "initial_value": "year", "choices": PERIODS},
}


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, fields in SETTINGS.items():
        Setting.objects.get_or_create(key=key, defaults={"module": "dashboard", **fields})
    for code in CODES:
        Setting.objects.get_or_create(
            key=f"dashboard.help_text.{code}",
            defaults={"module": "dashboard", "value_type": "text", "initial_value": "",
                      "max_length": 300},
        )  # fmt: skip


def unload(apps, schema_editor):
    """Els ajustos es queden: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("dashboard", "0002_min_group_size")]

    operations = [migrations.RunPython(load, unload)]
