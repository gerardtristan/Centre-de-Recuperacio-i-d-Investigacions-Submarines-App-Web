"""Esborrat RGPD (T-M01-22; spec 00, HU-19, RN-51 i RN-89; decisió 028).

1. La sol·licitud d'esborrat guarda qui l'ha resolta i quan, el motiu d'un rebuig i quan s'ha
   executat, amb els estats «aprovada», «rebutjada» i «executada».
2. **Excepció acotada al registre d'activitat.** Els disparadors de la 0004 rebutgen qualsevol
   UPDATE, DELETE o TRUNCATE. La spec en preveu una sola excepció: en un esborrat RGPD, el que
   identifica la persona se substitueix per la seva referència anònima (RN-89). Aquesta migració
   canvia només la funció del disparador perquè accepti un UPDATE si es compleix TOT això:
   - la transacció ha posat el paràmetre `cris.rgpd_anonymise` a `on`
     (`apps.core.audit.identity_substitution`): cap UPDATE no passa per descuit;
   - no canvien l'identificador, la data, l'acció, l'objecte, el camp, l'actor (tipus, compte,
     persona, rols i origen) ni els detalls;
   - l'adreça IP queda igual o es buida;
   - el valor anterior, el valor nou i el motiu queden iguals o passen a ser la referència
     anònima d'una persona que ja està anonimitzada (`core_is_anonymous_ref`).
   Per tant, ni amb el paràmetre posat s'hi pot escriure cap text que no sigui una referència
   anònima existent. DELETE i TRUNCATE continuen rebutjats sempre.

Desfer-la torna a posar la funció de la 0004 (sense excepció) i treu els camps.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

SUBSTITUTION_SQL = """
CREATE FUNCTION core_is_anonymous_ref(candidate text) RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT EXISTS (
        SELECT 1 FROM core_person
        WHERE status = 'anonymised' AND anonymous_ref = candidate
    );
$$;

CREATE OR REPLACE FUNCTION core_auditentry_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    -- NEW només existeix en un UPDATE: per això la condició va en dos passos.
    IF TG_OP = 'UPDATE' AND current_setting('cris.rgpd_anonymise', true) = 'on' THEN
        IF NEW.id = OLD.id
            AND NEW.created_at = OLD.created_at
            AND NEW.action = OLD.action
            AND NEW.target_type = OLD.target_type
            AND NEW.target_id = OLD.target_id
            AND NEW.field = OLD.field
            AND NEW.actor_kind = OLD.actor_kind
            AND NEW.actor_account_id IS NOT DISTINCT FROM OLD.actor_account_id
            AND NEW.actor_person_id IS NOT DISTINCT FROM OLD.actor_person_id
            AND NEW.actor_roles = OLD.actor_roles
            AND NEW.actor_origin = OLD.actor_origin
            AND NEW.details = OLD.details
            AND (NEW.ip_address IS NULL OR NEW.ip_address IS NOT DISTINCT FROM OLD.ip_address)
            AND (
                NEW.old_value IS NOT DISTINCT FROM OLD.old_value
                OR (jsonb_typeof(NEW.old_value) = 'string'
                    AND core_is_anonymous_ref(NEW.old_value #>> '{}'))
            )
            AND (
                NEW.new_value IS NOT DISTINCT FROM OLD.new_value
                OR (jsonb_typeof(NEW.new_value) = 'string'
                    AND core_is_anonymous_ref(NEW.new_value #>> '{}'))
            )
            AND (NEW.reason = OLD.reason OR core_is_anonymous_ref(NEW.reason))
        THEN
            RETURN NEW;
        END IF;
    END IF;
    RAISE EXCEPTION 'El registre d''activitat no es pot modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
"""

REVERSE_SQL = """
CREATE OR REPLACE FUNCTION core_auditentry_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'El registre d''activitat no es pot modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

DROP FUNCTION core_is_anonymous_ref(text);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0020_email_daily_limit"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="erasurerequest",
            name="executed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="executada el"),
        ),
        migrations.AddField(
            model_name="erasurerequest",
            name="rejection_reason",
            field=models.TextField(blank=True, verbose_name="motiu del rebuig"),
        ),
        migrations.AddField(
            model_name="erasurerequest",
            name="resolved_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="resolta el"),
        ),
        migrations.AddField(
            model_name="erasurerequest",
            name="resolved_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="resolta per",
            ),
        ),
        migrations.AlterField(
            model_name="erasurerequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pendent"),
                    ("approved", "Aprovada"),
                    ("rejected", "Rebutjada"),
                    ("executed", "Executada"),
                ],
                default="pending",
                max_length=10,
                verbose_name="estat",
            ),
        ),
        migrations.AddConstraint(
            model_name="erasurerequest",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["pending", "approved", "rejected", "executed"])),
                name="erasure_request_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="erasurerequest",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("resolved_at__isnull", True),
                        ("resolved_by__isnull", True),
                        ("status", "pending"),
                    ),
                    models.Q(
                        models.Q(("status", "pending"), _negated=True),
                        ("resolved_at__isnull", False),
                        ("resolved_by__isnull", False),
                    ),
                    _connector="OR",
                ),
                name="erasure_request_resolved_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="erasurerequest",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("rejection_reason__regex", "\\S"), ("status", "rejected")),
                    models.Q(
                        models.Q(("status", "rejected"), _negated=True), ("rejection_reason", "")
                    ),
                    _connector="OR",
                ),
                name="erasure_request_reason_only_when_rejected",
            ),
        ),
        migrations.AddConstraint(
            model_name="erasurerequest",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("executed_at__isnull", False), ("status", "executed")),
                    models.Q(
                        models.Q(("status", "executed"), _negated=True),
                        ("executed_at__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="erasure_request_executed_at_only_when_executed",
            ),
        ),
        migrations.RunSQL(SUBSTITUTION_SQL, REVERSE_SQL),
    ]
