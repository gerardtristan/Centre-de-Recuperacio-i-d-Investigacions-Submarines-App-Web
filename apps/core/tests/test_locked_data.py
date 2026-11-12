"""Dades bloquejades i la seva consulta (T-M00-04; M13; decisió 028, punt 2; 058, punt 7; spec 00,
CA-19.3 i RN-91). Només dades inventades.
"""

import datetime
import json
import re

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from apps.core import crypto, locked_data, privacy
from apps.core.models import AuditEntry, Charge, LockedIdentity, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.members.tests.test_cards import paid_member
from apps.members.tests.test_privacy import leaks

pytestmark = pytest.mark.django_db

LIST, DETAIL = "administration:locked_data", "administration:locked_data_detail"
REASON = "Requeriment de la gestoria per a l'exercici 2026 (prova inventada)"


def identity_of(person):
    return {
        "nom": person.first_name,
        "cognoms": person.last_name,
        "document": person.id_document_number,
    }


@pytest.fixture
def blocked(make_admin):  # noqa: F811
    """Un soci amb una quota pagada, anonimitzat: la seva identitat queda bloquejada."""
    member = paid_member()
    Person.objects.filter(pk=member.person_id).update(
        last_name="Bloquejada Inventada", id_document_type="dni", id_document_number="12345678Z"
    )
    person = Person.objects.get(pk=member.person_id)
    original = identity_of(person)
    privacy.anonymise_person(person, by=make_admin("administrator"))
    return LockedIdentity.objects.get(person=person), original


class TestLock:
    def test_ca_19_3_identity_on_economic_records_is_kept_encrypted(self, blocked):
        locked, original = blocked
        payload = json.loads(crypto.decrypt(locked.payload_encrypted))
        assert payload["first_name"] == original["nom"]
        assert payload["last_name"] == original["cognoms"]
        assert (payload["id_document_type"], payload["id_document_number"]) == ("dni", "12345678Z")
        assert set(payload) == set(locked_data.FIELDS)  # cap correu, telèfon, adreça ni data
        # En clar no queda enlloc: ni a la persona ni a cap altra taula (CA-19.6).
        assert leaks(original) == []

    def test_the_lock_is_in_the_audit_log_without_values(self, blocked):
        locked, original = blocked
        entry = AuditEntry.objects.get(action=locked_data.LOCKED)
        assert entry.details == {"fields": list(locked_data.FIELDS)}
        row = str(AuditEntry.objects.values().get(pk=entry.pk))
        assert original["cognoms"] not in row and "12345678Z" not in row

    def test_a_person_without_economic_records_keeps_nothing(self, make_admin):  # noqa: F811
        person = Person.objects.create(
            first_name="Sense", last_name="Càrrecs Inventada", origin=Person.Origin.WEB
        )
        privacy.anonymise_person(person, by=make_admin("administrator"))
        assert not LockedIdentity.objects.exists()
        assert not AuditEntry.objects.filter(action=locked_data.LOCKED).exists()


class TestConsult:
    @pytest.mark.parametrize("role", ["treasurer", "administrator"])
    def test_rn_91_m13_with_a_reason_returns_the_data_and_logs_it(self, blocked, make_admin, role):  # noqa: F811
        locked, original = blocked
        account = make_admin(role)
        result = locked_data.consult(locked, by=account, reason=REASON)
        assert result["identity"]["last_name"] == original["cognoms"]
        assert len(result["records"]) == 1
        entry = AuditEntry.objects.get(action=locked_data.VIEWED)
        assert (entry.actor_account, entry.reason) == (account, REASON)
        assert "12345678Z" not in str(AuditEntry.objects.values().get(pk=entry.pk))

    @pytest.mark.parametrize("role", ["secretary", "president", "board"])
    def test_rn_91_without_m13_nothing_is_returned(self, blocked, make_admin, role):  # noqa: F811
        locked, _original = blocked
        with pytest.raises(PermissionDenied):
            locked_data.consult(locked, by=make_admin(role), reason=REASON)
        assert not AuditEntry.objects.filter(action=locked_data.VIEWED).exists()

    def test_rn_91_a_reason_is_required(self, blocked, make_admin):  # noqa: F811
        locked, _original = blocked
        with pytest.raises(ValidationError):
            locked_data.consult(locked, by=make_admin("treasurer"), reason="   ")
        assert not AuditEntry.objects.filter(action=locked_data.VIEWED).exists()

    def test_m13_is_protected_and_not_editable_from_the_matrix(self):
        from apps.core.permission_catalog import CATALOG

        perm = CATALOG[locked_data.PERMISSION]
        assert perm.protected
        assert set(perm.initial) == {"treasurer", "administrator"}


