"""Peça comuna d'ajustos (T-AJ-01; decisió 055, RN-AJ-01 a 04).

Crea `Setting` i `SettingVersion`. A més del model, uns disparadors de PostgreSQL rebutgen
qualsevol UPDATE, DELETE o TRUNCATE de les versions, també amb SQL directe («només s'hi
afegeixen files»). Cap ajust no es carrega aquí: els declara cada mòdul amb la seva pantalla.

Desfer-la treu els disparadors i les taules.
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION core_settingversion_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les versions d''un ajust no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER core_settingversion_no_update_or_delete
    BEFORE UPDATE OR DELETE ON core_settingversion
    FOR EACH ROW EXECUTE FUNCTION core_settingversion_immutable();

CREATE TRIGGER core_settingversion_no_truncate
    BEFORE TRUNCATE ON core_settingversion
    FOR EACH STATEMENT EXECUTE FUNCTION core_settingversion_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER core_settingversion_no_truncate ON core_settingversion;
DROP TRIGGER core_settingversion_no_update_or_delete ON core_settingversion;
DROP FUNCTION core_settingversion_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_person_birth_date"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Setting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("key", models.CharField(max_length=60, unique=True, verbose_name="clau")),
                ("module", models.CharField(max_length=30, verbose_name="mòdul")),
                (
                    "value_type",
                    models.CharField(
                        choices=[
                            ("integer", "Enter"),
                            ("cents", "Import en cèntims"),
                            ("boolean", "Sí o no"),
                            ("text", "Text"),
                            ("choice", "Opció"),
                            ("url", "URL"),
                            ("day_month", "Dia i mes"),
                            ("integer_list", "Llista d'enters"),
                        ],
                        max_length=20,
                        verbose_name="tipus",
                    ),
                ),
                ("initial_value", models.JSONField(verbose_name="valor inicial")),
                (
                    "min_value",
                    models.BigIntegerField(blank=True, null=True, verbose_name="valor mínim"),
                ),
                (
                    "max_value",
                    models.BigIntegerField(blank=True, null=True, verbose_name="valor màxim"),
                ),
                ("choices", models.JSONField(blank=True, default=list, verbose_name="opcions")),
                (
                    "max_length",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="longitud màxima"
                    ),
                ),
                ("affects_money", models.BooleanField(default=False, verbose_name="afecta diners")),
                (
                    "effective_dated",
                    models.BooleanField(default=False, verbose_name="amb data d'entrada en vigor"),
                ),
            ],
            options={
                "verbose_name": "ajust",
                "verbose_name_plural": "ajustos",
                "ordering": ["module", "key"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("affects_money", False), ("effective_dated", True), _connector="OR"
                        ),
                        name="setting_money_is_effective_dated",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("min_value__isnull", True),
                            ("max_value__isnull", True),
                            ("min_value__lte", models.F("max_value")),
                            _connector="OR",
                        ),
                        name="setting_range_ordered",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="SettingVersion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("value", models.JSONField(verbose_name="valor")),
                (
                    "effective_from",
                    models.DateField(blank=True, null=True, verbose_name="en vigor des de"),
                ),
                (
                    "changed_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="data del canvi"
                    ),
                ),
                (
                    "previous_value",
                    models.JSONField(blank=True, null=True, verbose_name="valor anterior"),
                ),
                ("note", models.TextField(blank=True, verbose_name="nota")),
                (
                    "changed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="compte que el canvia",
                    ),
                ),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="versions",
                        to="core.setting",
                        verbose_name="ajust",
                    ),
                ),
            ],
            options={
                "verbose_name": "versió d'un ajust",
                "verbose_name_plural": "versions dels ajustos",
                "ordering": ["setting", "changed_at", "id"],
                "indexes": [
                    models.Index(
                        fields=["setting", "effective_from"], name="core_settin_setting_697d6c_idx"
                    )
                ],
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
