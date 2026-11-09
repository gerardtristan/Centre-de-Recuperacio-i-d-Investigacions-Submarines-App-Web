"""Alta de menors, tipus segons l'edat, previsió de la quota i acceptacions a la sol·licitud
(T-M01-13; 068, 069 punt 1 i 070; RN-M01-62 a RN-M01-69, CA-M01-01 i CA-M01-56 a CA-M01-62).

El dia «d'avui» es fixa substituint `fee_rules.local_today`: el formulari i el servei fan servir
el mateix dia. Només dades inventades (DNI de prova amb la lletra correcta, correus a
example.org)."""

from datetime import UTC, date, datetime

import pytest
from django.db import IntegrityError, connection, transaction
from django.db.utils import ProgrammingError
from django.test import Client
from django.urls import reverse

from apps.accounts.models import EmailLinkRequest
from apps.core.models import AppendOnlyError, AuditEntry, Charge, Consent, Person
from apps.core.permissions import has_perm
from apps.core.persons import age_on
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.views.audit import _field_permission
from apps.members import fee_rules
from apps.members.models import (
    AnnualFee,
    JoinAcceptance,
    Member,
    MemberCard,
    MemberRequest,
    MembershipNumberCounter,
    MembershipType,
)
from apps.members.tests.test_join import (  # noqa: F401 (fixtures secretary i texts)
    CREATED,
    IN_PERSON,
    PUBLIC,
    admin_client,
    form_data,
    secretary,
    submit,
    texts,
)

GUARDIAN = {
    "guardian_first_name": "Marta",
    "guardian_last_name": "Dorada Puig",
    "guardian_id_document": "00000002W",
    "guardian_authorization": "on",
}
TODAY = date(2026, 11, 6)
# Textos legals publicats per a totes les proves del mòdul (fixture de test_join).
pytestmark = pytest.mark.usefixtures("texts")


@pytest.fixture
def today(monkeypatch):
    def set_today(value):
        monkeypatch.setattr(fee_rules, "local_today", lambda now=None: value)

    set_today(TODAY)
    return set_today


def full_type():
    return MembershipType.objects.get(code="full").pk


def nothing_created():
    return (
        MemberRequest.objects.count() == 0
        and JoinAcceptance.objects.count() == 0
        and not AuditEntry.objects.filter(action=CREATED).exists()
        and not EmailLinkRequest.objects.exists()
    )


def preview(client=None, url=None, **overrides):
    data = form_data(**overrides)
    data["vista_previa"] = "1"
    return (client or Client()).post(url or reverse(PUBLIC), data).content.decode()


def type_fieldset(html: str) -> str:
    return html.split('id="part-variable"')[1].split("</fieldset>")[0]


