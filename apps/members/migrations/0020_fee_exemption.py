"""Exempció puntual d'una quota (T-M01-40; RN-M01-72 i RN-M01-94): només s'hi afegeixen files,
també amb SQL directe. Mateix contracte que l'historial del soci (0003): es rebutgen UPDATE,
DELETE i TRUNCATE. La fila no porta cap dada personal ni el motiu (que és al càrrec i al registre).

Desfer-la treu els disparadors i la taula.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION members_feeexemption_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les exempcions de quota no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER members_feeexemption_no_update_or_delete
    BEFORE UPDATE OR DELETE ON members_feeexemption
    FOR EACH ROW EXECUTE FUNCTION members_feeexemption_immutable();

CREATE TRIGGER members_feeexemption_no_truncate
    BEFORE TRUNCATE ON members_feeexemption
    FOR EACH STATEMENT EXECUTE FUNCTION members_feeexemption_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER members_feeexemption_no_truncate ON members_feeexemption;
DROP TRIGGER members_feeexemption_no_update_or_delete ON members_feeexemption;
DROP FUNCTION members_feeexemption_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0019_status_change_reason_anonymisation"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FeeExemption",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("starts_on", models.DateField(verbose_name="inici del període eximit")),
                ("valid_until", models.DateField(verbose_name="vàlid fins al")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "fee",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="exemption",
                        to="members.annualfee",
                        verbose_name="quota",
                    ),
                ),
                (
                    "granted_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="compte que l'ha concedit",
                    ),
                ),
            ],
            options={
                "verbose_name": "exempció de quota",
                "verbose_name_plural": "exempcions de quota",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("valid_until__gt", models.F("starts_on"))),
                        name="feeexemption_period_valid",
                    )
                ],
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
