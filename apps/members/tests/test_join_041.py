"""Canvis del formulari d'alta i destinatari de les comunicacions d'un menor (T-M01-41).

072: Q-011 (opció 3), Q-017, Q-031, Q-044 (opció A) i quarta instrucció, punt 3. 074: punts 13 a
16, RN-M01-78 i CA-M01-77. Els textos del butlletí i de les imatges són els PROVISIONALS de
`join.PROVISIONAL_OPTIONAL_TEXTS`, publicats només aquí. Només dades inventades (DNI de prova amb
la lletra correcta, correus a example.org).
"""

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse

from apps.core import consents
from apps.core.models import Consent, OutgoingEmail, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import admissions, fees, join, recipients
from apps.members import member_requests as mr
from apps.members.forms import JoinForm
from apps.members.models import JoinAcceptance, Member, MemberRequest, MembershipType
from apps.members.tests.test_cards import add_fee
from apps.members.tests.test_join import (  # noqa: F401 (fixture texts)
    IN_PERSON,
    PUBLIC,
    admin_client,
    form_data,
    texts,
)
from apps.members.tests.test_member_requests import travel_to

pytestmark = pytest.mark.usefixtures("texts")

UNDER14 = "2016-04-01"  # 10 anys
TEEN = "2010-06-15"  # 16 anys
GUARDIAN_EMAIL = "marta.dorada@example.org"
GUARDIAN = {
    "guardian_first_name": "Marta",
    "guardian_last_name": "Dorada Puig",
    "guardian_id_document": "00000002W",
    "guardian_email": GUARDIAN_EMAIL,
    "guardian_phone": "600 000 009",
    "guardian_authorization": "on",
}
NEWSLETTER, IMAGES = join.OPTIONAL_TEXTS


@pytest.fixture
def sec(make_admin, texts):  # noqa: F811
    return make_admin("secretary", username="secretaria.prova")


@pytest.fixture
def optional(texts):  # noqa: F811
    """Publica els textos provisionals del butlletí i de les imatges (mai en producció)."""
    for kind, body in join.PROVISIONAL_OPTIONAL_TEXTS.items():
        consents.publish_text(kind, body, by=texts)


def versions():
    return ";".join(f"{k}:{t.version}" for k, t in join.current_texts().items())


def data(**overrides):
    return form_data(text_versions=versions(), **overrides)


def post(client=None, url=None, **overrides):
    return (client or Client()).post(url or reverse(PUBLIC), data(**overrides))


def minor(birth=UNDER14, **overrides):
    return post(birth_date=birth, **{**GUARDIAN, **overrides})


def kinds(request, accepted_by=None):
    rows = JoinAcceptance.objects.filter(request=request)
    if accepted_by:
        rows = rows.filter(accepted_by=accepted_by)
    return sorted(rows.values_list("legal_text__kind", flat=True))


def emails(template):
    return list(
        OutgoingEmail.objects.filter(template=template).values_list("to_address", flat=True)
    )


