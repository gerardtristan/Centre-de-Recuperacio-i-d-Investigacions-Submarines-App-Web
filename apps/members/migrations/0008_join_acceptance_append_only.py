"""Acceptacions de l'alta (068): només s'hi afegeixen files, també amb SQL directe.

Mateix contracte que l'historial del soci (0003): es rebutgen UPDATE, DELETE i TRUNCATE. La fila
no porta dades personals pròpies; l'esborrat RGPD anonimitza la persona i la sol·licitud
(T-M01-22) i no necessita tocar aquesta taula. Les proves de concurrència desactiven els
disparadors de l'usuari només dins la transacció de neteja (`CommittedDataTestCase`).

Desfer-la treu els disparadors; no esborra cap fila.
"""

from django.db import migrations

APPEND_ONLY_SQL = """
CREATE FUNCTION members_joinacceptance_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les acceptacions de l''alta no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER members_joinacceptance_no_update_or_delete
    BEFORE UPDATE OR DELETE ON members_joinacceptance
    FOR EACH ROW EXECUTE FUNCTION members_joinacceptance_immutable();

CREATE TRIGGER members_joinacceptance_no_truncate
    BEFORE TRUNCATE ON members_joinacceptance
    FOR EACH STATEMENT EXECUTE FUNCTION members_joinacceptance_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER members_joinacceptance_no_truncate ON members_joinacceptance;
DROP TRIGGER members_joinacceptance_no_update_or_delete ON members_joinacceptance;
DROP FUNCTION members_joinacceptance_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [("members", "0007_join_birth_date_guardian_and_acceptances")]

    operations = [migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL)]
