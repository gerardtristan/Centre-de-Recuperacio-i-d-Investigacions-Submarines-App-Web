"""Catàleg del M02 i les seves dades inicials (T-M02-02; pla, M02-6).

- Tipus de sortida: «Immersió», «Medi ambient» (de medi ambient), «Sèniors» i «Jornada oberta»,
  amb el departament «General» de la 00 per defecte [A validar: junta, si són tipus propis]. El
  responsable els pot desactivar.
- Subtipus de medi ambient: «Neteja» (F §5). La resta de la llista és la S-M02-13.
- El catàleg de cursos i d'especialitats neix buit (S-M02-07): els cursos i els preus reals els
  ha de donar la junta. Cap projecte.

Cap dada personal. Desfer-la esborra aquestes files; només es pot si cap activitat les fa servir.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

OUTING_TYPES = [
    ("Immersió", False),
    ("Medi ambient", True),
    ("Sèniors", False),
    ("Jornada oberta", False),
]
SUBTYPES = ["Neteja"]


def create(apps, schema_editor):
    general, _ = apps.get_model("core", "Department").objects.get_or_create(name="General")
    OutingType = apps.get_model("activities", "OutingType")
    for name, environmental in OUTING_TYPES:
        OutingType.objects.create(
            name=name, is_environmental=environmental, default_department=general
        )
    Subtype = apps.get_model("activities", "EnvironmentalSubtype")
    for name in SUBTYPES:
        Subtype.objects.create(name=name)


def remove(apps, schema_editor):
    apps.get_model("activities", "EnvironmentalSubtype").objects.filter(name__in=SUBTYPES).delete()
    apps.get_model("activities", "OutingType").objects.filter(
        name__in=[name for name, _ in OUTING_TYPES]
    ).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0006_charges_and_departments"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EnvironmentalSubtype",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=80, unique=True, verbose_name="nom")),
                ("active", models.BooleanField(default=True, verbose_name="actiu")),
            ],
            options={
                "verbose_name": "subtipus de medi ambient",
                "verbose_name_plural": "subtipus de medi ambient",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="OutingType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=80, unique=True, verbose_name="nom")),
                (
                    "is_environmental",
                    models.BooleanField(default=False, verbose_name="és de medi ambient"),
                ),
                ("active", models.BooleanField(default=True, verbose_name="actiu")),
                (
                    "default_department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.department",
                        verbose_name="departament per defecte",
                    ),
                ),
            ],
            options={
                "verbose_name": "tipus de sortida",
                "verbose_name_plural": "tipus de sortida",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="TrainingCatalogueEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[("course", "Curs"), ("speciality", "Especialitat")],
                        max_length=10,
                        verbose_name="catàleg",
                    ),
                ),
                ("name", models.CharField(max_length=120, verbose_name="nom")),
                ("level", models.CharField(blank=True, max_length=60, verbose_name="nivell")),
                ("description", models.TextField(blank=True, verbose_name="descripció")),
                ("requirements", models.TextField(blank=True, verbose_name="requisits")),
                (
                    "default_places",
                    models.PositiveSmallIntegerField(verbose_name="places per defecte"),
                ),
                (
                    "price_member_cents",
                    models.PositiveIntegerField(verbose_name="preu de soci (cèntims)"),
                ),
                (
                    "price_non_member_cents",
                    models.PositiveIntegerField(verbose_name="preu de no soci (cèntims)"),
                ),
                (
                    "reinforcement_price_cents",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="preu del reforç (cèntims)"
                    ),
                ),
                (
                    "open_to_non_members",
                    models.BooleanField(default=False, verbose_name="oberta a no socis"),
                ),
                ("active", models.BooleanField(default=True, verbose_name="activa")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.department",
                        verbose_name="departament",
                    ),
                ),
            ],
            options={
                "verbose_name": "fitxa del catàleg",
                "verbose_name_plural": "fitxes del catàleg",
                "ordering": ["kind", "name"],
            },
        ),
        migrations.CreateModel(
            name="TrainingCataloguePrice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "price_member_cents",
                    models.PositiveIntegerField(verbose_name="preu de soci (cèntims)"),
                ),
                (
                    "price_non_member_cents",
                    models.PositiveIntegerField(verbose_name="preu de no soci (cèntims)"),
                ),
                (
                    "reinforcement_price_cents",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="preu del reforç (cèntims)"
                    ),
                ),
                ("valid_from", models.DateField(verbose_name="vigent des del")),
                ("note", models.TextField(verbose_name="motiu")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="canviat per",
                    ),
                ),
                (
                    "entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="prices",
                        to="activities.trainingcatalogueentry",
                        verbose_name="fitxa",
                    ),
                ),
            ],
            options={
                "verbose_name": "preu del catàleg",
                "verbose_name_plural": "preus del catàleg",
            },
        ),
        migrations.CreateModel(
            name="EnvironmentalProject",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="nom")),
                ("objective", models.TextField(verbose_name="objectiu")),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Actiu"), ("finished", "Acabat")],
                        default="active",
                        max_length=10,
                        verbose_name="estat",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.department",
                        verbose_name="departament",
                    ),
                ),
            ],
            options={
                "verbose_name": "projecte de medi ambient",
                "verbose_name_plural": "projectes de medi ambient",
                "ordering": ["name"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ["active", "finished"])),
                        name="environmentalproject_status_valid",
                    )
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="trainingcatalogueentry",
            constraint=models.UniqueConstraint(
                fields=("kind", "name"), name="trainingcatalogueentry_name_unique_per_kind"
            ),
        ),
        migrations.AddConstraint(
            model_name="trainingcatalogueentry",
            constraint=models.CheckConstraint(
                condition=models.Q(("kind__in", ["course", "speciality"])),
                name="trainingcatalogueentry_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="trainingcatalogueentry",
            constraint=models.CheckConstraint(
                condition=models.Q(("default_places__gt", 0)),
                name="trainingcatalogueentry_places_positive",
            ),
        ),
        migrations.AddIndex(
            model_name="trainingcatalogueprice",
            index=models.Index(fields=["entry", "valid_from"], name="cataloguepriceentry_from_idx"),
        ),
        migrations.RunPython(create, remove),
    ]
