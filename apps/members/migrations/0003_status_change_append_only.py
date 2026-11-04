"""Historial dels socis: només s'hi afegeixen files (M01-6, «sense UPDATE ni DELETE»).

Funció i disparadors propis, no els del registre d'activitat: el contracte és el mateix
(rebutjar UPDATE, DELETE i TRUNCATE, també amb SQL directe), però el missatge és d'aquesta
taula i l'excepció futura de la T-M01-22 (anonimitzar `reason`) s'hi podrà afegir sense tocar
el registre d'activitat. Les claus foranes que hi apunten són PROTECT: cap esborrat en
cascada hi arriba. Les proves de concurrència desactiven els disparadors de l'usuari només
dins la transacció de neteja (`CommittedDataTestCase`).

Desfer-la treu els disparadors; no esborra cap fila.
"""

from django.db import migrations

APPEND_ONLY_SQL = """
CREATE FUNCTION members_memberstatuschange_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'L''historial del soci no es pot modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER members_memberstatuschange_no_update_or_delete
    BEFORE UPDATE OR DELETE ON members_memberstatuschange
    FOR EACH ROW EXECUTE FUNCTION members_memberstatuschange_immutable();

CREATE TRIGGER members_memberstatuschange_no_truncate
    BEFORE TRUNCATE ON members_memberstatuschange
    FOR EACH STATEMENT EXECUTE FUNCTION members_memberstatuschange_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER members_memberstatuschange_no_truncate ON members_memberstatuschange;
DROP TRIGGER members_memberstatuschange_no_update_or_delete ON members_memberstatuschange;
DROP FUNCTION members_memberstatuschange_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [("members", "0002_initial_types_and_counter")]

    operations = [migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL)]
