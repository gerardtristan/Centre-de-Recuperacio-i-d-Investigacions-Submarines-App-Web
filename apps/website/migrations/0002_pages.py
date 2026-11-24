"""T-M07-04 (M07-6): pàgines i versions. Les versions només admeten INSERT, també amb una
consulta directa (RN-M07-03; patró de licences/0001). Les pàgines inicials són les de F §8.2 que
no tenen pantalla pròpia (P-590), sense contingut i sense publicar (P-40, S-M07-02)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

VERSION_APPEND_ONLY_SQL = """
CREATE FUNCTION website_version_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les versions de pàgina no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER website_version_no_update_or_delete
    BEFORE UPDATE OR DELETE ON website_pageversion
    FOR EACH ROW EXECUTE FUNCTION website_version_immutable();

CREATE TRIGGER website_version_no_truncate
    BEFORE TRUNCATE ON website_pageversion
    FOR EACH STATEMENT EXECUTE FUNCTION website_version_immutable();
"""

VERSION_APPEND_ONLY_REVERSE_SQL = """
DROP TRIGGER website_version_no_truncate ON website_pageversion;
DROP TRIGGER website_version_no_update_or_delete ON website_pageversion;
DROP FUNCTION website_version_immutable();
"""

# Adreça, títol i ordre al menú. «Inici» és la portada (T-M07-05); Notícies, Fer-se soci,
# Contacte, Preguntes freqüents, Tutorials i Butlletí tenen pantalla pròpia (M07-8).
INITIAL_PAGES = [
    ("qui-som", "Qui som", 1),
    ("el-centre", "El Centre", 2),
    ("historia", "Història", 3),
    ("formacio", "Formació i cursos", 4),
    ("sortides", "Sortides", 5),
    ("medi-ambient", "Medi ambient", 6),
    ("projectes", "Projectes", 7),
    ("galeria", "Galeria", 8),
]


def load(apps, schema_editor):
    Page = apps.get_model("website", "Page")
    for slug, title, order in INITIAL_PAGES:
        Page.objects.get_or_create(slug=slug, defaults={"title": title, "menu_order": order})


def unload(apps, schema_editor):
    """Les pàgines es queden (la reversió de l'esquema les esborra)."""


# fmt: off
class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_settings'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=60, unique=True, verbose_name='adreça')),
                ('title', models.CharField(max_length=120, verbose_name='títol')),
                ('template', models.CharField(choices=[('basica', 'Bàsica'), ('portada', 'Portada'), ('llista', 'Activitats'), ('blog', 'Notícies')], default='basica', max_length=20, verbose_name='plantilla')),
                ('accent', models.CharField(choices=[('accent', 'Daurat'), ('mari', 'Marí'), ('info', 'Blau')], default='accent', max_length=20, verbose_name="color d'accent")),
                ('menu_order', models.PositiveSmallIntegerField(default=0, verbose_name='ordre al menú')),
                ('in_menu', models.BooleanField(default=False, verbose_name='al menú')),
                ('share_title', models.CharField(blank=True, max_length=200, verbose_name='títol per compartir')),
                ('share_description', models.CharField(blank=True, max_length=500, verbose_name='descripció per compartir')),
                ('status', models.CharField(choices=[('draft', 'Esborrany'), ('published', 'Publicada'), ('retired', 'Retirada')], default='draft', max_length=20, verbose_name='estat')),
            ],
            options={
                'verbose_name': 'pàgina',
                'verbose_name_plural': 'pàgines',
                'ordering': ['menu_order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='PageVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(verbose_name='número')),
                ('blocks', models.JSONField(default=list, verbose_name='blocs')),
                ('published_at', models.DateTimeField(auto_now_add=True, verbose_name='publicada el')),
                ('note', models.CharField(blank=True, max_length=300, verbose_name='nota')),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='versions', to='website.page', verbose_name='pàgina')),
                ('published_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='publicada per')),
            ],
            options={
                'verbose_name': 'versió de pàgina',
                'verbose_name_plural': 'versions de pàgina',
                'ordering': ['page', 'number'],
                'constraints': [models.UniqueConstraint(fields=('page', 'number'), name='website_version_unique')],
            },
        ),
        migrations.RunSQL(VERSION_APPEND_ONLY_SQL, VERSION_APPEND_ONLY_REVERSE_SQL),
        migrations.RunPython(load, unload),
    ]
# fmt: on
