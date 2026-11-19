"""Carnet del soci (T-M01-19; RN-M01-18, 19, 21, 24, 25, 27; CA-M01-09 part del carnet, CA-M01-14
pel servei, CA-M01-15; decisions 069 i 070; P13). Només dades inventades."""

import hashlib
from datetime import date, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, Payment, Person
from apps.members import cards, services
from apps.members.cards import CardNotAllowed
from apps.members.fee_rules import local_today
from apps.members.models import AnnualFee, Member, MemberCard, MembershipType
from conftest import PASSWORD

SYSTEM = audit.system("proves")
S = Member.Status
CARD = "members:card"


def make_member(first="Anna", number=1287, status=S.ACTIVE, document="12345678Z", **fields):
    person = Person.objects.create(
        first_name=first,
        last_name="Prova",
        origin=Person.Origin.WEB,
        id_document_type=Person.DocumentType.DNI,
        id_document_number=document,
    )
    return Member.objects.create(
        person=person,
        member_number=number,
        type=MembershipType.objects.get(code="full"),
        status=status,
        joined_on=fields.pop("joined_on", date(2019, 3, 12)),
        **fields,
    )


def add_fee(member, *, period=2026):
    charge = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=9000,
        concept=f"Quota {period}",
        origin="members",
        by=SYSTEM,
    )
    return AnnualFee.objects.create(
        member=member,
        period=period,
        kind=AnnualFee.Kind.ANNUAL,
        charge=charge,
        due_on=date(period, 1, 1),
    )


def pay(fee, paid_at=None, *, amount=None):
    payment = Payment.objects.create(
        charge=fee.charge,
        method=Payment.Method.CARD,
        amount_cents=amount or fee.charge.amount_cents,
        paid_at=paid_at or timezone.now(),
    )
    if amount is None:
        charges.mark_paid(fee.charge, payment, origin="provider", by=SYSTEM)
    return payment


def paid_member(*args, **kwargs):
    member = make_member(*args, **kwargs)
    pay(add_fee(member))
    return member


def validity(member, card, today=None):
    return cards.validity(cards.load_member(member.pk), card, today)


# --- Emissió (069, RN-M01-24) -----------------------------------------------------------------