# --- (1) Butlletí i imatges (Q-031) ----------------------------------------------------------
class TestOptionalConsents:
    def test_without_published_texts_there_is_no_checkbox_and_a_posted_value_is_ignored(self):
        html = Client().get(reverse(PUBLIC)).content.decode()
        assert 'name="accept_newsletter"' not in html and 'name="accept_images"' not in html
        assert post(accept_newsletter="on", accept_images="on").status_code == 303
        assert kinds(MemberRequest.objects.get()) == ["membership_terms", "privacy"]

    def test_checkboxes_are_unchecked_by_default_and_separate_from_the_required(self, optional):
        html = Client().get(reverse(PUBLIC)).content.decode()
        for name in ("accept_newsletter", "accept_images"):
            tag = html.split(f'name="{name}"')[1].split(">")[0]
            assert "checked" not in tag
        assert "Consentiments opcionals" in html and "opcional" in html
        # Separats: el bloc opcional va després del dels obligatoris.
        assert html.index('name="accept_membership_terms"') < html.index('name="accept_images"')
        assert "TEXT PROVISIONAL" in html  # el text sencer, a la secció dels textos legals

    def test_server_never_marks_them_unless_they_arrive_checked(self, optional):
        assert post(accept_newsletter="false").status_code == 303
        request = MemberRequest.objects.get()
        assert kinds(request) == ["membership_terms", "privacy"]

    def test_adult_checked_boxes_become_consents_given_by_the_person_on_approval(
        self, optional, sec
    ):
        post(accept_newsletter="on", accept_images="on")
        request = MemberRequest.objects.get()
        assert kinds(request, "applicant") == [
            "images",
            "membership_terms",
            "newsletter",
            "privacy",
        ]
        assert not Consent.objects.exists()  # cap consentiment abans d'aprovar (CA-M01-01)
        admissions.approve_join(request, by=sec)
        granted = Consent.objects.filter(person=request.person)
        assert sorted(granted.values_list("legal_text__kind", flat=True)) == [
            "images",
            "membership_terms",
            "newsletter",
            "privacy",
        ]
        assert set(granted.values_list("given_by", flat=True)) == {"person"}
        assert consents.has_consent(request.person, NEWSLETTER)

    def test_only_the_checked_one_is_recorded(self, optional, sec):
        post(accept_images="on")
        request = MemberRequest.objects.get()
        admissions.approve_join(request, by=sec)
        assert consents.has_consent(request.person, IMAGES)
        assert not consents.has_consent(request.person, NEWSLETTER)

    def test_under_14_images_consent_goes_to_the_minor_given_by_the_guardian_option_a(
        self, optional, sec
    ):
        """072, Q-044 opció A: les imatges, a la persona del menor, amb el representant com a qui
        el dona. És l'única excepció: el butlletí es queda a la sol·licitud."""
        minor(id_document="00000003A", accept_images="on", accept_newsletter="on")
        request = MemberRequest.objects.get()
        assert kinds(request, "guardian") == [
            "guardian_authorization",
            "images",
            "membership_terms",
            "newsletter",
            "privacy",
        ]
        admissions.approve_join(request, by=sec, guardian_checked=True)
        granted = Consent.objects.filter(person=request.person)
        consent = granted.get()
        assert (consent.legal_text.kind, consent.given_by) == ("images", "guardian")

    def test_under_14_newsletter_stays_on_the_request_and_creates_no_consent_q_044(
        self, optional, sec
    ):
        """072, Q-044 i tercera instrucció, punt 3: el butlletí marcat pel representant es queda
        a la sol·licitud, com la resta de les seves acceptacions."""
        minor(id_document="00000003A", accept_newsletter="on")
        request = MemberRequest.objects.get()
        assert "newsletter" in kinds(request, "guardian")
        admissions.approve_join(request, by=sec, guardian_checked=True)
        assert not Consent.objects.filter(person=request.person).exists()
        assert JoinAcceptance.objects.filter(
            request=request, legal_text__kind="newsletter", accepted_by="guardian"
        ).exists()

    def test_14_to_17_newsletter_is_a_consent_given_by_the_minor(self, optional, sec):
        minor(TEEN, id_document="00000003A", accept_newsletter="on")
        request = MemberRequest.objects.get()
        admissions.approve_join(request, by=sec, guardian_checked=True)
        consent = Consent.objects.get(person=request.person)
        assert (consent.legal_text.kind, consent.given_by) == ("newsletter", "person")

    def test_14_to_17_consents_are_given_by_the_minor_rn_m01_78(self, optional, sec):
        """RN-M01-78 [A validar: assessor de protecció de dades, Q-016]."""
        minor(TEEN, id_document="00000003A", accept_images="on")
        request = MemberRequest.objects.get()
        assert kinds(request, "applicant") == ["images"]
        admissions.approve_join(request, by=sec, guardian_checked=True)
        consent = Consent.objects.get(person=request.person)
        assert (consent.legal_text.kind, consent.given_by) == ("images", "person")

    def test_in_person_form_has_them_too(self, optional, sec):
        client = admin_client(sec)
        html = client.get(reverse(IN_PERSON)).content.decode()
        assert 'name="accept_newsletter"' in html and "Q-16 i Q-028" in html
        assert client.post(reverse(IN_PERSON), data(accept_newsletter="on")).status_code == 303
        acceptance = JoinAcceptance.objects.get(legal_text__kind=NEWSLETTER)
        assert (acceptance.channel, acceptance.recorded_by) == ("in_person", sec)

    def test_given_by_is_validated_by_the_database(self, optional):
        person = Person.objects.create(first_name="Anna", origin="web")
        text = consents.current_text(IMAGES)
        with pytest.raises(IntegrityError), transaction.atomic():
            Consent.objects.create(
                person=person, legal_text=text, action="granted", channel="web", given_by="altre"
            )


