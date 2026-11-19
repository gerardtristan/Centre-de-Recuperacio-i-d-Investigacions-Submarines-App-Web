"""Textos editables dels correus (T-M00-08; 085, S-1 i S-3): text per defecte, versió publicada
amb el valor anterior, vista prèvia, permís i seguretat del text (cap plantilla des de la base
de dades, cap HTML). Només dades inventades."""

import datetime
import re

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import translation

from apps.core import business_settings, mail, texts
from apps.core.models import (
    AuditEntry,
    OutgoingEmail,
    PermissionMatrixVersion,
    Role,
    RolePermission,
    Setting,
    SettingVersion,
)
from apps.core.tests.test_guest_links import admin_client

pytestmark = pytest.mark.django_db

R = Role.Code
AREA = "texts-members"
CODE = f"settings.section.{AREA}"
OLD_CODE = "settings.section.texts"
LEAVE = f"{AREA}.baixa-efectiva"
DUE = f"{AREA}.recordatori-quota"
OVERDUE = f"{AREA}.recordatori-quota-vencuda"
EDITED = "Baixa feta\n\nHola,\n\nDes del {data} ja no ets soci.\n"


def read_only_treasurer(make_admin):
    RolePermission.objects.create(
        role=Role.objects.get(code=R.TREASURER), permission_code=CODE, scope="read"
    )
    return make_admin(R.TREASURER)


def leave_email():
    return mail.queue_email(
        "baixa-efectiva",
        to="anna@example.org",
        context={"effective_on": datetime.date(2026, 12, 31)},
    )


def reminder(overdue):
    context = {"due_on": datetime.date(2026, 12, 15), "amount": "55,00 €", "overdue": overdue}
    return mail.queue_email("recordatori-quota", to="anna@example.org", context=context)


def url(key, name="setting_detail"):
    return reverse(f"administration:{name}", args=[AREA, key])


# --- Registre i text per defecte ------------------------------------------------------------


def test_every_editable_email_has_its_setting_priority_and_a_valid_default():
    for key, entry in texts.EMAILS.items():
        setting = Setting.objects.get(key=key)  # el crea `core/0047`
        assert (setting.module, setting.value_type, setting.initial_value) == (AREA, "text", "")
        assert entry.template in mail.TEMPLATE_PRIORITIES
        texts.validate(key, str(entry.default))


def test_without_a_published_version_the_default_text_is_sent():
    email = leave_email()
    assert email.subject == "La teva baixa al C.R.I.S. és efectiva"
    assert "és efectiva des del 31/12/2026." in email.body_text
    assert email.body_html == "" and email.language == "ca"


def test_the_reminder_picks_the_variant_by_the_due_date():
    assert reminder(False).subject == "Recordatori: la teva quota del C.R.I.S."
    overdue = reminder(True)
    assert overdue.subject == "Tens una quota del C.R.I.S. pendent de pagar"
    assert "de 55,00 € va vèncer el 15/12/2026" in overdue.body_text


# --- Publicar una versió --------------------------------------------------------------------


def test_published_text_is_sent_with_its_values_and_keeps_the_previous_one(make_admin):
    secretary = make_admin(R.SECRETARY)
    business_settings.change(LEAVE, EDITED, secretary, "Text de la secretaria (prova)")

    email = leave_email()
    assert email.subject == "Baixa feta"
    assert email.body_text == "Hola,\n\nDes del 31/12/2026 ja no ets soci.\n"
    version = SettingVersion.objects.get(setting__key=LEAVE)
    assert (version.previous_value, version.note) == ("", "Text de la secretaria (prova)")
    entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED, field=LEAVE)
    assert (entry.old_value, entry.new_value) == ("", EDITED)

    business_settings.change(LEAVE, "", secretary)  # torna al text per defecte
    assert leave_email().subject == "La teva baixa al C.R.I.S. és efectiva"
    assert SettingVersion.objects.filter(setting__key=LEAVE).count() == 2


