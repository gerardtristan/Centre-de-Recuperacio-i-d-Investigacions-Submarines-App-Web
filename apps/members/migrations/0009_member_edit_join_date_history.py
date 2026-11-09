"""Correccions de la data d'alta (T-M01-15b; RN-M01-22): taula i disparadors.

Mateix contracte que l'historial del soci (0003): es rebutgen UPDATE, DELETE i TRUNCATE, també
amb SQL directe. La fila no porta text lliure ni dades personals pròpies (dates, marca i
compte), de manera que l'esborrat RGPD (T-M01-22) no necessita tocar-la. Les proves de
concurrència desactiven els disparadors de l'usuari només dins la transacció de neteja
(`CommittedDataTestCase`).

Desfer-la treu els disparadors i la taula.
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION members_memberjoindatechange_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les correccions de la data d''alta no es poden modificar ni esborrar (%).',
        TG_OP USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER members_memberjoindatechange_no_update_or_delete
    BEFORE UPDATE OR DELETE ON members_memberjoindatechange
    FOR EACH ROW EXECUTE FUNCTION members_memberjoindatechange_immutable();

CREATE TRIGGER members_memberjoindatechange_no_truncate
    BEFORE TRUNCATE ON members_memberjoindatechange
    FOR EACH STATEMENT EXECUTE FUNCTION members_memberjoindatechange_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER members_memberjoindatechange_no_truncate ON members_memberjoindatechange;
DROP TRIGGER members_memberjoindatechange_no_update_or_delete ON members_memberjoindatechange;
DROP FUNCTION members_memberjoindatechange_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0008_join_acceptance_append_only"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MemberJoinDateChange",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("from_joined_on", models.DateField(verbose_name="data d'alta anterior")),
                ("from_is_approximate", models.BooleanField(verbose_name="aproximada abans")),
                ("to_joined_on", models.DateField(verbose_name="data d'alta nova")),
                ("to_is_approximate", models.BooleanField(verbose_name="aproximada ara")),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="data i hora"
                    ),
                ),
                (
                    "actor_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="compte",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="join_date_changes",
                        to="members.member",
                        verbose_name="soci",
                    ),
                ),
            ],
            options={
                "verbose_name": "correcció de la data d'alta",
                "verbose_name_plural": "correccions de la data d'alta",
                "indexes": [
                    models.Index(fields=["member", "created_at"], name="joindatechange_member_idx")
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("from_is_approximate", models.F("to_is_approximate")),
                            ("from_joined_on", models.F("to_joined_on")),
                            _negated=True,
                        ),
                        name="memberjoindatechange_changes_something",
                    )
                ],
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
