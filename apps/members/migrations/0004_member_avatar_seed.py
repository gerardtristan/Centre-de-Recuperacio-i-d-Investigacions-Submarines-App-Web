"""Llavor de l'avatar: aleatòria, fixada en l'alta i que no canvia mai (M01-6, RN-M01-30).

La genera `new_avatar_seed` amb una font aleatòria segura del sistema, no cap dada personal:
per això l'anonimització de la T-M01-22 no l'ha de tocar i el disparador no hi xoca. El
disparador només salta si el valor canvia, de manera que desar el soci sense tocar-la (com fa
l'ORM amb tots els camps) continua funcionant.

En afegir la columna, Django calcula el valor per defecte una sola vegada: si hi hagués socis,
tots rebrien la mateixa llavor. Ara no n'hi ha a cap entorn (cap migració del M01 s'ha aplicat
fora de la base de dades de proves). Desfer-la treu el disparador i la columna, amb les llavors.
"""

from django.db import migrations, models

import apps.members.models

IMMUTABLE_SEED_SQL = """
CREATE FUNCTION members_member_avatar_seed_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'La llavor de l''avatar no es pot canviar.'
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER members_member_avatar_seed_no_update
    BEFORE UPDATE OF avatar_seed ON members_member
    FOR EACH ROW WHEN (OLD.avatar_seed IS DISTINCT FROM NEW.avatar_seed)
    EXECUTE FUNCTION members_member_avatar_seed_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER members_member_avatar_seed_no_update ON members_member;
DROP FUNCTION members_member_avatar_seed_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [("members", "0003_status_change_append_only")]

    operations = [
        migrations.AddField(
            model_name="member",
            name="avatar_seed",
            field=models.CharField(
                default=apps.members.models.new_avatar_seed,
                editable=False,
                max_length=64,
                verbose_name="llavor de l'avatar",
            ),
        ),
        migrations.RunSQL(IMMUTABLE_SEED_SQL, REVERSE_SQL),
    ]