def test_editing_one_variant_does_not_change_the_other(make_admin):
    business_settings.change(
        OVERDUE, "Impagada\n\nPaga {import} del {data}.", make_admin(R.SECRETARY)
    )
    assert reminder(True).subject == "Impagada"
    assert reminder(False).subject == "Recordatori: la teva quota del C.R.I.S."


# --- Seguretat del text ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "Assumpte\n\nHola {nom}",  # variable que aquest correu no té
        "Assumpte\n\n{{ data }}",  # sintaxi de plantilla de Django
        "Assumpte\n\n{% load static %}{% debug %}",
        "Assumpte\n\n{data.__class__}",
        "Assumpte\n\n<a href='https://exemple.invalid'>entra</a>",  # HTML
        "Assumpte\n\n<script>alert(1)</script>",
        "Només assumpte",
        "\n\nNomés cos",
    ],
)
def test_unsafe_or_incomplete_text_is_rejected_and_nothing_is_saved(make_admin, value):
    with pytest.raises(ValidationError):
        business_settings.change(LEAVE, value, make_admin(R.SECRETARY))
    assert not SettingVersion.objects.filter(setting__key=LEAVE).exists()


def test_values_are_inserted_once_and_never_rendered_as_a_template(make_admin):
    business_settings.change(DUE, "Quota\n\nImport: {import}, {data}", make_admin(R.SECRETARY))
    context = {"due_on": datetime.date(2026, 12, 15), "amount": "{data} {{ 7|add:1 }}"}
    email = mail.queue_email("recordatori-quota", to="anna@example.org", context=context)
    assert email.body_text == "Import: {data} {{ 7|add:1 }}, 15/12/2026\n"


def test_the_subject_is_a_single_line():
    subject, body = texts.preview(LEAVE, "Assumpte   amb  espais\nCos")
    assert (subject, body) == ("Assumpte amb espais", "Cos\n")


# --- Permís ---------------------------------------------------------------------------------


def test_only_the_section_editor_publishes(make_admin):
    reader = read_only_treasurer(make_admin)  # «Cons.»
    with pytest.raises(Http404):
        business_settings.change(LEAVE, EDITED, reader)
    assert AuditEntry.objects.filter(action=business_settings.ACTION_DENIED, field=LEAVE).exists()
    with pytest.raises(Http404):
        business_settings.change(LEAVE, EDITED, make_admin(R.COURSES_MANAGER))
    assert not SettingVersion.objects.exists()


# --- Pantalla -------------------------------------------------------------------------------


def test_screen_shows_the_default_text_to_edit_and_the_allowed_variables(make_admin):
    client = admin_client(make_admin(R.SECRETARY))
    listing = client.get(reverse("administration:settings_section", args=[AREA]))
    assert "Correu de baixa efectiva" in listing.content.decode()
    html = client.get(url(LEAVE)).content.decode()
    assert "La teva baixa com a soci és efectiva des del {data}." in html
    assert "{data} (data de la baixa)" in html


def test_preview_uses_invented_data_escapes_the_text_and_saves_nothing(make_admin):
    client = admin_client(make_admin(R.SECRETARY))
    value = 'Baixa & co\n\nDes del {data}, "adeu".'
    response = client.post(url(LEAVE), {"value": value, "note": "", "preview": ""})
    html = response.content.decode()
    assert response.status_code == 200
    assert "Vista prèvia amb dades inventades" in html
    assert "Baixa &amp; co" in html and "Des del 31/12/2026, &quot;adeu&quot;." in html
    assert not SettingVersion.objects.exists()


def test_preview_of_an_unsafe_text_shows_the_error(make_admin):
    client = admin_client(make_admin(R.SECRETARY))
    response = client.post(url(LEAVE), {"value": "A\n\n<b>x</b>", "note": "", "preview": ""})
    assert "etiquetes HTML" in response.content.decode()
    assert "Vista prèvia amb dades inventades" not in response.content.decode()


def test_preview_without_edit_permission_is_not_found(make_admin):
    client = admin_client(read_only_treasurer(make_admin))
    assert client.get(url(LEAVE)).status_code == 200  # «Cons.»: veu el text i l'historial
    response = client.post(url(LEAVE), {"value": EDITED, "note": "", "preview": ""})
    assert response.status_code == 404
    assert client.get(reverse("administration:settings_section", args=[AREA])).status_code == 200
    assert admin_client(make_admin(R.COURSES_MANAGER)).get(url(LEAVE)).status_code == 404