# --- (2) Contacte del representant (Q-011, opció 3) -------------------------------------------
class TestGuardianContact:
    def test_guardian_email_and_phone_are_stored_normalised(self):
        minor(guardian_email="Marta.Dorada@Example.org ", guardian_phone="600-000 009")
        request = MemberRequest.objects.get()
        assert (request.guardian_email, request.guardian_phone) == (GUARDIAN_EMAIL, "600000009")

    @pytest.mark.parametrize("missing", ["guardian_email", "guardian_phone"])
    @pytest.mark.parametrize("birth", [UNDER14, TEEN])
    def test_guardian_email_and_phone_are_required(self, missing, birth):
        response = minor(birth, **{missing: ""})
        assert response.status_code == 200
        assert "Per a una persona menor, és obligatori." in response.content.decode()
        assert not MemberRequest.objects.exists()

    def test_invalid_guardian_phone_is_rejected(self):
        assert minor(guardian_phone="123").status_code == 200
        assert not MemberRequest.objects.exists()

    def test_minor_own_email_and_phone_are_optional(self):
        assert minor(TEEN, contact_email="", phone="").status_code == 303
        person = MemberRequest.objects.get().person
        assert (person.contact_email, person.phone) == ("", "")

    @pytest.mark.parametrize("missing", ["contact_email", "phone"])
    def test_adult_email_and_phone_are_still_required(self, missing):
        response = post(**{missing: ""})
        assert response.status_code == 200
        assert not MemberRequest.objects.exists()

    def test_adult_guardian_contact_is_discarded(self):
        post(guardian_email=GUARDIAN_EMAIL, guardian_phone="600000009")
        request = MemberRequest.objects.get()
        assert (request.guardian_email, request.guardian_phone) == ("", "")

    def test_service_rechecks_the_guardian_contact(self, sec):
        form = JoinForm(data(birth_date=UNDER14, **GUARDIAN), texts=join.current_texts())
        assert form.is_valid(), form.errors
        cleaned = {**form.cleaned_data, "guardian_phone": ""}
        with pytest.raises(ValidationError):
            join.submit(cleaned, channel=MemberRequest.Channel.WEB)

    def test_contact_without_guardian_or_half_is_refused_by_the_database(self):
        post()
        with pytest.raises(IntegrityError), transaction.atomic():
            MemberRequest.objects.update(guardian_email=GUARDIAN_EMAIL, guardian_phone="600000009")

    def test_pending_join_shows_the_guardian_contact(self, sec):
        minor()
        html = admin_client(sec).get(reverse("administration:join_requests")).content
        assert GUARDIAN_EMAIL in html.decode() and "600000009" in html.decode()


# --- (3) Destinatari de les comunicacions (RN-M01-78, CA-M01-77) ------------------------------
class TestRecipientRule:
    @pytest.mark.parametrize(
        ("age", "own", "guardian", "expected"),
        [
            (10, "nen@example.org", "tutor@example.org", "tutor@example.org"),  # < 14: sempre
            (13, "", "tutor@example.org", "tutor@example.org"),
            (14, "", "tutor@example.org", "tutor@example.org"),  # 14 a 17 sense correu
            (17, "", "tutor@example.org", "tutor@example.org"),
            (14, "noia@example.org", "tutor@example.org", "noia@example.org"),
            (18, "adult@example.org", "tutor@example.org", "adult@example.org"),
            (None, "sense.data@example.org", "tutor@example.org", "sense.data@example.org"),
            (10, "nen@example.org", "", ""),  # sense representant: no s'envia res
        ],
    )
    def test_ca_m01_77_address_for(self, age, own, guardian, expected):
        assert recipients.address_for(age, own, guardian) == expected


def approved_minor(birth, *, own_email="", document="00000003A", by=None):
    """Persona menor amb una alta aprovada amb el representant (com en aprovar-la)."""
    person = Person.objects.create(
        first_name="Pol",
        last_name="Dorada",
        origin="web",
        contact_email=own_email,
        id_document_type="dni",
        id_document_number=document,
    )
    MemberRequest.objects.create(
        kind=MemberRequest.Kind.JOIN,
        person=person,
        requested_type=MembershipType.objects.get(code="supporter"),
        channel=MemberRequest.Channel.WEB,
        status=MemberRequest.Status.APPROVED,
        birth_date=date.fromisoformat(birth),
        guardian_first_name="Marta",
        guardian_last_name="Dorada Puig",
        guardian_id_document_type="dni",
        guardian_id_document_number="00000002W",
        guardian_email=GUARDIAN_EMAIL,
        guardian_phone="600000009",
    )
    return person


def member_of(person, number=901):
    return Member.objects.create(
        person=person,
        member_number=number,
        type=MembershipType.objects.get(code="supporter"),
        status=Member.Status.ACTIVE,
        joined_on=date(2024, 1, 10),
    )


