"""Exportació RGPD amb les notes de l'administració revisades (T-M01-22c; 085, A-1, opció C;
P-416): darrere de l'interruptor apagat; qui té M11 amb edició les revisa, en pot deixar fora
amb motiu i, amb la contrasenya i el codi, prepara l'exportació. Només dades inventades."""

import json

import pyotp
import pytest
from django.core.files.storage import storages
from django.http import Http404
from django.urls import reverse

from apps.accounts import totp
from apps.accounts.security import AREA_ADMIN
from apps.core import charges, privacy
from apps.core.models import AuditEntry, Charge, Department, PrivateFile
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

PAGE = "administration:gdpr_notes_export"
NOTE = "Anul·lada per un error de l'oficina (nota inventada)."


@pytest.fixture
def on(settings):
    settings.GDPR_ADMIN_NOTES_EXPORT_ENABLED = True


@pytest.fixture
def handler(make_admin):  # noqa: F811
    account = make_admin("administrator")
    account.set_password(PASSWORD)
    account.save()
    return account


@pytest.fixture
def person(personal_account, handler):
    """La persona del compte personal, amb un càrrec anul·lat amb un motiu (una nota)."""
    charge = charges.create_charge(
        personal_account.person,
        kind=Charge.Kind.FEE,
        amount_cents=9000,
        concept="Quota inventada",
        department=Department.objects.get(name="General"),
        origin="members",
        by=handler,
    )
    charges.cancel(charge, NOTE, by=handler)
    return personal_account.person


def content(file: PrivateFile) -> dict:
    with storages["private"].open(file.storage_key, "rb") as handle:
        return json.loads(handle.read())


def form_data(account, **extra):
    code = pyotp.TOTP(totp.secret_of(account.totp_device)).now()
    return {"password": PASSWORD, "code": code, **extra}


def test_the_notes_are_collected_by_date(person):
    notes = privacy.admin_notes(person)
    assert [n["text"] for n in notes] == [NOTE]
    assert notes[0]["key"].startswith("core.charge.")


def test_the_usual_export_has_no_notes(person, personal_account):
    data = content(privacy.request_export(person, by=personal_account))
    assert "notes_de_l_administracio" not in data
    assert NOTE not in json.dumps(data, ensure_ascii=False)


def test_off_by_default_nothing_is_prepared(person, handler):
    with pytest.raises(Http404):
        privacy.export_with_notes(person, by=handler)


def test_on_the_reviewed_notes_go_to_the_export(on, person, handler):
    data = content(privacy.export_with_notes(person, by=handler))
    assert [n["text"] for n in data["notes_de_l_administracio"]] == [NOTE]
    assert "revisat" in data["nota"]
    entry = AuditEntry.objects.get(action=privacy.NOTES_REVIEWED)
    assert entry.details["included"] == [privacy.admin_notes(person)[0]["key"]]
    assert NOTE not in json.dumps(entry.details, ensure_ascii=False)  # cap text al registre


def test_an_excluded_note_needs_a_reason_and_stays_out(on, person, handler):
    key = privacy.admin_notes(person)[0]["key"]
    with pytest.raises(Exception, match="motiu"):
        privacy.export_with_notes(person, by=handler, excluded={key})
    assert not PrivateFile.objects.filter(owner=person).exists()
    data = content(
        privacy.export_with_notes(person, by=handler, excluded={key}, reason="Parla d'un tercer.")
    )
    assert data["notes_de_l_administracio"] == []
    entry = AuditEntry.objects.get(action=privacy.NOTES_REVIEWED)
    assert entry.details["excluded"] == [key] and entry.reason == "Parla d'un tercer."


def test_an_unknown_key_is_rejected(on, person, handler):
    with pytest.raises(Exception, match="han canviat"):
        privacy.export_with_notes(person, by=handler, excluded={"core.charge.0"}, reason="x")


@pytest.mark.parametrize("role", ["secretary", "treasurer", "president"])
def test_without_m11_not_found(on, person, make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        privacy.export_with_notes(person, by=make_admin(role))


def test_nobody_prepares_their_own(on, make_admin):  # noqa: F811
    account = make_admin("administrator")
    with pytest.raises(Exception, match="pròpia"):
        privacy.export_with_notes(account.person, by=account)


class TestScreen:
    def test_off_the_page_does_not_exist(self, person, handler, login_as):
        client = login_as(handler, AREA_ADMIN)
        assert client.get(reverse(PAGE, args=[person.pk])).status_code == 404

    def test_the_handler_reviews_and_prepares_it(self, on, person, handler, login_as):
        client = login_as(handler, AREA_ADMIN)
        url = reverse(PAGE, args=[person.pk])
        page = client.get(url).content.decode()
        assert "Anul·lada per un error de l" in page and 'name="exclou_0"' in page
        response = client.post(url, form_data(handler))
        assert response.status_code == 302
        export = privacy.live_export(person)
        assert [n["text"] for n in content(export)["notes_de_l_administracio"]] == [NOTE]
        assert "Exportació preparada" in client.get(url).content.decode()

    def test_excluding_without_a_reason_shows_the_error(self, on, person, handler, login_as):
        client = login_as(handler, AREA_ADMIN)
        url = reverse(PAGE, args=[person.pk])
        response = client.post(url, form_data(handler, exclou_0="on"))
        assert response.status_code == 200
        assert "Cal el motiu" in response.content.decode()
        assert privacy.live_export(person) is None

    def test_without_m11_not_found(self, on, person, make_admin, login_as):  # noqa: F811
        client = login_as(make_admin("secretary"), AREA_ADMIN)
        url = reverse(PAGE, args=[person.pk])
        assert client.get(url).status_code == 404
        assert client.post(url, {}).status_code == 404


def test_the_members_module_adds_its_notes_but_not_what_the_person_wrote(personal_account):
    from apps.members.models import MemberRequest, MembershipType

    person = personal_account.person
    for channel, reason in (("web", "Ho escric jo."), ("in_person", "Ho anota la secretaria.")):
        MemberRequest.objects.create(
            kind=MemberRequest.Kind.JOIN,
            person=person,
            requested_type=MembershipType.objects.get(code="full"),
            channel=channel,
            request_reason=reason,
            resolution_reason=f"Resolució ({channel}).",
            status=MemberRequest.Status.REJECTED,
        )
    texts = {n["text"] for n in privacy.admin_notes(person)}
    assert texts == {"Ho anota la secretaria.", "Resolució (web).", "Resolució (in_person)."}