# --- Regles pures ------------------------------------------------------------------------------
class TestRules:
    @pytest.mark.parametrize(
        ("birth", "on", "age"),
        [
            (date(2013, 3, 10), date(2027, 3, 9), 13),
            (date(2013, 3, 10), date(2027, 3, 10), 14),  # el dia que en fa 14
            (date(2008, 11, 7), date(2026, 11, 6), 17),
            (date(2008, 11, 6), date(2026, 11, 6), 18),  # el dia que en fa 18
            (date(2012, 2, 29), date(2026, 2, 28), 13),
            (date(2012, 2, 29), date(2026, 3, 1), 14),
        ],
    )
    def test_age_on_birthdays(self, birth, on, age):
        assert age_on(birth, on) == age

    def test_local_date_is_barcelona(self):
        # 31/12 a les 23:30 UTC ja és l'1 de gener a Barcelona; a les 22:30 UTC, encara no.
        new_year = datetime(2026, 12, 31, 23, 30, tzinfo=UTC)
        assert fee_rules.local_today(new_year) == date(2027, 1, 1)
        new_year_eve = datetime(2026, 12, 31, 22, 30, tzinfo=UTC)
        assert fee_rules.local_today(new_year_eve) == date(2026, 12, 31)

    def test_first_fee_year_is_the_year_after_turning_14(self):
        # Exemple confirmat: 14 anys el 10/03/2027, comença a pagar l'01/01/2028.
        assert fee_rules.first_fee_year(date(2013, 3, 10)) == 2028

    def test_may_choose(self):
        assert fee_rules.may_choose("supporter", 5)
        assert not fee_rules.may_choose("full", 13)
        assert fee_rules.may_choose("full", 14)

    @pytest.mark.parametrize(
        ("birth", "on", "expected"),
        [
            # Menor de 14: exempt fins al 31/12 de l'any en què en fa 14 (068).
            (date(2013, 3, 10), date(2026, 11, 6), ("exempt", None, 2027)),
            # Ja té 14 anys aquest any però encara no paga: exempt fins al 31/12/2027.
            (date(2013, 3, 10), date(2027, 6, 15), ("exempt", None, 2027)),
            (date(2013, 3, 10), date(2027, 12, 31), ("exempt", None, 2027)),
            # L'1 de gener següent ja paga, i la quota és íntegra (070).
            (date(2013, 3, 10), date(2028, 1, 1), ("full", 9000, None)),
            # Adult: quota íntegra en qualsevol mes, sense prorrata ni regla de novembre (070).
            (date(1990, 5, 20), date(2026, 1, 15), ("full", 9000, None)),
            (date(1990, 5, 20), date(2026, 10, 31), ("full", 9000, None)),
            (date(1990, 5, 20), date(2026, 11, 1), ("full", 9000, None)),
            (date(1990, 5, 20), date(2026, 12, 31), ("full", 9000, None)),
        ],
    )
    def test_fee_preview(self, birth, on, expected):
        p = fee_rules.fee_preview(birth, 9000, on)
        assert (p.kind, p.cents, p.until_year) == expected


# --- Data de naixement (RN-M01-52, CA-M01-41) --------------------------------------------------
class TestBirthDate:
    @pytest.mark.parametrize("value", ["2026-11-07", "2030-01-01"])  # posteriors a avui
    def test_future_dates_are_rejected(self, today, value):
        html = submit(birth_date=value).content.decode()
        assert "no pot ser posterior a avui" in html
        assert nothing_created()

    def test_implausible_date_is_rejected(self, today):
        assert "Revisa la data de naixement" in submit(birth_date="1900-01-01").content.decode()
        assert nothing_created()

    def test_both_date_formats_are_accepted(self, today):
        submit(birth_date="20/05/1990")
        assert MemberRequest.objects.get().birth_date == date(1990, 5, 20)


