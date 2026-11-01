"""Registre d'activitat (T-M01-07; spec 00, RN-50 a RN-53; RN-RP-15).

A més del model, uns disparadors de PostgreSQL rebutgen qualsevol UPDATE, DELETE o TRUNCATE
de la taula, també amb SQL directe o des d'una consola (RN-51, CA-14.3). L'única excepció de
la spec, substituir la identitat per la referència anònima en un esborrat RGPD (RN-89), no
existeix encara: l'afegirà, acotada, la tasca de l'esborrat RGPD amb una migració pròpia.
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import apps.core.models

IMMUTABLE_SQL = """
CREATE FUNCTION core_auditentry_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'El registre d''activitat no es pot modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER core_auditentry_no_update_or_delete
    BEFORE UPDATE OR DELETE ON core_auditentry
    FOR EACH ROW EXECUTE FUNCTION core_auditentry_immutable();

CREATE TRIGGER core_auditentry_no_truncate
    BEFORE TRUNCATE ON core_auditentry
    FOR EACH STATEMENT EXECUTE FUNCTION core_auditentry_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER core_auditentry_no_truncate ON core_auditentry;
DROP TRIGGER core_auditentry_no_update_or_delete ON core_auditentry;
DROP FUNCTION core_auditentry_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_initial_roles_and_matrix"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, verbose_name="data i hora"
                    ),
                ),
                (
                    "actor_kind",
                    models.CharField(
                        choices=[
                            ("account", "Compte"),
                            ("guest", "Convidat"),
                            ("system", "Sistema"),
                            ("anonymous", "Sense identificar"),
                        ],
                        max_length=10,
                        verbose_name="tipus d'actor",
                    ),
                ),
                (
                    "actor_roles",
                    models.JSONField(blank=True, default=list, verbose_name="rols actius"),
                ),
                (
                    "actor_origin",
                    models.CharField(blank=True, max_length=100, verbose_name="origen"),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(blank=True, null=True, verbose_name="adreça IP"),
                ),
                ("action", models.CharField(max_length=60, verbose_name="acció")),
                (
                    "target_type",
                    models.CharField(blank=True, max_length=60, verbose_name="tipus d'objecte"),
                ),
                (
                    "target_id",
                    models.CharField(
                        blank=True, max_length=64, verbose_name="identificador de l'objecte"
                    ),
                ),
                ("field", models.CharField(blank=True, max_length=60, verbose_name="camp")),
                (
                    "old_value",
                    models.JSONField(
                        blank=True,
                        encoder=apps.core.models.AuditJSONEncoder,
                        null=True,
                        verbose_name="valor anterior",
                    ),
                ),
                (
                    "new_value",
                    models.JSONField(
                        blank=True,
                        encoder=apps.core.models.AuditJSONEncoder,
                        null=True,
                        verbose_name="valor nou",
                    ),
                ),
                ("reason", models.TextField(blank=True, verbose_name="motiu")),
                (
                    "details",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=apps.core.models.AuditJSONEncoder,
                        verbose_name="detalls",
                    ),
                ),
                (
                    "actor_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="compte que actua",
                    ),
                ),
                (
                    "actor_person",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.person",
                        verbose_name="persona que actua",
                    ),
                ),
            ],
            options={
                "verbose_name": "entrada del registre d'activitat",
                "verbose_name_plural": "registre d'activitat",
                "ordering": ["created_at", "id"],
                "indexes": [
                    models.Index(fields=["target_type", "target_id"], name="auditentry_target_idx"),
                    models.Index(
                        fields=["actor_account", "created_at"], name="auditentry_account_idx"
                    ),
                    models.Index(fields=["action", "created_at"], name="auditentry_action_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("actor_account__isnull", False), ("actor_kind", "account")),
                            models.Q(
                                models.Q(("actor_kind", "account"), _negated=True),
                                ("actor_account__isnull", True),
                                ("actor_roles", []),
                            ),
                            _connector="OR",
                        ),
                        name="auditentry_account_actor",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("actor_kind__in", ["system", "guest"]), _negated=True),
                            models.Q(("actor_origin", ""), _negated=True),
                            _connector="OR",
                        ),
                        name="auditentry_origin_for_system_and_guest",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("actor_kind", "guest"), _negated=True),
                            ("actor_person__isnull", False),
                            _connector="OR",
                        ),
                        name="auditentry_guest_has_person",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("actor_kind", "anonymous"), _negated=True),
                            ("actor_person__isnull", True),
                            _connector="OR",
                        ),
                        name="auditentry_anonymous_has_no_person",
                    ),
                ],
            },
        ),
        migrations.RunSQL(IMMUTABLE_SQL, REVERSE_SQL),
    ]
