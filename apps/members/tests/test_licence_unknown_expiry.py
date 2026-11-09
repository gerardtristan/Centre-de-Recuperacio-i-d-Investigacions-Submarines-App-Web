"""Caducitat desconeguda al registre mínim de llicència (T-M01-34; RN-M01-50, CA-M01-40).

Un registre de Cluber sense caducitat es desa; la fitxa hi diu «caducitat desconeguda» i
`members.licence_record` el torna marcat (`expiry_unknown`) només si no n'hi ha cap amb data.
La marca és neutra: què vol dir per al 02 («pendent de confirmar») no és d'aquí [A validar:
secretaria]. Només dades inventades.
"""

import dataclasses
import datetime

import pytest
from django.urls import reverse

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.models import LicenceRecord
from apps.members.services import LicenceInfo, licence_record, licence_records
from apps.members.tests.test_member_edit import a_member
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db

DETAIL = "administration:member_detail"
ISSUED = datetime.date(2025, 3, 1)
UNKNOWN = "caducitat desconeguda"


def a_record(member, *, expires_on=None, issued_on=ISSUED, source=LicenceRecord.Source.CLUBER):
    record = LicenceRecord(
        member=member,
        licence_type="Anual FECDAS",
        issued_on=issued_on,
        expires_on=expires_on,
        source=source,
    )
    record.full_clean(exclude=["import_batch"])
    record.save()
    return record


class TestSaving:
    def test_cluber_record_without_expiry_is_accepted(self):
        record = a_record(a_member())
        record.refresh_from_db()
        assert (record.source, record.expires_on) == ("cluber", None)


class TestDetail:
    @pytest.mark.parametrize("role", ["secretary", "administrator", "treasurer"])
    def test_detail_says_unknown_expiry(self, make_admin, role):  # noqa: F811
        member = a_member()
        a_record(member)
        page = admin_client(make_admin(role)).get(reverse(DETAIL, args=[member.pk]))
        assert UNKNOWN in page.content.decode()

    def test_known_expiry_shows_the_date_not_the_text(self, make_admin):  # noqa: F811
        member = a_member()
        a_record(member, expires_on=datetime.date(2026, 12, 31))
        page = admin_client(make_admin("secretary")).get(reverse(DETAIL, args=[member.pk]))
        page = page.content.decode()
        assert "31/12/2026" in page and UNKNOWN not in page


class TestService:
    def test_marked_unknown_if_no_known_expiry(self):
        member = a_member()
        record = a_record(member)
        result = licence_record(member.person)
        assert result.record_id == record.pk
        assert result.expiry_unknown is True and result.expires_on is None

    def test_known_expiry_wins_and_is_not_marked(self):
        member = a_member()
        a_record(member, issued_on=datetime.date(2026, 6, 1))  # més nou, però sense data
        known = a_record(member, expires_on=datetime.date(2026, 3, 31))
        result = licence_record(member.person)
        assert result.record_id == known.pk
        assert result.expiry_unknown is False

    def test_every_row_of_licence_records_is_marked(self):
        member = a_member()
        unknown = a_record(member)
        known = a_record(member, expires_on=datetime.date(2026, 12, 31))
        marks = {row.record_id: row.expiry_unknown for row in licence_records()}
        assert marks == {unknown.pk: True, known.pk: False}

    def test_mark_is_derived_and_read_only(self):
        # No és un camp: no pot contradir `expires_on` i el contracte de la T-M01-30 no canvia.
        assert "expiry_unknown" not in [f.name for f in dataclasses.fields(LicenceInfo)]
        member = a_member()
        a_record(member)
        result = licence_record(member.person)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.expiry_unknown = False
