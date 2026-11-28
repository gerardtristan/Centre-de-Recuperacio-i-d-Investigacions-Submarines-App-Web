"""T-M07-21 (addenda 106; decisió 034): menús, capçalera i peu de la web pública. Les versions de
la capçalera i el peu només admeten INSERT, també amb una consulta directa (com les de les pàgines,
0002). El menú principal inicial és mínim (P-700): el de la capçalera pública actual («Inici»)
més «Notícies» i «Ajuda». Depèn de la 0010 (el PILOT l'encadena en fusionar)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

CHROME_APPEND_ONLY_SQL = """
CREATE FUNCTION website_chrome_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les versions de la capçalera i el peu no es poden modificar ni esborrar (%).',
        TG_OP USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER website_chrome_no_update_or_delete
    BEFORE UPDATE OR DELETE ON website_sitechrome
    FOR EACH ROW EXECUTE FUNCTION website_chrome_immutable();

CREATE TRIGGER website_chrome_no_truncate
    BEFORE TRUNCATE ON website_sitechrome
    FOR EACH STATEMENT EXECUTE FUNCTION website_chrome_immutable();
"""

CHROME_APPEND_ONLY_REVERSE_SQL = """
DROP TRIGGER website_chrome_no_truncate ON website_sitechrome;
DROP TRIGGER website_chrome_no_update_or_delete ON website_sitechrome;
DROP FUNCTION website_chrome_immutable();
"""

# Mínim i fàcil de substituir: l'enllaç de la capçalera pública actual (el logotip, «Inici») més
# «Notícies» i «Ajuda». El menú real (el de cris1954.cat) arriba amb les pàgines inicials (P-700).
INITIAL_MENU = [("Inici", "/"), ("Notícies", "/noticies/"), ("Ajuda", "/ajuda/")]


def load(apps, schema_editor):
    Menu = apps.get_model("website", "Menu")
    MenuItem = apps.get_model("website", "MenuItem")
    menu, created = Menu.objects.get_or_create(
        code="principal", defaults={"name": "Menú principal"}
    )
    if not created:
        return
    for order, (label, url) in enumerate(INITIAL_MENU, start=1):
        MenuItem.objects.create(menu=menu, label=label, url=url, order=order)


def unload(apps, schema_editor):
    """El menú es queda (la reversió de l'esquema l'esborra)."""


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0013_media_focal_renditions"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Menu",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("code", models.SlugField(max_length=30, unique=True, verbose_name="codi")),
                ("name", models.CharField(max_length=100, verbose_name="nom")),
            ],
            options={
                "verbose_name": "menú",
                "verbose_name_plural": "menús",
            },
        ),
        migrations.CreateModel(
            name="SiteChrome",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("number", models.PositiveIntegerField(unique=True, verbose_name="número")),
                (
                    "header_text",
                    models.CharField(max_length=120, verbose_name="text de la capçalera"),
                ),
                (
                    "footer_text",
                    models.TextField(blank=True, max_length=1000, verbose_name="text del peu"),
                ),
                ("saved_at", models.DateTimeField(auto_now_add=True, verbose_name="desada el")),
                ("note", models.CharField(blank=True, max_length=300, verbose_name="nota")),
                (
                    "saved_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="desada per",
                    ),
                ),
            ],
            options={
                "verbose_name": "versió de la capçalera i el peu",
                "verbose_name_plural": "versions de la capçalera i el peu",
                "ordering": ["number"],
            },
        ),
        migrations.RunSQL(CHROME_APPEND_ONLY_SQL, CHROME_APPEND_ONLY_REVERSE_SQL),
        migrations.CreateModel(
            name="MenuItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("label", models.CharField(max_length=40, verbose_name="text")),
                ("url", models.CharField(blank=True, max_length=300, verbose_name="adreça")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ordre")),
                (
                    "menu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="items",
                        to="website.menu",
                        verbose_name="menú",
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="website.page",
                        verbose_name="pàgina",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="children",
                        to="website.menuitem",
                        verbose_name="dins de",
                    ),
                ),
            ],
            options={
                "verbose_name": "enllaç del menú",
                "verbose_name_plural": "enllaços del menú",
                "ordering": ["order", "pk"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("page__isnull", False),
                            models.Q(("url", ""), _negated=True),
                            _negated=True,
                        ),
                        name="website_menuitem_one_target",
                    )
                ],
            },
        ),
        migrations.RunPython(load, unload),
    ]
