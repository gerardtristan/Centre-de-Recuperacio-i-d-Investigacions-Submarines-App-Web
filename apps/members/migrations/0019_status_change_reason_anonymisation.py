"""Historial dels socis: excepció acotada per anonimitzar el motiu en un esborrat RGPD (T-M01-22;
decisió 028; aprovació del pla de la T-M01-11, 04/11/2026).

Els disparadors de la 0003 rebutgen qualsevol UPDATE, DELETE o TRUNCATE. `reason` és text lliure
i pot portar dades personals. Aquesta migració canvia només la funció del disparador perquè
accepti un UPDATE si es compleix TOT això:
- la transacció ha posat el paràmetre `cris.rgpd_anonymise` a `on`
  (`apps.core.audit.identity_substitution`), el mateix del registre d'activitat (core/0019);
- no canvia cap altra columna: ni el soci, ni els estats, ni els tipus, ni la data efectiva, ni
  la procedència, ni el compte, ni la data;
- el motiu nou és exactament la referència anònima de la persona d'aquell soci, que ja ha
  d'estar anonimitzada.
Per tant, ni amb el paràmetre posat es pot canviar el motiu d'un soci que no s'ha anonimitzat, ni
escriure-hi cap altre text. DELETE i TRUNCATE continuen rebutjats sempre.

Desfer-la torna a posar la funció de la 0003, sense excepció.
"""

from django.db import migrations

EXCEPTION_SQL = """
CREATE OR REPLACE FUNCTION members_memberstatuschange_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    -- NEW només existeix en un UPDATE: per això la condició va en dos passos.
    IF TG_OP = 'UPDATE' AND current_setting('cris.rgpd_anonymise', true) = 'on' THEN
        IF NEW.id = OLD.id
            AND NEW.member_id = OLD.member_id
            AND NEW.from_status = OLD.from_status
            AND NEW.to_status = OLD.to_status
            AND NEW.from_type_id IS NOT DISTINCT FROM OLD.from_type_id
            AND NEW.to_type_id = OLD.to_type_id
            AND NEW.effective_on = OLD.effective_on
            AND NEW.origin = OLD.origin
            AND NEW.actor_account_id IS NOT DISTINCT FROM OLD.actor_account_id
            AND NEW.created_at = OLD.created_at
            AND EXISTS (
                SELECT 1
                FROM members_member AS m
                JOIN core_person AS p ON p.id = m.person_id
                WHERE m.id = NEW.member_id
                  AND p.status = 'anonymised'
                  AND p.anonymous_ref = NEW.reason
            )
        THEN
            RETURN NEW;
        END IF;
    END IF;
    RAISE EXCEPTION 'L''historial del soci no es pot modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
"""

REVERSE_SQL = """
CREATE OR REPLACE FUNCTION members_memberstatuschange_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'L''historial del soci no es pot modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
"""


class Migration(migrations.Migration):
    dependencies = [("members", "0018_member_card_version_and_key_id")]

    operations = [migrations.RunSQL(EXCEPTION_SQL, REVERSE_SQL)]
