"""Pantalla per publicar versions dels textos legals (T-M00-08b; M12, spec 00 HU-17, CA-17.2).
Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.core import consents
from apps.core.models import AuditEntry, LegalText, Role, RolePermission
from apps.core.tests.test_guest_links import admin_client

pytestmark = pytest.mark.django_db

R = Role.Code
LIST = reverse("administration:legal_texts")
M12 = consents.PUBLISH_PERMISSION


def detail(kind="privacy"):
    return reverse("administration:legal_text_detail", args=[kind])


@pytest.fixture
def admin(make_admin):
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def privacy_v1(admin):
    return consents.publish_text("privacy", "Política inventada, versió 1.", by=admin)


def test_without_m12_every_screen_is_not_found(make_admin, privacy_v1):
    client = admin_client(make_admin(R.SECRETARY))
    assert client.get(LIST).status_code == 404
    assert client.get(detail()).status_code == 404
    data = {"content": "Nova", "note": "", "publish": "", "reviewed": consents.digest("Nova")}
    assert client.post(detail(), data).status_code == 404
    assert LegalText.objects.count() == 1


def test_list_shows_every_known_kind(admin, privacy_v1):
    html = admin_client(admin).get(LIST).content.decode()
    assert "Política de privacitat" in html and "Condicions de soci" in html
    assert "Encara no publicat" in html  # condicions de soci sense cap versió


def test_unknown_kind_is_not_found(admin):
    assert admin_client(admin).get(detail("no-existeix")).status_code == 404


def test_the_detail_shows_the_text_in_force_to_edit(admin, privacy_v1):
    html = admin_client(admin).get(detail()).content.decode()
    assert "Política inventada, versió 1." in html
    assert "Publica" not in html  # primer, la revisió


def test_review_shows_the_text_as_it_will_appear_and_saves_nothing(admin, privacy_v1):
    response = admin_client(admin).post(detail(), {"content": "Línia 1 & 2\r\n\r\nLínia 3"})
    html = response.content.decode()
    assert "Línia 1 &amp; 2" in html and "Publica la versió 2" in html
    assert f'value="{consents.digest("Línia 1 & 2" + chr(10) * 2 + "Línia 3")}"' in html
    assert LegalText.objects.count() == 1


def test_publishing_the_reviewed_text_creates_the_next_version_with_its_note(admin, privacy_v1):
    content = "Política inventada, versió 2."
    data = {"content": content, "note": "Canvi de prova", "publish": "",
            "reviewed": consents.digest(content, "Canvi de prova")}  # fmt: skip
    response = admin_client(admin).post(detail(), data)
    assert response.status_code == 302
    new = consents.current_text("privacy")
    assert (new.version, new.content, new.note, new.published_by) == (
        2,
        content,
        data["note"],
        admin,
    )
    assert LegalText.objects.get(version=1).content == "Política inventada, versió 1."
    entry = AuditEntry.objects.filter(action=consents.PUBLISHED).latest("id")
    assert entry.reason == "Canvi de prova"


def test_a_text_changed_after_the_review_is_not_published(admin, privacy_v1):
    data = {"content": "Un altre text", "note": "", "publish": "",
            "reviewed": consents.digest("El text revisat")}  # fmt: skip
    response = admin_client(admin).post(detail(), data)
    assert response.status_code == 200
    assert "han canviat" in response.content.decode()
    assert LegalText.objects.count() == 1


@pytest.mark.parametrize("content", ["<p>Hola</p>", "Text <!-- amagat -->"])
def test_html_is_rejected(admin, content):
    with pytest.raises(ValidationError, match="HTML"):
        consents.publish_text("privacy", content, by=admin)
    response = admin_client(admin).post(detail(), {"content": content})
    assert "HTML" in response.content.decode() and "Publica la versió" not in (
        response.content.decode()
    )
    assert not LegalText.objects.exists()


def test_the_settings_index_links_to_the_legal_texts_only_with_m12(admin, make_admin):
    index = reverse("administration:settings")
    assert LIST in admin_client(admin).get(index).content.decode()
    assert LIST not in admin_client(make_admin(R.TREASURER)).get(index).content.decode()


# --- Revisió de la PR #224 ------------------------------------------------------------------


def test_with_read_only_m12_you_review_but_never_publish(make_admin, privacy_v1):
    reader = make_admin(R.SECRETARY)
    RolePermission.objects.create(
        role=Role.objects.get(code=R.SECRETARY), permission_code=M12, scope="read"
    )
    client = admin_client(reader)
    assert client.get(detail()).status_code == 200
    html = client.post(detail(), {"content": "Nova"}).content.decode()
    assert "Publica la versió" not in html
    data = {"content": "Nova", "note": "", "publish": "", "reviewed": consents.digest("Nova")}
    assert client.post(detail(), data).status_code == 404
    with pytest.raises(Http404):
        consents.publish_text("privacy", "Nova", by=reader)
    assert LegalText.objects.count() == 1


def test_next_version_and_history_count_every_language(admin, privacy_v1):
    LegalText.objects.create(kind="privacy", version=2, language="es", content="Traducción.")
    html = admin_client(admin).post(detail(), {"content": "Versió nova"}).content.decode()
    assert "Publica la versió 3" in html
    assert "Traducción." in html and ">es<" in html  # la versió 2 surt a l'historial
    data = {"content": "Versió nova", "note": "", "publish": "",
            "reviewed": consents.digest("Versió nova")}  # fmt: skip
    admin_client(admin).post(detail(), data)
    assert consents.current_text("privacy").version == 3


def test_imported_kinds_are_not_on_the_screen_and_cannot_be_published(admin):
    consents.imported_text("cluber_images", "Text de Cluber inventat.", language="es", by=admin)
    assert "cluber_images" not in admin_client(admin).get(LIST).content.decode()
    assert admin_client(admin).get(detail("cluber_images")).status_code == 404
    with pytest.raises(ValidationError):
        consents.publish_text("cluber_images", "Versió nova", by=admin)
    assert LegalText.objects.filter(kind="cluber_images").count() == 1


def test_the_review_fingerprint_also_covers_the_note(admin, privacy_v1):
    data = {"content": "Nova", "note": "Una altra nota", "publish": "",
            "reviewed": consents.digest("Nova", "La nota revisada")}  # fmt: skip
    response = admin_client(admin).post(detail(), data)
    assert "han canviat" in response.content.decode()
    assert LegalText.objects.count() == 1


def test_error_messages_are_shown_as_errors(admin, privacy_v1, monkeypatch):
    def fail(*args, **kwargs):
        raise ValidationError("Error inventat")

    monkeypatch.setattr(consents, "publish_text", fail)
    data = {"content": "Nova", "note": "", "publish": "", "reviewed": consents.digest("Nova")}
    html = admin_client(admin).post(detail(), data).content.decode()
    assert "avis avis-error" in html and "Error inventat" in html


def test_member_labels_come_from_the_single_list():
    from apps.members.forms import LEGAL_LABELS

    assert all(LEGAL_LABELS[kind] == label for kind, label in consents.KINDS.items())