@pytest.mark.django_db
class TestIssue:
    def test_only_the_fingerprint_is_stored(self):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        card = MemberCard.objects.get(member=member)
        assert len(token) >= 43  # 32 octets en base64 URL: 256 bits
        assert card.token_hash == hashlib.sha256(token.encode()).hexdigest()
        stored = [str(v) for v in MemberCard.objects.values().get().values()]
        logged = [str(v) for e in AuditEntry.objects.values() for v in e.values()]
        assert not any(token in value for value in stored + logged)

    def test_tokens_are_random(self):
        first = cards.issue_card(paid_member(), by=SYSTEM)
        second = cards.issue_card(paid_member("Berta", 1288, document="87654321X"), by=SYSTEM)
        assert first != second

    def test_issuing_is_recorded(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        entry = AuditEntry.objects.get(action=cards.CARD_ISSUED)
        assert entry.target_id == str(MemberCard.objects.get(member=member).pk)
        assert entry.actor_origin == "proves"

    @pytest.mark.parametrize("status", [S.PENDING, S.UNPAID, S.LEFT])
    def test_no_card_unless_active(self, status):
        member = make_member(
            status=status, **({"left_on": date(2026, 1, 1)} if status == S.LEFT else {})
        )
        pay(add_fee(member))
        with pytest.raises(CardNotAllowed):
            cards.issue_card(member, by=SYSTEM)
        assert not MemberCard.objects.exists()

    def test_no_card_before_the_payment_is_confirmed(self):
        # RN-M01-67: aprovat i actiu no n'hi ha prou sense un pagament confirmat.
        member = make_member()
        add_fee(member)  # pendent
        with pytest.raises(CardNotAllowed):
            cards.issue_card(member, by=SYSTEM)
        assert not MemberCard.objects.exists()

    def test_no_card_without_any_fee(self):
        # Els exempts (P-57) no tenen cap activació ni carnet: no s'inventa cap regla.
        with pytest.raises(CardNotAllowed):
            cards.issue_card(make_member(), by=SYSTEM)

    def test_no_card_with_a_partial_payment(self):
        # Tres quotes (070): sense comportament aprovat (P-61).
        member = make_member()
        pay(add_fee(member), amount=3200)
        with pytest.raises(CardNotAllowed):
            cards.issue_card(member, by=SYSTEM)

    def test_a_second_card_needs_replace(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        with pytest.raises(CardNotAllowed):
            cards.issue_card(member, by=SYSTEM)
        assert MemberCard.objects.filter(member=member).count() == 1


# --- Validesa (RN-M01-18, RN-M01-19, 070) -----------------------------------------------------


@pytest.mark.django_db
class TestValidity:
    def test_valid_until_twelve_months_after_the_payment(self):
        member = make_member()
        paid_at = timezone.make_aware(datetime(2026, 11, 9, 10, 0))
        pay(add_fee(member), paid_at)
        cards.issue_card(member, by=SYSTEM)
        card = cards.active_card(member)
        result = validity(member, card, date(2026, 11, 10))
        assert result == cards.CardValidity(True, date(2027, 11, 9))  # mai el 31/12
        assert validity(member, card, date(2027, 11, 9)).valid  # el dia de la renovació, sí
        assert not validity(member, card, date(2027, 11, 10)).valid

    def test_a_pending_renewal_does_not_take_the_paid_period_away(self):
        # Una quota de renovació pendent (T-M01-18) no treu la validesa del període pagat.
        member = make_member()
        pay(add_fee(member), timezone.make_aware(datetime(2026, 11, 9, 10, 0)))
        cards.issue_card(member, by=SYSTEM)
        add_fee(member, period=2027)
        result = validity(member, cards.active_card(member), date(2027, 10, 30))
        assert result == cards.CardValidity(True, date(2027, 11, 9))

    def test_the_latest_payment_sets_the_renewal_date(self):
        member = make_member()
        pay(add_fee(member), timezone.make_aware(datetime(2025, 11, 1, 10, 0)))
        pay(add_fee(member, period=2027), timezone.make_aware(datetime(2026, 10, 20, 10, 0)))
        cards.issue_card(member, by=SYSTEM)
        until = validity(member, cards.active_card(member), date(2026, 11, 9)).until
        assert until == date(2027, 10, 20)

    def test_unpaid_member_card_is_not_valid_and_not_revoked(self):
        # CA-M01-09 (part del carnet) i D1: l'impagat no revoca ni modifica el carnet. Que
        # `mark_unpaid` no el toqui ho comprova test_services (T-M01-12).
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        card = cards.active_card(member)
        before = MemberCard.objects.filter(pk=card.pk).values().get()
        Member.objects.filter(pk=member.pk).update(status=S.UNPAID)
        assert not validity(member, card).valid
        assert MemberCard.objects.filter(pk=card.pk).values().get() == before
        Member.objects.filter(pk=member.pk).update(status=S.ACTIVE)
        assert validity(member, card).valid

    def test_revoked_card_is_not_valid(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        card = cards.revoke_card(member, by=SYSTEM, reason="Petició del soci")
        assert not validity(member, card).valid

    def test_left_member_card_is_not_valid(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        card = cards.active_card(member)
        Member.objects.filter(pk=member.pk).update(status=S.LEFT, left_on=local_today())
        assert not validity(member, card).valid

    def test_partial_payment_has_no_validity(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        card = cards.active_card(member)
        pay(add_fee(member, period=2027), amount=3200)  # P-61: cap regla, cap «fins al»
        assert validity(member, card) == cards.CardValidity(False, None)


@pytest.mark.django_db
class TestValidCardForToken:
    def test_valid_token(self):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        assert cards.valid_card_for_token(token).member_id == member.pk

    def test_unknown_revoked_and_unpaid_give_the_same_none(self):
        # CA-M01-14 pel servei; la pàgina i el temps de resposta són de la T-M01-20.
        revoked = paid_member()
        revoked_token = cards.issue_card(revoked, by=SYSTEM)
        cards.revoke_card(revoked, by=SYSTEM, reason="Baixa")
        unpaid = paid_member("Berta", 1288, document="87654321X")
        unpaid_token = cards.issue_card(unpaid, by=SYSTEM)
        Member.objects.filter(pk=unpaid.pk).update(status=S.UNPAID)
        for token in ("inventat", "", None, revoked_token, unpaid_token):
            assert cards.valid_card_for_token(token) is None

    def test_expired_token(self):
        # Pagament de fa més de 12 mesos: la renovació ja ha passat (070).
        member = make_member()
        pay(add_fee(member), timezone.now() - timedelta(days=400))
        token = cards.issue_card(member, by=SYSTEM)
        assert cards.valid_card_for_token(token) is None
        assert validity(member, cards.active_card(member)).until < local_today()


# --- Revocació i substitució (RN-M01-25, CA-M01-15) -------------------------------------------


@pytest.mark.django_db
class TestRevokeAndReplace:
    def test_revoke_needs_a_reason(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        for reason in ("", "   ", None):
            with pytest.raises(ValidationError):
                cards.revoke_card(member, by=SYSTEM, reason=reason)
        assert cards.active_card(member) is not None
        assert not AuditEntry.objects.filter(action=cards.CARD_REVOKED).exists()

    def test_revoke_is_recorded_with_reason(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        card = cards.revoke_card(member, by=SYSTEM, reason="  Petició del soci ")
        assert card.revoked_reason == "Petició del soci"
        entry = AuditEntry.objects.get(action=cards.CARD_REVOKED)
        assert (entry.field, entry.old_value, entry.reason) == (
            "revoked_at",
            None,
            "Petició del soci",
        )
        assert entry.target_id == str(card.pk)

    def test_revoke_without_card_does_nothing(self):
        assert cards.revoke_card(paid_member(), by=SYSTEM, reason="Baixa") is None
        assert not AuditEntry.objects.filter(action=cards.CARD_REVOKED).exists()

    def test_type_change_old_card_not_valid_new_card_valid(self):
        # CA-M01-15. El canvi de tipus el resol la T-M01-17, que ha de cridar `replace_card`
        # dins la seva transacció; aquí es compon amb la primitiva de la T-M01-12.
        member = paid_member()
        old_token = cards.issue_card(member, by=SYSTEM)
        services._change_type(
            member,
            MembershipType.objects.get(code="supporter"),
            by=SYSTEM,
            effective_on=local_today(),
        )
        new_token = cards.replace_card(member, by=SYSTEM, reason="Canvi de tipus")
        assert cards.valid_card_for_token(old_token) is None
        assert cards.valid_card_for_token(new_token).member_id == member.pk
        assert MemberCard.objects.filter(member=member).count() == 2

    def test_replace_is_all_or_nothing(self):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        Member.objects.filter(pk=member.pk).update(status=S.UNPAID)
        with pytest.raises(CardNotAllowed):
            cards.replace_card(member, by=SYSTEM, reason="Canvi de tipus")
        # La revocació es desfà: el carnet continua sense revocar (i «No vàlid» per l'impagat).
        assert cards.active_card(member).token_hash == cards.token_hash(token)
        assert not AuditEntry.objects.filter(action=cards.CARD_REVOKED).exists()


@pytest.mark.parametrize("joined,expected", [(date(1998, 3, 15), 28), (date(1998, 11, 15), 27)])
def test_years_of_membership(joined, expected):
    # RN-M01-21, exemple de M01-7: avui 27/10/2026.
    member = Member(joined_on=joined)
    assert cards.years_of_membership(member, date(2026, 10, 27)) == expected


# --- Pàgina del soci (P13) --------------------------------------------------------------------


def account_for(member, email="anna.soci@example.org"):
    account = Account.objects.create_personal(member.person, email, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


@pytest.fixture
def personal(login_as):
    return lambda member: login_as(account_for(member), AREA_PERSONAL)


def test_without_session_goes_to_the_login(client, db):
    response = client.get(reverse(CARD))
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


def test_admin_session_does_not_enter(login_as, admin_account):
    response = login_as(admin_account, AREA_ADMIN).get(reverse(CARD))
    assert response.status_code == 302


def test_not_a_member_gets_not_found(login_as, db):
    person = Person.objects.create(
        first_name="Convidat", last_name="Prova", origin=Person.Origin.WEB
    )
    account = Account.objects.create_personal(person, "convidat@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    assert login_as(account, AREA_PERSONAL).get(reverse(CARD)).status_code == 404


@pytest.mark.django_db
def test_member_without_card(personal):
    response = personal(make_member(status=S.PENDING)).get(reverse(CARD))
    assert response.status_code == 200
    assert "Ara no tens cap carnet." in response.content.decode()


@pytest.mark.django_db
def test_own_valid_card_and_nothing_of_others(personal):
    other = paid_member("Sentinella", 1999, document="87654321X")
    cards.issue_card(other, by=SYSTEM)
    member = make_member(joined_on=date(1998, 3, 15))
    paid_at = timezone.now()
    pay(add_fee(member), paid_at)
    token = cards.issue_card(member, by=SYSTEM)
    client = personal(member)
    html = client.get(reverse(CARD)).content.decode()
    until = cards.validity(cards.load_member(member.pk), cards.active_card(member)).until
    assert "Vàlid" in html and "No vàlid" not in html
    assert until.strftime("%d/%m/%Y") in html
    assert "1287" in html and member.type.name in html
    assert "Sentinella" not in html and "1999" not in html
    assert token not in html and cards.active_card(member).token_hash not in html
    assert f'href="{reverse(CARD)}" aria-current="page"' in html


@pytest.mark.django_db
def test_unpaid_member_sees_not_valid(personal):
    member = paid_member()
    cards.issue_card(member, by=SYSTEM)
    Member.objects.filter(pk=member.pk).update(status=S.UNPAID)
    html = personal(member).get(reverse(CARD)).content.decode()
    assert "No vàlid" in html


@pytest.mark.django_db
def test_approximate_date_shows_since_year(personal):
    member = paid_member(joined_on=date(1998, 3, 15), joined_on_is_approximate=True)
    cards.issue_card(member, by=SYSTEM)
    # T-DX-61: «Soci des de» al davant del carnet; «~» perquè la data és aproximada.
    html = personal(member).get(reverse(CARD)).content.decode()
    assert "Soci des de" in html and "~1998" in html


@pytest.mark.django_db
def test_new_member_card_never_says_zero_years(personal):
    # Antiguitat (T-DX-60): amb menys d'un any, «Soci des de AAAA», mai «0 anys»; el mateix filtre
    # que l'inici.
    joined = timezone.localdate()
    member = paid_member(joined_on=joined)
    cards.issue_card(member, by=SYSTEM)
    html = personal(member).get(reverse(CARD)).content.decode()
    assert f"Soci des de {joined.year}" in html
    assert "0 anys" not in html


# --- Validesa del 072: exempts, importats i el 29 de febrer (retoc de la T-M01-26) -----------


def exempt_member(birth=date(2015, 5, 1), **kwargs):
    member = make_member(**kwargs)
    Person.objects.filter(pk=member.person_id).update(birth_date=birth)
    return member


@pytest.mark.django_db
class TestValidUntil072:
    def test_paid_member_is_valid_until_the_same_day_of_the_next_year(self):
        # Correcció 1 de la 072: mateix dia de l'any següent, no «+365 dies».
        member = make_member()
        pay(add_fee(member, period=2026), timezone.make_aware(datetime(2026, 3, 10, 12)))
        card = MemberCard.objects.get(
            pk=MemberCard.objects.create(member=member, token_hash="a" * 64).pk
        )
        assert validity(member, card, date(2027, 3, 10)) == cards.CardValidity(
            True, date(2027, 3, 10)
        )
        assert not validity(member, card, date(2027, 3, 11)).valid

    def test_a_29_february_payment_expires_on_28_february(self):
        member = make_member()
        pay(add_fee(member, period=2024), timezone.make_aware(datetime(2024, 2, 29, 12)))
        assert cards.valid_until(cards.load_member(member.pk)) == date(2025, 2, 28)

    def test_exempt_member_is_valid_until_31_december_of_the_last_exempt_year(self):
        # Q-002 (072): nascut el 2015, paga des del 2030; carnet fins al 31/12/2029.
        member = exempt_member()
        token = cards.issue_card(member, by=SYSTEM)
        card = MemberCard.objects.get(token_hash=cards.token_hash(token))
        assert validity(member, card, date(2029, 12, 31)) == cards.CardValidity(
            True, date(2029, 12, 31)
        )
        assert not validity(member, card, date(2030, 1, 1)).valid

    def test_exempt_member_with_a_fee_follows_the_fee(self):
        # Q-003: el primer any de quota ja no compta l'exempció; sense pagar, cap validesa.
        member = exempt_member()
        add_fee(member, period=2030)
        assert cards.valid_until(cards.load_member(member.pk)) is None

    def test_member_without_birth_date_or_fee_has_no_validity(self):
        member = make_member()
        assert cards.valid_until(cards.load_member(member.pk)) is None
        with pytest.raises(CardNotAllowed):
            cards.issue_card(member, by=SYSTEM)

    def test_imported_member_is_valid_one_year_from_cluber_renewal(self):
        # Q-076 (072): des de «Data alta/renovació» [A validar: tresorer].
        member = make_member(cluber_id="CLB-1", cluber_renewed_on=date(2024, 2, 29))
        assert cards.valid_until(cards.load_member(member.pk)) == date(2025, 2, 28)
        member = make_member(
            first="Berta",
            number=88,
            document="87654321X",
            cluber_id="CLB-2",
            cluber_renewed_on=date(2026, 6, 15),
        )
        token = cards.issue_card(member, by=SYSTEM)
        card = MemberCard.objects.get(token_hash=cards.token_hash(token))
        assert validity(member, card, date(2027, 6, 15)).valid
        assert not validity(member, card, date(2027, 6, 16)).valid

    def test_a_platform_payment_after_cluber_wins_if_later(self):
        member = make_member(cluber_id="CLB-3", cluber_renewed_on=date(2025, 1, 10))
        pay(add_fee(member, period=2026), timezone.make_aware(datetime(2026, 2, 1, 12)))
        assert cards.valid_until(cards.load_member(member.pk)) == date(2027, 2, 1)

    def test_cluber_renewal_only_for_cluber_members(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            make_member(cluber_renewed_on=date(2026, 1, 1))

    def test_summary_gives_the_same_valid_until(self):
        member = exempt_member()
        assert services.get_member_summary(member.person).valid_until == date(2029, 12, 31)


# --- Darrere del carnet i exempts (retoc de la T-M01-19, 072) --------------------------------


@pytest.mark.django_db
def test_card_back_shows_the_wireframe_content(personal):
    # Q-065: tipus, alta, quota, llicència i text legal; sense cap marca [A validar].
    member = make_member(joined_on=date(2019, 3, 12))
    paid = timezone.make_aware(datetime(2026, 3, 10, 12))
    pay(add_fee(member), paid)
    cards.issue_card(member, by=SYSTEM)
    html = personal(member).get(reverse(CARD)).content.decode()
    assert "Darrere del carnet" in html
    assert member.type.name in html and "12/03/2019" in html
    assert "Pagada fins al 10/03/2027" in html
    assert "Carnet personal i intransferible" in html and "cris@cris.es" in html
    # Decisió 085 (J-6): el NIF del club al darrere del carnet.
    assert "NIF V08591042" in html
    assert "A validar" not in html


@pytest.mark.django_db
def test_exempt_member_card_page(personal):
    # Q-002: vàlid fins al 31/12 de l'últim any exempt.
    member = exempt_member(birth=date(2015, 5, 1))
    cards.issue_card(member, by=SYSTEM)
    html = personal(member).get(reverse(CARD)).content.decode()
    assert "Exempt per edat fins al 31/12/2029" in html
    assert "Vàlid fins al" in html


# --- Importats sense data d'alta (retoc de la T-M01-25, 072, Q-075) --------------------------


@pytest.mark.django_db
def test_only_an_imported_member_may_lack_the_join_date():
    with pytest.raises(IntegrityError), transaction.atomic():
        make_member(joined_on=None)


@pytest.mark.django_db
def test_imported_member_without_join_date_shows_no_seniority(personal, admin_account):
    from apps.core.models import ImportBatch
    from apps.members import roster
    from apps.members.tests.test_cluber_preview import make_batch

    batch = make_batch(admin_account, ImportBatch.Status.CONFIRMED)
    member = make_member(
        joined_on=None,
        import_batch=batch,
        cluber_id="CLB-1",
        cluber_renewed_on=local_today() - timedelta(days=30),
    )
    assert cards.years_of_membership(member) is None
    cards.issue_card(member, by=SYSTEM)  # Q-076: vàlid des de la renovació de Cluber
    html = personal(member).get(reverse(CARD)).content.decode()
    assert "Anys de soci" not in html and "Vàlid" in html and "No vàlid" not in html
    assert roster.export_row(member, [("joined_on", "Data d'alta")]) == [""]