# --- Menors (RN-M01-62 a RN-M01-64; CA-M01-56, 57) ----------------------------------------------
class TestMinors:
    def test_under_14_with_guardian_creates_the_request_with_the_guardian(self, today):
        response = submit(birth_date="2016-04-01", **GUARDIAN)
        assert response.status_code == 303
        request = MemberRequest.objects.get()
        assert request.birth_date == date(2016, 4, 1)
        assert request.requested_type.code == "supporter"
        assert (
            request.guardian_first_name,
            request.guardian_last_name,
            request.guardian_id_document_type,
            request.guardian_id_document_number,
        ) == ("Marta", "Dorada Puig", "dni", "00000002W")
        # CA-M01-59: tot ho accepta el representant, també l'autorització; res del menor.
        rows = JoinAcceptance.objects.filter(request=request).select_related("legal_text")
        assert sorted(a.legal_text.kind for a in rows) == [
            "guardian_authorization",
            "membership_terms",
            "privacy",
        ]
        assert {a.accepted_by for a in rows} == {"guardian"}
        assert not Consent.objects.filter(person=request.person).exists()

    def test_under_14_cannot_choose_full_even_with_a_tampered_form(self, today):
        response = submit(birth_date="2016-04-01", membership_type=full_type(), **GUARDIAN)
        assert "Amb menys de 14 anys només es pot ser simpatitzant." in response.content.decode()
        assert nothing_created()

    @pytest.mark.parametrize("missing", list(GUARDIAN))
    def test_minor_without_complete_guardian_data_or_authorization_is_rejected(
        self, today, missing
    ):
        data = {**GUARDIAN, missing: None}
        response = submit(birth_date="2010-06-01", membership_type=full_type(), **data)
        assert response.status_code == 200
        assert nothing_created()

    def test_authorization_is_required_for_14_to_17(self, today):
        response = submit(birth_date="2010-06-01", **{**GUARDIAN, "guardian_authorization": None})
        assert "Sense l&#x27;autorització del pare" in response.content.decode()
        assert nothing_created()

    @pytest.mark.parametrize("document", ["00000002A", "12345678Z"])  # lletra dolenta; el seu
    def test_guardian_document_must_be_valid_and_not_the_minors(self, today, document):
        submit(birth_date="2010-06-01", **{**GUARDIAN, "guardian_id_document": document})
        assert nothing_created()

    def test_14_to_17_may_choose_full(self, today):
        response = submit(birth_date="2010-06-01", membership_type=full_type(), **GUARDIAN)
        assert response.status_code == 303
        assert MemberRequest.objects.get().requested_type.code == "full"

    def test_adult_guardian_data_is_not_stored(self, today):
        submit(birth_date="1990-05-20", **GUARDIAN)
        request = MemberRequest.objects.get()
        assert request.guardian_id_document_number == "" and request.guardian_first_name == ""
        assert {a.accepted_by for a in request.acceptances.all()} == {"applicant"}
        assert not request.acceptances.filter(legal_text__kind="guardian_authorization").exists()

    @pytest.mark.parametrize(
        ("on", "full_allowed"),
        [(date(2027, 3, 9), False), (date(2027, 3, 10), True)],  # aniversari dels 14
    )
    def test_14th_birthday(self, today, on, full_allowed):
        today(on)
        response = submit(birth_date="2013-03-10", membership_type=full_type(), **GUARDIAN)
        assert (response.status_code == 303) is full_allowed

    @pytest.mark.parametrize(
        ("on", "needs_guardian"),
        [(date(2026, 11, 5), True), (date(2026, 11, 6), False)],  # aniversari dels 18
    )
    def test_18th_birthday(self, today, on, needs_guardian):
        today(on)
        response = submit(birth_date="2008-11-06")  # sense representant
        assert (response.status_code == 200) is needs_guardian

    @pytest.mark.parametrize(
        ("on", "full_allowed"),
        [(date(2026, 12, 31), False), (date(2027, 1, 1), True)],  # 14 anys l'1 de gener
    )
    def test_new_year_with_barcelona_date(self, today, on, full_allowed):
        today(on)
        response = submit(birth_date="2013-01-01", membership_type=full_type(), **GUARDIAN)
        assert (response.status_code == 303) is full_allowed

    def test_in_person_minor_records_the_account(self, secretary, today):  # noqa: F811
        client = admin_client(secretary)
        client.post(reverse(IN_PERSON), form_data(birth_date="2016-04-01", **GUARDIAN))
        rows = list(MemberRequest.objects.get().acceptances.all())
        assert len(rows) == 3
        assert all(
            (a.accepted_by, a.channel, a.recorded_by) == ("guardian", "in_person", secretary)
            for a in rows
        )


# --- Document repetit (RN-M01-66, CA-M01-60) ---------------------------------------------------
def test_nothing_is_changed_or_attributed_to_an_existing_person(today):
    existing = Person.objects.create(
        first_name="Pau",
        last_name="Mero",
        contact_email="pau.mero@example.org",
        phone="600000099",
        id_document_type="dni",
        id_document_number="12345678Z",
        origin=Person.Origin.IN_PERSON,
    )
    snapshot = Person.objects.filter(pk=existing.pk).values().get()
    response = submit(birth_date="2016-04-01", **GUARDIAN)
    assert response.status_code == 303
    assert Person.objects.filter(pk=existing.pk).values().get() == snapshot
    assert not Consent.objects.filter(person=existing).exists()
    request = MemberRequest.objects.get()
    assert request.person == existing and request.duplicate_warning
    # Les acceptacions són de la sol·licitud: el model no té cap clau cap a `Person`.
    assert "person" not in {f.name for f in JoinAcceptance._meta.get_fields()}
    assert request.acceptances.count() == 3