def test_publishing_from_the_screen_sends_the_new_text(make_admin):
    client = admin_client(make_admin(R.SECRETARY))
    response = client.post(url(LEAVE), {"value": EDITED, "note": "Prova inventada"})
    assert response.status_code == 302
    assert leave_email().subject == "Baixa feta"
    assert OutgoingEmail.objects.count() == 1


# --- Revisió de la PR #222 ------------------------------------------------------------------


def test_saving_the_default_text_unchanged_keeps_it_as_default(make_admin):
    default = str(texts.EMAILS[LEAVE].default).replace("\n", "\r\n")  # com l'envia el navegador
    version = business_settings.change(LEAVE, default + "\r\n", make_admin(R.SECRETARY))
    assert version.value == ""
    assert texts.status(LEAVE) == "Text per defecte"


def test_line_endings_are_normalised_on_save(make_admin):
    business_settings.change(LEAVE, "Baixa\r\n\r\nDes del {data}.", make_admin(R.SECRETARY))
    assert business_settings.get(LEAVE) == "Baixa\n\nDes del {data}."


def test_an_unknown_variable_never_stops_an_email(caplog):
    subject, body = texts._fill("Hola {nom}\nCos {data}", {"data": "1/1/2027"})
    assert (subject, body) == ("Hola {nom}", "Cos 1/1/2027\n")
    assert "nom" in caplog.text


def test_every_default_text_in_every_language_uses_only_its_variables():
    for code, _name in settings.LANGUAGES:
        with translation.override(code):
            for key, entry in texts.EMAILS.items():
                used = set(texts._VAR.findall(str(entry.default)))
                assert used <= set(entry.vars), (code, key, used)
                texts.validate(key, str(entry.default))


def test_a_long_subject_is_rejected_with_a_message(make_admin):
    with pytest.raises(ValidationError, match="200"):
        business_settings.change(LEAVE, "A" * 201 + "\n\nCos {data}", make_admin(R.SECRETARY))
    business_settings.change(LEAVE, "A" * 200 + "\n\nCos {data}", make_admin(R.SECRETARY))


def test_the_email_records_the_language_its_text_is_in():
    subject, _body, language = texts.render_email(
        "baixa-efectiva", {"effective_on": datetime.date(2026, 12, 31)}, "es"
    )
    assert language == "ca"  # cap traducció: el text és el català


def test_a_text_setting_without_an_entry_does_not_break_the_screen(make_admin):
    Setting.objects.create(key=f"{AREA}.no-existeix", module=AREA, value_type="text",
                           initial_value="", max_length=100)  # fmt: skip
    client = admin_client(make_admin(R.SECRETARY))
    assert client.get(reverse("administration:settings_section", args=[AREA])).status_code == 200
    assert client.get(url(f"{AREA}.no-existeix")).status_code == 200


@pytest.mark.parametrize(
    "value", ["Preu\n\nAmb <menys de 50 € n'hi ha prou el {data}.", "A\n\n1 < 2 > 0 {data}"]
)
def test_a_less_than_sign_is_not_html(make_admin, value):
    business_settings.change(LEAVE, value, make_admin(R.SECRETARY))


@pytest.mark.parametrize("value", ["A\n\n<!-- x -->", "A\n\n</p>", "A\n\n<br/>"])
def test_things_that_look_like_tags_are_rejected(make_admin, value):
    with pytest.raises(ValidationError, match="HTML"):
        business_settings.change(LEAVE, value, make_admin(R.SECRETARY))


# --- Part b: la resta de correus (T-M00-08b) --------------------------------------------------


