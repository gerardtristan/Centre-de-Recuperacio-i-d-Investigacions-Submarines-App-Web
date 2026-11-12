"""Data de naixement declarada i comprovació posterior (decisió 081, punt 16; RN-M01-99; T-M01-35 i
T-M01-18).

- La data declarada s'accepta i té efecte de seguida, també l'exempció de la quota per edat: la
  comprovació no és mai una condició prèvia.
- La secretaria la comprova després amb el document (el d'un menor, el DNI que mostra el seu
  representant legal) i ho marca a la fitxa, amb P5 i C1. No es desa cap còpia del document.
- Si la data canvia, la comprovació deixa de valer.
- Un menor sense document a la fitxa (RN-M01-70) també es pot marcar, després de veure'n el DNI a
  través del representant legal (decisió 082, punt 1; P-73 resolta); no es desa cap document.

Només dades inventades.
"""

from datetime import date
from html import unescape

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.core import persons
from apps.core.models import AuditEntry, PrivateFile
from apps.core.privacy import export_person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import birth_date, cards, member_edit
from apps.members.services import OwnMemberChange
from apps.members.tests.test_roster import DETAIL, LIST, add_fee, admin_client, make_member

CHECK = "administration:member_birth_date_check"
DECLARED = "(declarada, sense comprovar)"
FILTER = "Només els exempts per edat amb la data sense comprovar"
TODAY = date.today()
MINOR_BIRTH = date(TODAY.year - 10, 3, 1)  # exempt per edat (068)


def detail(client, member):
    return unescape(client.get(reverse(DETAIL, args=[member.pk])).content.decode())


@pytest.fixture
def minor(db):
    return make_member(
        610,
        "Lluc",
        "Menor",
        type_code="supporter",
        birth_date=MINOR_BIRTH,
        id_document_type="dni",
        id_document_number="12345678Z",
    )


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin("secretary")


def test_declared_date_gives_the_exemption_at_once_without_any_prior_check(db):
    """El soci declara la data al perfil: l'exempció s'aplica ja, sense esperar la secretaria."""
    member = make_member(611, "Nil", "Declarat", type_code="supporter")
    assert birth_date.complete_own(member.person, MINOR_BIRTH, by=None)
    member.person.refresh_from_db()
    assert member.person.birth_date_checked_at is None
    assert cards.is_exempt(cards.load_member(member.pk))


def test_detail_says_declared_and_offers_the_check_to_the_secretary(minor, secretary):
    text = detail(admin_client(secretary), minor)
    assert DECLARED in text
    assert "Marca la data com a comprovada" in text
    assert "No se n'ha desat cap còpia." in text


def test_treasurer_sees_neither_the_state_nor_the_action(minor, make_admin):  # noqa: F811
    text = detail(admin_client(make_admin("treasurer")), minor)
    assert DECLARED not in text and "comprovada" not in text


def test_secretary_marks_it_checked_without_storing_any_document(minor, secretary):
    client = admin_client(secretary)
    response = client.post(reverse(CHECK, args=[minor.pk]), {"confirmo": "1"})
    assert response.status_code in (302, 303)
    minor.person.refresh_from_db()
    assert minor.person.birth_date_checked_at is not None
    entry = AuditEntry.objects.get(action=persons.BIRTH_DATE_CHECKED)
    assert entry.actor_account == secretary and entry.target_id == str(minor.person.pk)
    assert entry.details == {}  # 082: només qui i quan
    assert MINOR_BIRTH.isoformat() not in str(entry.old_value) + str(entry.new_value)
    assert not PrivateFile.objects.exists()
    text = detail(client, minor)
    assert f"(comprovada el {minor.person.birth_date_checked_at:%d/%m/%Y})" in text
    assert "Marca la data com a comprovada" not in text
    # L'exempció no ha canviat: ja hi era abans de comprovar-la.
    assert cards.is_exempt(cards.load_member(minor.pk))


