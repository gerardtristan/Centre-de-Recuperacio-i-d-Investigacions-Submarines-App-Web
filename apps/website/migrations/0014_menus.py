"""T-M07-21 (addenda 106; decisió 034): menús, capçalera i peu de la web pública. Les versions de
la capçalera i el peu només admeten INSERT, també amb una consulta directa (com les de les pàgines,
0002). El menú principal inicial és el de la capçalera del wireframe públic
(`design/wireframes/publica.html`), amb «Notícies» i «Ajuda» (P-700): els enllaços a pàgines no
surten fins que la pàgina es publica. Depèn de la 0010 (el PILOT l'encadena en fusionar)."""

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

# (text, pàgina o adreça, submenú). Els sis primers, a la pastilla; la resta, a «Més».
INITIAL_MENU = [
    ("Inici", "/", []),
    ("Activitats", "/activitats/", [("Formació i cursos", "formacio"), ("Sortides", "sortides")]),
    ("Qui som", "qui-som", []),
    ("El Centre", "el-centre", []),
    ("Projectes", "projectes", []),
    ("Notícies", "/noticies/", []),
    ("Medi ambient", "medi-ambient", []),
    ("Galeria", "galeria", []),
    ("Fer-se soci", "/fer-se-soci/", []),
    ("Contacte", "/contacte/", []),
    ("Ajuda", "/ajuda/", []),
]


def load(apps, schema_editor):
    Menu = apps.get_model("website", "Menu")
    MenuItem = apps.get_model("website", "MenuItem")
    Page = apps.get_model("website", "Page")
    menu, created = Menu.objects.get_or_create(
        code="principal", defaults={"name": "Menú principal"}
    )
    if not created:
        return

    def target(value):
        if value.startswith("/"):
            return {"url": value}
        return {"page": Page.objects.filter(slug=value).first()}

    for order, (label, value, children) in enumerate(INITIAL_MENU, start=1):
        item = MenuItem.objects.create(menu=menu, label=label, order=order, **target(value))
        for sub_order, (sub_label, sub_value) in enumerate(children, start=1):
            MenuItem.objects.create(
                menu=menu, parent=item, label=sub_label, order=sub_order, **target(sub_value)
            )


def unload(apps, schema_editor):
    """El menú es queda (la reversió de l'esquema l'esborra)."""


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0010_tutorials"),
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
