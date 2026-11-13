"""Moviments de tresoreria: només s'hi afegeixen files, també amb una consulta SQL directa
(T-M04-03; RN-T07, RNF-T2, CA-T06.3). Mateix contracte que el registre d'activitat (core 0004):
es rebutgen UPDATE, DELETE i TRUNCATE. «Anul·lat» es dedueix del contramoviment (RN-T25), i per
això cap excepció no cal.

Els permisos de PostgreSQL de RNF-T2 (treure UPDATE i DELETE a l'usuari de l'aplicació) no són
aquí: avui la plataforma té un sol usuari de base de dades, que és l'amo de les taules (P-75).

Desfer-la treu els activadors i la funció; la taula i les dades queden com estaven.
"""

from django.db import migrations

APPEND_ONLY_SQL = """
CREATE FUNCTION treasury_movement_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Els moviments de tresoreria no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER treasury_movement_no_update_or_delete
    BEFORE UPDATE OR DELETE ON treasury_movement
    FOR EACH ROW EXECUTE FUNCTION treasury_movement_immutable();

CREATE TRIGGER treasury_movement_no_truncate
    BEFORE TRUNCATE ON treasury_movement
    FOR EACH STATEMENT EXECUTE FUNCTION treasury_movement_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER treasury_movement_no_truncate ON treasury_movement;
DROP TRIGGER treasury_movement_no_update_or_delete ON treasury_movement;
DROP FUNCTION treasury_movement_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [("treasury", "0005_movement")]

    operations = [migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL)]
