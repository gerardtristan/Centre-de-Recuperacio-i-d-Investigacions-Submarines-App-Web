"""Textos editables dels correus (T-M00-08; 085, S-1 i S-3): text per defecte, versió publicada
amb el valor anterior, vista prèvia, permís i seguretat del text (cap plantilla des de la base
de dades, cap HTML). Només dades inventades."""

import datetime

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import translation

from apps.core import business_settings, mail, texts
from apps.core.models import AuditEntry, OutgoingEmail, Role, Setting, SettingVersion
from apps.core.tests.test_guest_links import admin_client

pytestmark = pytest.mark.django_db

R = Role.Code
LEAVE = "texts.baixa-efectiva"
DUE = "texts.recordatori-quota"
OVERDUE = "texts.recordatori-quota-vencuda"
EDITED = "Baixa feta\n\nHola,\n\nDes del {data} ja no ets soci.\n"


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
    return reverse(f"administration:{name}", args=["texts", key])


# --- Registre i text per defecte ------------------------------------------------------------


def test_every_editable_email_has_its_setting_priority_and_a_valid_default():
    for key, entry in texts.EMAILS.items():
        setting = Setting.objects.get(key=key)  # el crea `core/0047`
        assert (setting.module, setting.value_type, setting.initial_value) == ("texts", "text", "")
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
    business_settings.change(OVERDUE, "Impagada\n\nPaga {import}.", make_admin(R.SECRETARY))
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
    business_settings.change(DUE, "Quota\n\nImport: {import}", make_admin(R.SECRETARY))
    context = {"due_on": datetime.date(2026, 12, 15), "amount": "{data} {{ 7|add:1 }}"}
    email = mail.queue_email("recordatori-quota", to="anna@example.org", context=context)
    assert email.body_text == "Import: {data} {{ 7|add:1 }}\n"


def test_the_subject_is_a_single_line():
    subject, body = texts.preview(LEAVE, "Assumpte   amb  espais\nCos")
    assert (subject, body) == ("Assumpte amb espais", "Cos\n")


# --- Permís ---------------------------------------------------------------------------------


def test_only_the_section_editor_publishes(make_admin):
    administrator = make_admin(R.ADMINISTRATOR)  # «Cons.»
    with pytest.raises(Http404):
        business_settings.change(LEAVE, EDITED, administrator)
    assert AuditEntry.objects.filter(action=business_settings.ACTION_DENIED, field=LEAVE).exists()
    with pytest.raises(Http404):
        business_settings.change(LEAVE, EDITED, make_admin(R.TREASURER))
    assert not SettingVersion.objects.exists()


# --- Pantalla -------------------------------------------------------------------------------


def test_screen_shows_the_default_text_to_edit_and_the_allowed_variables(make_admin):
    client = admin_client(make_admin(R.SECRETARY))
    listing = client.get(reverse("administration:settings_section", args=["texts"]))
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
    client = admin_client(make_admin(R.ADMINISTRATOR))
    assert client.get(url(LEAVE)).status_code == 200  # «Cons.»: veu el text i l'historial
    response = client.post(url(LEAVE), {"value": EDITED, "note": "", "preview": ""})
    assert response.status_code == 404
    assert client.get(reverse("administration:settings_section", args=["texts"])).status_code == 200
    assert admin_client(make_admin(R.TREASURER)).get(url(LEAVE)).status_code == 404


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
        business_settings.change(LEAVE, "A" * 201 + "\n\nCos", make_admin(R.SECRETARY))
    business_settings.change(LEAVE, "A" * 200 + "\n\nCos", make_admin(R.SECRETARY))


def test_the_email_records_the_language_its_text_is_in():
    subject, _body, language = texts.render_email(
        "baixa-efectiva", {"effective_on": datetime.date(2026, 12, 31)}, "es"
    )
    assert language == "ca"  # cap traducció: el text és el català


def test_a_text_setting_without_an_entry_does_not_break_the_screen(make_admin):
    Setting.objects.create(key="texts.no-existeix", module="texts", value_type="text",
                           initial_value="", max_length=100)  # fmt: skip
    client = admin_client(make_admin(R.SECRETARY))
    assert client.get(reverse("administration:settings_section", args=["texts"])).status_code == 200
    assert client.get(url("texts.no-existeix")).status_code == 200


@pytest.mark.parametrize("value", ["Preu\n\nAmb <menys de 50 € n'hi ha prou.", "A\n\n1 < 2 > 0"])
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
        "texts.avis-renovacio-pas-acceptat", "Renovació\n\nEl {data} passes a simpatitzant.",
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
    key = f"texts.{template}"
    assert texts.EMAILS[key].vars == {}
    with pytest.raises(ValidationError):
        business_settings.change(key, "Assumpte\n\nHola {nom}", make_admin(R.SECRETARY))
    assert "no té variables" in texts.help_text(key)


def test_any_other_downgrade_state_gets_the_general_renewal_text():
    context = {"renews_on": datetime.date(2027, 1, 15), "downgrade": "un-estat-nou"}
    email = mail.queue_email("avis-renovacio", to="anna@example.org", context=context)
    assert "demana-ho a «Canvi de tipus»" in email.body_text


def test_text_settings_reverse_migration_keeps_versions(make_admin):
    from importlib import import_module

    from django.apps import apps as django_apps

    migration = import_module("apps.core.migrations.0049_legal_text_note_and_more_texts")
    business_settings.change("texts.alta-rebutjada", "Rebuig\n\nCos.", make_admin(R.SECRETARY))
    migration.unload(django_apps, None)
    assert SettingVersion.objects.filter(setting__key="texts.alta-rebutjada").exists()
    assert not Setting.objects.filter(key="texts.rebut-sollicitud-alta").exists()