# --- Document del sol·licitant: obligatori per als adults, opcional per als menors ---------------
class TestApplicantDocument:
    REQUIRED = "Aquest camp és obligatori."

    @pytest.mark.parametrize("value", ["", None])  # buit, o el camp tret del formulari
    def test_adult_without_document_is_rejected(self, today, value):
        response = submit(birth_date="1990-05-20", id_document=value)
        assert response.status_code == 200
        assert self.REQUIRED in response.content.decode()
        assert nothing_created()

    def test_service_rejects_an_adult_without_document_too(self, today):
        from django.core.exceptions import ValidationError

        from apps.members import join

        data = {
            "first_name": "Laia",
            "last_name": "Dorada",
            "id_document_type": "",
            "id_document_number": "",
            "contact_email": "laia@example.org",
            "phone": "600000001",
            "membership_type": MembershipType.objects.get(code="supporter"),
            "birth_date": date(1990, 5, 20),
            "on": TODAY,
        }
        with pytest.raises(ValidationError):
            join.submit(data, channel="web", send_receipt=False)
        assert MemberRequest.objects.count() == 0

    @pytest.mark.parametrize("birth", ["2010-06-01", "2016-04-01"])  # 16 anys; menys de 14
    def test_minor_without_document_is_accepted(self, today, birth):
        response = submit(birth_date=birth, id_document="", **GUARDIAN)
        assert response.status_code == 303
        request = MemberRequest.objects.get()
        person = request.person
        assert (person.id_document_type, person.id_document_number) == ("", "")
        # Sense document no hi ha avís de document repetit.
        assert not any(w["match"] == "document" for w in request.duplicate_warning)
        assert request.guardian_id_document_number == "00000002W"

    def test_two_minors_without_document_are_never_merged(self, today):
        submit(birth_date="2016-04-01", id_document="", **GUARDIAN)
        submit(birth_date="2016-04-01", id_document="", first_name="Pol", **GUARDIAN)
        assert Person.objects.filter(id_document_number="").count() >= 2
        assert MemberRequest.objects.count() == 2

    def test_minor_with_an_invalid_document_is_rejected(self, today):
        response = submit(birth_date="2010-06-01", id_document="12345678A", **GUARDIAN)
        assert "Escriu un DNI o un NIE vàlid" in response.content.decode()
        assert nothing_created()

    def test_minor_with_a_valid_repeated_document_gets_the_warning(self, today):
        existing = Person.objects.create(
            first_name="Pau",
            last_name="Mero",
            id_document_type="dni",
            id_document_number="12345678Z",
            origin=Person.Origin.IN_PERSON,
        )
        assert submit(birth_date="2010-06-01", **GUARDIAN).status_code == 303
        request = MemberRequest.objects.get()
        assert request.person == existing
        assert {"match": "document", "person_id": existing.pk} in request.duplicate_warning

    def test_minor_without_document_still_needs_the_guardians(self, today):
        data = {**GUARDIAN, "guardian_id_document": ""}
        response = submit(birth_date="2016-04-01", id_document="", **data)
        assert "Per a una persona menor, és obligatori." in response.content.decode()
        assert nothing_created()

    @pytest.mark.parametrize(
        ("birth", "required"),
        [("2008-11-06", True), ("2008-11-07", False)],  # avui en fa 18; demà en farà 18
    )
    def test_18th_birthday(self, today, birth, required):
        response = submit(birth_date=birth, id_document="", **GUARDIAN)
        assert (response.status_code == 200) is required

    def test_labels_follow_the_server_computed_age(self, today):
        page = Client().get(reverse(PUBLIC)).content.decode().replace("&#x27;", "'")
        assert "Document d'identitat (DNI o NIE; obligatori per a majors d'edat)" in page
        minor = preview(birth_date="2016-04-01").replace("&#x27;", "'")
        assert 'id="etiqueta-document" hx-swap-oob="innerHTML"' in minor
        assert "Document d'identitat (DNI o NIE, opcional)" in minor
        adult = preview(birth_date="1990-05-20").replace("&#x27;", "'")
        assert "Document d'identitat (DNI o NIE)</span>" in adult

    def test_bank_and_health_notice_is_on_no_screen(self, secretary, today):  # noqa: F811
        public = Client().get(reverse(PUBLIC)).content.decode()
        internal = admin_client(secretary).get(reverse(IN_PERSON)).content.decode()
        for html in (public, internal):
            assert "dades bancàries" not in html and "mandat SEPA" not in html