class TestEmailFor:
    def test_ca_m01_77_under_14_with_own_email_goes_to_the_guardian(self):
        person = approved_minor(UNDER14, own_email="pol@example.org")
        assert recipients.email_for(person) == GUARDIAN_EMAIL

    def test_ca_m01_77_14_to_17_without_email_goes_to_the_guardian(self):
        assert recipients.email_for(approved_minor(TEEN)) == GUARDIAN_EMAIL

    def test_14_to_17_with_own_email_goes_to_the_minor(self):
        person = approved_minor(TEEN, own_email="pol@example.org")
        assert recipients.email_for(person) == "pol@example.org"

    def test_the_person_birth_date_wins(self):
        person = approved_minor(UNDER14, own_email="pol@example.org")
        Person.objects.filter(pk=person.pk).update(birth_date=date(1990, 1, 1))
        person.refresh_from_db()
        assert recipients.email_for(person) == "pol@example.org"

    def test_an_unreviewed_request_cannot_divert_an_existing_person_mail(self):
        """Seguretat: una sol·licitud pendent amb el document d'una persona existent no canvia on
        van els seus correus."""
        person = Person.objects.create(
            first_name="Anna", origin="web", contact_email="anna@example.org"
        )
        MemberRequest.objects.create(
            kind=MemberRequest.Kind.JOIN,
            person=person,
            requested_type=MembershipType.objects.get(code="supporter"),
            channel=MemberRequest.Channel.WEB,
            birth_date=date.fromisoformat(UNDER14),
            guardian_first_name="Algú",
            guardian_last_name="Altre",
            guardian_id_document_type="dni",
            guardian_id_document_number="00000002W",
            guardian_email="intrus@example.org",
            guardian_phone="600000009",
        )
        assert recipients.email_for(person) == "anna@example.org"

    def test_minor_without_guardian_address_gets_nothing(self):
        person = Person.objects.create(
            first_name="Nil",
            origin="web",
            contact_email="nil@example.org",
            birth_date=date(2016, 1, 1),
        )
        assert recipients.email_for(person) == ""


class TestCommunications:
    """CA-M01-77 per a cada comunicació que avui va a una persona."""

    @pytest.mark.parametrize(
        ("birth", "own", "expected"),
        [
            (UNDER14, "pol@example.org", GUARDIAN_EMAIL),
            (TEEN, "", GUARDIAN_EMAIL),
            (TEEN, "pol@example.org", "pol@example.org"),
        ],
    )
    def test_receipt(self, birth, own, expected):
        client = Client()
        response = client.post(
            reverse(PUBLIC), data(birth_date=birth, contact_email=own, **GUARDIAN)
        )
        assert response.status_code == 303
        assert emails(join.RECEIPT_TEMPLATE) == [expected]
        # La confirmació diu on s'ha enviat el rebut.
        assert expected in client.get(reverse(PUBLIC)).content.decode()

    def test_receipt_of_an_adult_goes_to_the_adult(self):
        post()
        assert emails(join.RECEIPT_TEMPLATE) == ["laia.dorada@example.org"]

    def test_rejection_of_a_minor_goes_to_the_guardian(self, sec):
        """REVISIO-NOTES, fila 33: el rebuig d'un menor de 9 anys anava al correu del menor."""
        minor(contact_email="pol@example.org")
        request = MemberRequest.objects.get()
        admissions.reject_join(request, by=sec, reason="Motiu inventat de proves")
        assert emails(admissions.REJECTION_TEMPLATE) == [GUARDIAN_EMAIL]

    def test_rejection_of_a_teen_without_email_goes_to_the_guardian(self, sec):
        minor(TEEN, contact_email="")
        admissions.reject_join(MemberRequest.objects.get(), by=sec, reason="Motiu de proves")
        assert emails(admissions.REJECTION_TEMPLATE) == [GUARDIAN_EMAIL]

    def test_approval_sends_no_email_today(self, sec):
        """L'aprovació encara no envia cap correu (la invitació és de la T-M01-14): quan n'hi
        hagi, ha de passar per `recipients.email_for`."""
        minor(id_document="00000003A")
        OutgoingEmail.objects.all().delete()
        admissions.approve_join(MemberRequest.objects.get(), by=sec, guardian_checked=True)
        assert not OutgoingEmail.objects.exists()

    @pytest.mark.parametrize(
        ("birth", "own", "expected"),
        [
            (UNDER14, "pol@example.org", GUARDIAN_EMAIL),
            (TEEN, "", GUARDIAN_EMAIL),
            (TEEN, "pol@example.org", "pol@example.org"),
        ],
    )
    def test_fee_reminder(self, birth, own, expected):
        """072, quarta instrucció, punt 3, i RN-M01-78."""
        fee = add_fee(member_of(approved_minor(birth, own_email=own)), period=2026)
        assert fees.send_due_reminders(fee.due_on) == 1
        assert emails(fees.REMINDER_TEMPLATE) == [expected]

    def test_fee_reminder_without_any_address_is_not_sent(self):
        person = Person.objects.create(first_name="Nil", origin="web", birth_date=date(2016, 1, 1))
        fee = add_fee(member_of(person), period=2026)
        fees.send_due_reminders(fee.due_on)
        assert not OutgoingEmail.objects.exists()

    def test_leave_confirmation_goes_to_the_guardian(self, make_admin):  # noqa: F811
        member = member_of(approved_minor(UNDER14, own_email="pol@example.org"))
        leave = MemberRequest.objects.create(
            kind=MemberRequest.Kind.LEAVE,
            person=member.person,
            member=member,
            request_reason="Motiu inventat",
            channel=MemberRequest.Channel.IN_PERSON,
        )
        mr.approve_leave(leave, by=make_admin("secretary"), effective_on=date(2026, 1, 1))
        assert emails(mr.LEAVE_EMAIL) == [GUARDIAN_EMAIL]

    def test_scheduled_leave_from_the_daily_task_goes_to_the_guardian(
        self,
        make_admin,  # noqa: F811
        monkeypatch,
    ):
        member = member_of(approved_minor(TEEN))
        leave = MemberRequest.objects.create(
            kind=MemberRequest.Kind.LEAVE,
            person=member.person,
            member=member,
            request_reason="Motiu inventat",
            channel=MemberRequest.Channel.IN_PERSON,
        )
        day = mr.local_today() + timedelta(days=10)
        mr.approve_leave(leave, by=make_admin("secretary"), effective_on=day)
        assert not OutgoingEmail.objects.exists()
        travel_to(monkeypatch, day)
        assert len(mr.apply_due_leaves()) == 1
        assert emails(mr.LEAVE_EMAIL) == [GUARDIAN_EMAIL]