@pytest.mark.parametrize(
    ("downgrade", "subject_part", "body_part"),
    [
        ("", "es renova", "demana-ho a «Canvi de tipus»"),
        ("accepted", "es renova", "Tens acceptat el pas a simpatitzant"),
        ("pending", "es renova", "Tens una sol·licitud de pas a simpatitzant pendent"),
    ],
)
def test_the_renewal_notice_has_one_text_per_downgrade_state(downgrade, subject_part, body_part):
    context = {"renews_on": datetime.date(2027, 1, 15), "downgrade": downgrade}
    email = mail.queue_email("avis-renovacio", to="anna@example.org", context=context)
    assert subject_part in email.subject
    assert "es renova el 15/01/2027." in email.body_text and body_part in email.body_text


def test_renewal_variants_are_edited_separately(make_admin):
    business_settings.change(
        f"{AREA}.avis-renovacio-pas-acceptat", "Renovació\n\nEl {data} passes a simpatitzant.",
        make_admin(R.SECRETARY),
    )  # fmt: skip
    context = {"renews_on": datetime.date(2027, 1, 15), "downgrade": "accepted"}
    email = mail.queue_email("avis-renovacio", to="anna@example.org", context=context)
    assert email.body_text == "El 15/01/2027 passes a simpatitzant.\n"
    context["downgrade"] = ""
    other = mail.queue_email("avis-renovacio", to="anna@example.org", context=context)
    assert other.subject == "La teva quota del C.R.I.S. es renova d'aquí a poc"


@pytest.mark.parametrize(
    ("template", "subject"),
    [
        ("rebut-sollicitud-alta", "Hem rebut la teva sol·licitud d'alta al C.R.I.S."),
        ("alta-rebutjada", "La teva sol·licitud d'alta al C.R.I.S."),
    ],
)
def test_join_emails_are_editable_and_have_no_variables(template, subject, make_admin):
    assert mail.queue_email(template, to="anna@example.org").subject == subject
    key = f"{AREA}.{template}"
    assert texts.EMAILS[key].vars == {}
    with pytest.raises(ValidationError):
        business_settings.change(key, "Assumpte\n\nHola {nom}", make_admin(R.SECRETARY))
    assert "no té variables" in texts.help_text(key)


def test_any_other_downgrade_state_gets_the_general_renewal_text():
    context = {"renews_on": datetime.date(2027, 1, 15), "downgrade": "un-estat-nou"}
    email = mail.queue_email("avis-renovacio", to="anna@example.org", context=context)
    assert "demana-ho a «Canvi de tipus»" in email.body_text


def _area_migration():
    from importlib import import_module

    from django.apps import apps as django_apps

    return import_module("apps.core.migrations.0050_text_areas"), django_apps


def test_the_area_migration_reverse_keeps_versions_and_the_matrix_history(make_admin):
    migration, django_apps = _area_migration()
    business_settings.change(f"{AREA}.alta-rebutjada", "Rebuig\n\nCos.", make_admin(R.SECRETARY))
    versions = PermissionMatrixVersion.objects.count()
    migration.unload(django_apps, None)
    assert SettingVersion.objects.filter(setting__key="texts.alta-rebutjada").exists()
    assert not Setting.objects.filter(module=AREA).exists()
    admin = RolePermission.objects.get(role__code=R.ADMINISTRATOR, permission_code=OLD_CODE)
    assert admin.scope == "read"
    assert PermissionMatrixVersion.objects.count() == versions + 1  # la història només creix
    migration.load(django_apps, None)
    assert SettingVersion.objects.filter(setting__key=f"{AREA}.alta-rebutjada").exists()
    assert PermissionMatrixVersion.objects.count() == versions + 2
    assert not RolePermission.objects.filter(permission_code=OLD_CODE).exists()