class TestScreens:
    def test_screens_need_m13(self, blocked, make_admin):  # noqa: F811
        locked, _original = blocked
        for role in ("secretary", "president", "board"):
            client = admin_client(make_admin(role))
            assert client.get(reverse(LIST)).status_code == 404
            assert client.get(reverse(DETAIL, args=[locked.pk])).status_code == 404
            response = client.post(reverse(DETAIL, args=[locked.pk]), {"reason": REASON})
            assert response.status_code == 404
        assert not AuditEntry.objects.filter(action=locked_data.VIEWED).exists()

    def test_list_and_get_show_only_the_anonymous_reference(self, blocked, make_admin):  # noqa: F811
        locked, original = blocked
        client = admin_client(make_admin("treasurer"))
        for response in (
            client.get(reverse(LIST)),
            client.get(reverse(DETAIL, args=[locked.pk])),
        ):
            text = response.content.decode()
            assert response.status_code == 200
            assert locked.person.anonymous_ref in text
            assert original["cognoms"] not in text and "12345678Z" not in text
        assert not AuditEntry.objects.filter(action=locked_data.VIEWED).exists()

    def test_post_without_reason_shows_nothing(self, blocked, make_admin):  # noqa: F811
        locked, original = blocked
        client = admin_client(make_admin("treasurer"))
        response = client.post(reverse(DETAIL, args=[locked.pk]), {"reason": ""})
        assert "Escriu el motiu de la consulta." in response.content.decode()
        assert original["cognoms"] not in response.content.decode()

    def test_post_with_reason_shows_the_data_without_cache(self, blocked, make_admin):  # noqa: F811
        locked, original = blocked
        client = admin_client(make_admin("treasurer"))
        response = client.post(reverse(DETAIL, args=[locked.pk]), {"reason": REASON})
        text = response.content.decode()
        assert original["cognoms"] in text and "12345678Z" in text
        assert "no-store" in response["Cache-Control"] or "no-cache" in response["Cache-Control"]
        assert AuditEntry.objects.filter(action=locked_data.VIEWED).count() == 1

    def test_ca_19_3_blocked_data_is_not_shown_anywhere_else(self, blocked, make_admin):  # noqa: F811
        """Cap llistat, cerca, fitxa, revisió de quotes, registre ni exportació no mostra la
        identitat bloquejada: només M13 amb motiu."""
        _locked, original = blocked
        client = admin_client(make_admin("administrator"))
        pages = [
            reverse("administration:members_list"),
            reverse("administration:members_list") + "?q=" + original["cognoms"].split()[0],
            reverse("administration:members_list") + "?q=12345678Z",
            reverse("administration:fees"),
            reverse("administration:guest_links"),
            reverse("administration:audit_log"),
            reverse("administration:gdpr_requests"),
        ]
        for url in pages:
            # El camp de cerca torna a mostrar el que s'ha escrit: no compta com a resultat.
            text = re.sub(r'value="[^"]*"', "", client.get(url).content.decode())
            for value in (original["cognoms"], "12345678Z"):
                assert value not in text, url


class TestRetention085:
    """CA-19.5 i RN-90, amb el termini de la decisió 085 (G-1): les dades bloquejades es
    destrueixen quan han passat 6 anys des del tancament de l'exercici de l'últim registre
    econòmic de la persona. Els registres econòmics no s'esborren mai."""

    def test_the_term_is_six_years_after_the_year_of_the_last_economic_record(self, blocked):
        locked, _original = blocked
        year = locked_data.last_record_date(locked).year
        assert locked_data.retention_years() == 6
        assert locked_data.expires_on(locked) == datetime.date(year + 6, 12, 31)

    def test_ca_19_5_expired_data_is_destroyed_and_recorded_with_the_reference(self, blocked):
        locked, original = blocked
        person = locked.person
        charges_before = Charge.objects.filter(person=person).count()
        limit = locked_data.expires_on(locked)

        assert locked_data.destroy_expired(today=limit) == 0  # l'últim dia encara hi són
        assert LockedIdentity.objects.filter(pk=locked.pk).exists()

        assert locked_data.destroy_expired(today=limit + datetime.timedelta(days=1)) == 1
        assert not LockedIdentity.objects.filter(pk=locked.pk).exists()
        # Els registres econòmics continuen, sense cap dada personal.
        assert Charge.objects.filter(person=person).count() == charges_before
        entry = AuditEntry.objects.get(action=locked_data.DESTROYED)
        assert entry.actor_kind == AuditEntry.ActorKind.SYSTEM
        assert entry.target_id == str(person.pk)
        assert entry.details == {
            "reference": person.anonymous_ref,
            "retention_years": 6,
            "last_record_year": limit.year - 6,
        }
        assert not leaks(original)
        # Idempotent: tornar-la a executar no fa res.
        assert locked_data.destroy_expired(today=limit + datetime.timedelta(days=2)) == 0

    def test_the_term_is_configurable(self, blocked, settings):
        locked, _original = blocked
        year = locked_data.last_record_date(locked).year
        settings.LOCKED_DATA_RETENTION_YEARS = 10
        assert locked_data.expires_on(locked).year == year + 10

    def test_the_daily_task_is_registered(self):
        from apps.core import tasks

        assert tasks.destroy_expired_locked_data.name == "core.destroy_expired_locked_data"