def test_without_the_confirmation_nothing_changes(minor, secretary):
    client = admin_client(secretary)
    client.post(reverse(CHECK, args=[minor.pk]), {})
    minor.person.refresh_from_db()
    assert minor.person.birth_date_checked_at is None
    assert not AuditEntry.objects.filter(action=persons.BIRTH_DATE_CHECKED).exists()


def test_without_c1_the_service_refuses_it(minor, make_admin):  # noqa: F811
    with pytest.raises(ValidationError):
        birth_date.mark_checked(minor, by=make_admin("treasurer"), confirmed=True)
    minor.person.refresh_from_db()
    assert minor.person.birth_date_checked_at is None


def test_own_member_cannot_be_checked(make_admin):  # noqa: F811
    member = make_member(
        612, birth_date=MINOR_BIRTH, id_document_type="dni", id_document_number="12345678Z"
    )
    own = make_admin("secretary", person=member.person, username="secretaria.propia")
    with pytest.raises(OwnMemberChange):
        birth_date.mark_checked(member, by=own, confirmed=True)


def test_a_new_date_needs_a_new_check(minor, secretary):
    birth_date.mark_checked(minor, by=secretary, confirmed=True)
    member_edit.edit_member_data(
        minor, by=secretary, fields={"birth_date": date(TODAY.year - 9, 3, 1)}
    )
    minor.person.refresh_from_db()
    assert minor.person.birth_date_checked_at is None
    entry = AuditEntry.objects.filter(action=persons.BIRTH_DATE_SET).latest("pk")
    assert entry.details["check_reset"] is True


def test_082_minor_without_document_on_file_can_be_checked_without_storing_anything(db, secretary):
    """Decisió 082, punt 1 (P-73): la secretaria marca la data d'un menor sense document a la
    fitxa després de veure'n el DNI a través del representant legal. No es desa cap document ni
    cap còpia; només qui ho ha comprovat i quan. RN-M01-70 no canvia: el document continua buit."""
    member = make_member(613, "Pol", "Senedoc", type_code="supporter", birth_date=MINOR_BIRTH)
    client = admin_client(secretary)
    text = detail(client, member)
    assert "Marca la data com a comprovada" in text
    assert "pendent de decidir" not in text
    client.post(reverse(CHECK, args=[member.pk]), {"confirmo": "1"})
    member.person.refresh_from_db()
    assert member.person.birth_date_checked_at is not None
    assert member.person.id_document_number == "" and member.person.id_document_type == ""
    entry = AuditEntry.objects.get(action=persons.BIRTH_DATE_CHECKED)
    assert entry.actor_account == secretary and entry.created_at is not None
    assert entry.details == {} and entry.reason == ""
    assert not PrivateFile.objects.exists()
    assert cards.is_exempt(cards.load_member(member.pk))


def test_secretary_list_of_exempt_minors_with_the_date_unchecked(minor, secretary):
    checked = make_member(
        614,
        "Ona",
        "Comprovada",
        birth_date=MINOR_BIRTH,
        id_document_type="dni",
        id_document_number="00000000T",
    )
    birth_date.mark_checked(checked, by=secretary, confirmed=True)
    paying = make_member(615, "Pau", "Quota", birth_date=MINOR_BIRTH)
    add_fee(paying)
    make_member(616, "Marta", "Adulta", birth_date=date(1988, 10, 8))
    client = admin_client(secretary)
    text = unescape(client.get(reverse(LIST), {"sense_comprovar": "on"}).content.decode())
    assert FILTER in text
    assert "Lluc Menor" in text
    for name in ("Ona Comprovada", "Pau Quota", "Marta Adulta"):
        assert name not in text


def test_export_of_personal_data_says_when_it_was_checked(minor, secretary):
    birth_date.mark_checked(minor, by=secretary, confirmed=True)
    minor.person.refresh_from_db()
    data = export_person(minor.person)["persona"]
    assert data["data_de_naixement_comprovada_el"] == minor.person.birth_date_checked_at
