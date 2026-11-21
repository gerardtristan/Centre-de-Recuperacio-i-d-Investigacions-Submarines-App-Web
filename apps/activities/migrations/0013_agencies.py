"""T-M02-41 (addenda de la 104): agències com a dada, `source = federation`, `official_level` a la
fitxa i els ajustos VC-55 a VC-59.

- `CertificationAgency` amb les dades inicials FECDAS, PADI, SSI, CMAS i NAUI [A verificar:
  secretaria].
- `agency` de `CertificationLevel` i de `DiverCertification` passa de text a FK. El text de cada
  fila es converteix en una agència (es crea si no hi és). Tornar enrere torna el nom com a text.
- Ajustos: destinació de les homologacions (VC-55, «FECDAS»), fotos (VC-56, apagat), mesos de
  conservació de la foto (VC-57, 3, de 0 a 24), preus de les tramitacions (VC-58, 0, amb data
  d'entrada en vigor) i cobrar-les (VC-59, apagat). Els permisos per editar-los són del nucli.
"""

import django.db.models.deletion
from django.db import migrations, models

AGENCIES = ("FECDAS", "PADI", "SSI", "CMAS", "NAUI")
SETTINGS = {
    "activities.homologation_target_agency": {
        "value_type": "text", "initial_value": "FECDAS", "max_length": 60,
    },
    "activities.card_photos_enabled": {"value_type": "boolean", "initial_value": False},
    "activities.card_photo_retention_months": {
        "value_type": "integer", "initial_value": 3, "min_value": 0, "max_value": 24,
    },
    "activities.homologation_fee_cents": {
        "value_type": "cents", "initial_value": 0, "min_value": 0,
        "affects_money": True, "effective_dated": True,
    },
    "activities.course_filing_fee_cents": {
        "value_type": "cents", "initial_value": 0, "min_value": 0,
        "affects_money": True, "effective_dated": True,
    },
    "activities.filing_fees_enabled": {"value_type": "boolean", "initial_value": False},
}  # fmt: skip
MODELS = ("CertificationLevel", "DiverCertification")


def seed(apps, schema_editor):
    Agency = apps.get_model("activities", "CertificationAgency")
    for name in AGENCIES:
        Agency.objects.get_or_create(name=name)
    Setting = apps.get_model("core", "Setting")
    for key, fields in SETTINGS.items():
        Setting.objects.get_or_create(key=key, defaults={"module": "activities", **fields})


def unseed(apps, schema_editor):
    """Les agències i els ajustos es queden fins que s'esborra el model (els ajustos: historial)."""


def text_to_agency(apps, schema_editor):
    Agency = apps.get_model("activities", "CertificationAgency")
    for name in MODELS:
        model = apps.get_model("activities", name)
        for row in model.objects.exclude(agency="").only("pk", "agency"):
            agency, _created = Agency.objects.get_or_create(name=row.agency.strip()[:60])
            model.objects.filter(pk=row.pk).update(agency_ref=agency)


def agency_to_text(apps, schema_editor):
    for name in MODELS:
        model = apps.get_model("activities", name)
        for row in model.objects.exclude(agency_ref=None).select_related("agency_ref"):
            model.objects.filter(pk=row.pk).update(agency=row.agency_ref.name)


def fk(related_name):
    return models.ForeignKey(
        null=True,
        blank=True,
        on_delete=django.db.models.deletion.PROTECT,
        related_name=related_name,
        to="activities.certificationagency",
        verbose_name="agència o federació",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("activities", "0012_void_pending_since"),
        ("core", "0013_business_settings"),
    ]

    operations = [
        migrations.CreateModel(
            name="CertificationAgency",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=60, unique=True, verbose_name="nom")),
                ("active", models.BooleanField(default=True, verbose_name="activa")),
            ],
            options={
                "verbose_name": "agència de titulació",
                "verbose_name_plural": "agències de titulació",
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(seed, unseed),
        migrations.AddField("certificationlevel", "agency_ref", fk("levels")),
        migrations.AddField("divercertification", "agency_ref", fk("certifications")),
        migrations.RunPython(text_to_agency, agency_to_text),
        migrations.RemoveField("certificationlevel", "agency"),
        migrations.RemoveField("divercertification", "agency"),
        migrations.RenameField("certificationlevel", "agency_ref", "agency"),
        migrations.RenameField("divercertification", "agency_ref", "agency"),
        migrations.AlterField(
            model_name="divercertification",
            name="source",
            field=models.CharField(
                choices=[
                    ("club_course", "Curs del club"),
                    ("declared", "Declarada"),
                    ("imported", "Importada"),
                    ("federation", "Tramitada a la federació"),
                ],
                max_length=12,
                verbose_name="origen",
            ),
        ),
        migrations.RemoveConstraint(model_name="divercertification", name="divercert_source_valid"),
        migrations.AddConstraint(
            model_name="divercertification",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    source__in=["club_course", "declared", "imported", "federation"]
                ),
                name="divercert_source_valid",
            ),
        ),
        migrations.AddField(
            model_name="trainingcatalogueentry",
            name="official_level",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="activities.certificationlevel",
                verbose_name="nivell oficial que es tramita",
            ),
        ),
    ]