# --- Res de soci, número, quota ni carnet (069) ------------------------------------------------
def test_a_request_creates_no_member_number_fee_or_card(today):
    counter = MembershipNumberCounter.objects.get().last_number
    submit(birth_date="1990-05-20")
    assert MemberRequest.objects.count() == 1
    assert Member.objects.count() == AnnualFee.objects.count() == MemberCard.objects.count() == 0
    assert Charge.objects.count() == 0
    assert MembershipNumberCounter.objects.get().last_number == counter


# --- Immutabilitat i restriccions ---------------------------------------------------------------
class TestModel:
    def test_acceptances_cannot_be_changed_or_deleted(self, today):
        submit(birth_date="1990-05-20")
        row = JoinAcceptance.objects.first()
        row.accepted_by = "guardian"
        with pytest.raises(AppendOnlyError):
            row.save()
        with pytest.raises(AppendOnlyError):
            JoinAcceptance.objects.all().delete()
        # També amb SQL directe (disparadors de la migració 0008).
        for sql in (
            "UPDATE members_joinacceptance SET accepted_by = 'guardian'",
            "DELETE FROM members_joinacceptance",
        ):
            with pytest.raises(ProgrammingError), transaction.atomic(), connection.cursor() as c:
                c.execute(sql)

    def test_guardian_data_is_all_or_nothing(self, today):
        submit(birth_date="2016-04-01", **GUARDIAN)
        with pytest.raises(IntegrityError), transaction.atomic():
            MemberRequest.objects.update(guardian_id_document_number="")
        # També amb SQL directe, i en el sentit contrari (representant a mitges en un adult).
        for sql in (
            "UPDATE members_memberrequest SET guardian_first_name = ''",
            "UPDATE members_memberrequest SET guardian_id_document_type = 'passport'",
        ):
            with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as c:
                c.execute(sql)


# --- Visibilitat (secció 6) ---------------------------------------------------------------------
class TestVisibility:
    def test_audit_entries_carry_no_birth_date_or_guardian_data(self, today):
        submit(birth_date="2016-04-01", **GUARDIAN)
        for entry in AuditEntry.objects.all():
            text = repr(entry.__dict__)
            assert "2016-04-01" not in text and "2016, 4, 1" not in text
            assert "Marta" not in text and "00000002W" not in text

    def test_guardian_fields_are_hidden_in_the_audit_log_like_the_members_identity(self):
        assert _field_permission("birth_date") == "members.field.birth_date"
        for name in ("guardian_first_name", "guardian_id_document_number"):
            assert _field_permission(name) == "members.field.identity"

    def test_treasurer_has_no_birth_date_or_identity_permission(self, make_admin):  # noqa: F811
        treasurer = make_admin("treasurer")
        assert not has_perm(treasurer, "members.field.birth_date")
        assert not has_perm(treasurer, "members.field.identity")
        assert not has_perm(treasurer, "members.create_in_person")