# --- (4) Passaport només a l'alta presencial (Q-017) ------------------------------------------
class TestPassport:
    def test_web_has_no_document_type_and_rejects_a_tampered_passport(self):
        assert 'name="id_document_kind"' not in Client().get(reverse(PUBLIC)).content.decode()
        response = post(id_document="PAA123456", id_document_kind="passport")
        assert response.status_code == 200
        assert "Escriu un DNI o un NIE vàlid" in response.content.decode()
        assert not MemberRequest.objects.exists()

    def test_web_rejects_a_tampered_guardian_passport(self):
        response = minor(guardian_id_document="PAA123456", guardian_id_document_kind="passport")
        assert response.status_code == 200
        assert not MemberRequest.objects.exists()

    def test_service_rejects_a_passport_from_the_web(self):
        form = JoinForm(data(), texts=join.current_texts())
        assert form.is_valid(), form.errors
        cleaned = {**form.cleaned_data, "id_document_type": "passport"}
        with pytest.raises(ValidationError):
            join.submit(cleaned, channel=MemberRequest.Channel.WEB)
        assert not MemberRequest.objects.exists()

    def test_in_person_accepts_a_passport_for_the_person(self, sec):
        client = admin_client(sec)
        assert 'name="id_document_kind"' in client.get(reverse(IN_PERSON)).content.decode()
        response = client.post(
            reverse(IN_PERSON), data(id_document="paa-123 456", id_document_kind="passport")
        )
        assert response.status_code == 303
        person = MemberRequest.objects.get().person
        assert (person.id_document_type, person.id_document_number) == ("passport", "PAA123456")

    def test_in_person_accepts_a_passport_for_the_guardian(self, sec):
        response = admin_client(sec).post(
            reverse(IN_PERSON),
            data(
                birth_date=UNDER14,
                **{
                    **GUARDIAN,
                    "guardian_id_document": "X1234567",
                    "guardian_id_document_kind": "passport",
                },
            ),
        )
        assert response.status_code == 303
        request = MemberRequest.objects.get()
        assert (request.guardian_id_document_type, request.guardian_id_document_number) == (
            "passport",
            "X1234567",
        )

    def test_in_person_invalid_passport_is_rejected(self, sec):
        response = admin_client(sec).post(
            reverse(IN_PERSON), data(id_document="P-1", id_document_kind="passport")
        )
        assert "número de passaport vàlid" in response.content.decode()
        assert not MemberRequest.objects.exists()