def test_the_area_migration_gives_the_administrator_edit_even_without_a_previous_cell():
    migration, django_apps = _area_migration()
    migration.unload(django_apps, None)
    RolePermission.objects.filter(role__code=R.ADMINISTRATOR, permission_code=OLD_CODE).delete()
    # Una cel·la nova que ja hi era no trenca la restricció d'unicitat.
    RolePermission.objects.create(
        role=Role.objects.get(code=R.SECRETARY), permission_code=CODE, scope="read"
    )
    migration.load(django_apps, None)
    cells = dict(
        RolePermission.objects.filter(permission_code=CODE).values_list("role__code", "scope")
    )
    assert cells == {R.ADMINISTRATOR: "all", R.SECRETARY: "all"}
    # Una sola entrada per cel·la a la versió, amb l'abast inicial i el final reals.
    diff = PermissionMatrixVersion.objects.latest("number").diff
    pairs = [(entry["role"], entry["permission"]) for entry in diff]
    assert len(pairs) == len(set(pairs))
    admin = next(e for e in diff if (e["role"], e["permission"]) == (R.ADMINISTRATOR, CODE))
    assert (admin["before"], admin["after"]) == (None, "all")


def test_the_area_migration_only_renames_keys_with_the_section_prefix():
    migration, django_apps = _area_migration()
    migration.unload(django_apps, None)
    Setting.objects.create(key="altra.clau", module="texts", value_type="text", initial_value="")
    migration.load(django_apps, None)
    other = Setting.objects.get(key="altra.clau")
    assert other.module == "texts"
    assert Setting.objects.filter(key=LEAVE, module=AREA).exists()


# --- Àrees de textos (T-M00-08d; 097, CA-M00-08.4; P-380) -------------------------------------


@pytest.mark.parametrize(
    "role", [code for code in R.values if code not in ("member", "visitor", "guest")]
)
def test_initial_cell_of_each_role_in_the_members_area(role):
    cell = RolePermission.objects.filter(role__code=role, permission_code=CODE).first()
    expected = {R.ADMINISTRATOR: "all", R.SECRETARY: "all"}.get(role)
    assert (cell.scope if cell else None) == expected


def test_no_cell_of_the_old_section_is_left():
    assert not RolePermission.objects.filter(permission_code=OLD_CODE).exists()


def test_an_email_of_another_area_is_editable(monkeypatch):
    other = texts.EmailText("prova", "Prova", "Assumpte\n\nCos")
    monkeypatch.setitem(texts.EMAILS, "texts-payments.prova", other)
    assert texts.is_editable(Setting(key="texts-payments.prova", module="texts-payments"))
    assert not texts.is_editable(Setting(key="texts-payments.altre", module="texts-payments"))


@pytest.mark.parametrize("role", [R.ADMINISTRATOR, R.SECRETARY])
def test_the_administrator_and_the_secretary_edit_the_members_area(make_admin, role):
    client = admin_client(make_admin(role))
    response = client.post(url(LEAVE), {"value": EDITED, "note": ""})
    assert response.status_code == 302
    assert business_settings.get(LEAVE) == EDITED.rstrip("\n")


def test_without_the_area_every_text_screen_is_not_found(make_admin):
    # CA-M00-08.4: P-391 resolta (propietari, 18/11/2026): «no trobat», com tots els
    # apartats d'ajustos (RN-RP-22).
    client = admin_client(make_admin(R.TREASURER))
    assert client.get(reverse("administration:settings_section", args=[AREA])).status_code == 404
    assert client.get(url(LEAVE)).status_code == 404
    assert client.post(url(LEAVE), {"value": EDITED, "note": ""}).status_code == 404
    assert not SettingVersion.objects.exists()


def test_the_settings_index_lists_only_the_areas_of_the_user(make_admin):
    index = reverse("administration:settings")
    assert (
        "Textos dels correus i de l&#x27;ajuda: socis"
        in admin_client(make_admin(R.SECRETARY)).get(index).content.decode()
    )
    html = admin_client(make_admin(R.TREASURER)).get(index).content.decode()
    assert "Textos dels correus" not in html


# --- Variables obligatòries (T-M00-08c; 097, CA-M00-08.2) -------------------------------------


@pytest.mark.parametrize(
    ("key", "value", "missing"),
    [
        (DUE, "Quota\n\nLa teva quota venç el {data}.", "{import}"),
        (OVERDUE, "Quota\n\nDeus {import}.", "{data}"),
        (LEAVE, "Baixa\n\nJa no ets soci.", "{data}"),
        (f"{AREA}.avis-renovacio", "Renovació\n\nAviat es renova.", "{data}"),
    ],
)
def test_a_text_without_a_required_variable_is_rejected_and_says_which(
    make_admin, key, value, missing
):
    with pytest.raises(ValidationError, match=re.escape(missing)):
        business_settings.change(key, value, make_admin(R.SECRETARY))
    assert not SettingVersion.objects.filter(setting__key=key).exists()