# --- Vista prèvia i presentació de la quota (068, 070) ------------------------------------------
class TestPreview:
    def test_preview_creates_nothing_and_does_not_count_for_the_limit(self, today):
        html = preview(birth_date="1990-05-20")
        assert 'id="part-variable"' in html and 'hx-swap-oob="innerHTML"' in html
        assert nothing_created()

    def test_preview_shows_no_errors_while_the_person_is_typing(self, today):
        html = preview(birth_date="2016-04-01", accept_privacy=None)
        assert "errorlist" not in html and 'aria-invalid="true"' not in html

    @pytest.mark.parametrize(
        "on", [date(2026, 1, 15), date(2026, 10, 31), date(2026, 11, 1), date(2026, 12, 31)]
    )
    def test_adult_sees_the_full_annual_fee_in_any_month(self, today, on):
        today(on)
        html = preview(birth_date="1990-05-20").replace("&#x27;", "'")
        types = type_fieldset(html)
        assert "Simpatitzant · quota anual de 35,00 €" in types
        assert "Ple dret · quota anual de 90,00 €" in types
        assert "L'import es confirma en aprovar l'alta." in types
        assert 'name="guardian_first_name"' not in html

    @pytest.mark.parametrize("birth", ["1990-05-20", "2011-06-01", "2016-04-01", None])
    def test_no_proration_or_november_rule_texts(self, today, birth):
        # 070: cap text de prorrata, de «la resta de l'any», d'any natural ni de plaços.
        for on in (date(2026, 3, 1), date(2026, 11, 15), date(2026, 12, 31)):
            today(on)
            html = preview(birth_date=birth) if birth else Client().get(reverse(PUBLIC))
            text = (html if birth else html.content.decode()).lower()
            for banned in (
                "proporcional",
                "prorrat",
                "inclou el que queda",
                "any natural",
                "mesos que queden",
                "terminis",
                "plaços",
                "32 €",
            ):
                assert banned not in text, (birth, on, banned)

    def test_under_14_sees_only_supporter_without_fee(self, today):
        html = preview(birth_date="2016-04-01")
        assert "Simpatitzant · sense quota fins al 31/12/2030" in html
        assert "Ple dret" not in html
        assert 'name="guardian_first_name"' in html and "Menor de 14 anys" in html

    def test_turned_14_this_year_sees_both_types_without_an_amount(self, today):
        today(date(2027, 6, 15))
        html = preview(birth_date="2013-03-10")
        types = type_fieldset(html)
        assert "Simpatitzant · sense quota fins al 31/12/2027" in types
        assert "Ple dret · sense quota fins al 31/12/2027" in types
        assert "€" not in types

    def test_from_january_after_turning_14_the_full_fee_is_shown(self, today):
        today(date(2028, 1, 1))
        types = type_fieldset(preview(birth_date="2013-03-10"))
        assert "Simpatitzant · quota anual de 35,00 €" in types
        assert "Ple dret · quota anual de 90,00 €" in types

    def test_guardian_block_only_for_minors_also_without_javascript(self, today):
        # Sense data (primera càrrega, també sense JavaScript) i per a un adult: no hi és.
        first = Client().get(reverse(PUBLIC)).content.decode().replace("&#x27;", "'")
        assert 'class="representant"' not in first and 'name="guardian_authorization"' not in first
        assert "Els menors de 14 anys només poden ser simpatitzants, sense quota." in first
        assert 'class="representant"' not in preview(birth_date="2008-11-06")  # avui en fa 18
        # Un menor: la vista prèvia el mostra; sense JavaScript, l'enviament el torna amb errors.
        assert 'class="representant"' in preview(birth_date="2008-11-07")  # encara en té 17
        sent = submit(birth_date="2010-06-01").content.decode()
        assert 'class="representant"' in sent and "Per a una persona menor, és obligatori." in sent
        assert nothing_created()

    def test_each_legal_text_has_its_own_required_checkbox(self, today):
        for field in ("accept_privacy", "accept_membership_terms"):
            response = submit(birth_date="1990-05-20", **{field: None})
            assert response.status_code == 200
        assert nothing_created()
        minor = preview(birth_date="2016-04-01")
        assert minor.count('class="etiqueta-obligatori"') == 3  # i l'autorització
        assert 'href="#text-guardian_authorization" data-obre-text' in minor

    def test_in_person_preview_needs_p2(self, secretary, make_admin, today):  # noqa: F811
        html = preview(admin_client(secretary), reverse(IN_PERSON), birth_date="2016-04-01")
        assert "Menor de 14 anys" in html
        other = admin_client(make_admin("treasurer"))
        data = {**form_data(birth_date="2016-04-01"), "vista_previa": "1"}
        assert other.post(reverse(IN_PERSON), data).status_code == 404