def test_every_required_variable_is_declared_and_in_the_default_text():
    for key, entry in texts.EMAILS.items():
        assert set(entry.required) <= set(entry.vars), key
        assert all(f"{{{name}}}" in str(entry.default) for name in entry.required), key
    assert texts.EMAILS[DUE].required == ("import", "data")


def test_the_help_text_says_which_variables_are_required():
    assert "obligatòries: {import}, {data}" in texts.help_text(DUE)


def test_an_email_without_required_variables_accepts_any_text(make_admin):
    business_settings.change(
        f"{AREA}.alta-rebutjada", "Alta\n\nNo s'ha aprovat.", make_admin(R.SECRETARY)
    )


# --- Textos d'ajuda de les pantalles (T-M00-08e) ---------------------------------------------

HELP = f"{AREA}.ajuda-perfil-nom"


def test_every_help_text_has_its_setting_and_a_valid_default_without_variables():
    # CA-M00-08.5: una ajuda no té cap variable, ni de l'IBAN ni de cap altra dada.
    for key, entry in texts.HELP.items():
        setting = Setting.objects.get(key=key)  # el crea `core/0051`
        assert (setting.module, setting.value_type, setting.initial_value) == (AREA, "text", "")
        texts.validate(key, str(entry.default))
        assert "{" not in str(entry.default) and texts.current(key) == str(entry.default)


@pytest.mark.parametrize(
    "value", ["Adreça't a {nom}", "Pregunta-ho {{ a }}", "Vés a <a href='x'>la secretaria</a>"]
)
def test_a_help_text_with_a_variable_or_html_is_rejected_and_nothing_is_saved(make_admin, value):
    # CA-M00-08.1: les ajudes no tenen variables; CA-M00-08.2 no s'hi aplica (cap obligatòria).
    with pytest.raises(ValidationError):
        business_settings.change(HELP, value, make_admin(R.SECRETARY))
    assert not SettingVersion.objects.filter(setting__key=HELP).exists()


def test_help_text_preview_shows_the_question_and_saves_nothing(make_admin):
    client = admin_client(make_admin(R.SECRETARY))
    page = client.get(url(HELP)).content.decode()
    assert "Ajuda d&#x27;«El meu perfil»: Com canvio el nom" in page
    response = client.post(url(HELP), {"value": "Truca a la secretaria & junta", "preview": ""})
    html = response.content.decode()
    assert "Vista prèvia amb dades inventades" in html  # CA-M00-08.3: sense cap dada real
    assert "Com canvio el nom o el document?" in html
    assert "Truca a la secretaria &amp; junta" in html
    assert not SettingVersion.objects.exists()


def test_help_text_read_only_and_without_permission(make_admin):
    # CA-M00-08.4, amb «no trobat» (P-391).
    reader = admin_client(read_only_treasurer(make_admin))
    assert reader.get(url(HELP)).status_code == 200
    assert reader.post(url(HELP), {"value": "Text inventat", "note": ""}).status_code == 404
    other = admin_client(make_admin(R.COURSES_MANAGER))
    assert other.get(url(HELP)).status_code == 404
    assert not SettingVersion.objects.exists()


@pytest.mark.parametrize("back", ["", "  \r\n "])
def test_going_back_to_the_default_help_text_leaves_a_version(make_admin, back):
    # CA-M00-08.6: una ajuda en blanc també torna al text per defecte.
    secretary = make_admin(R.SECRETARY)
    business_settings.change(HELP, "Truca a la secretaria.", secretary)
    version = business_settings.change(HELP, back, secretary)
    assert (version.previous_value, version.value) == ("Truca a la secretaria.", "")
    assert texts.current(HELP) == str(texts.HELP[HELP].default)
    assert SettingVersion.objects.filter(setting__key=HELP).count() == 2
