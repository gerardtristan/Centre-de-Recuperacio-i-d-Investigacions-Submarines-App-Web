"""Models del M01 (T-M01-11): restriccions i índexs comprovats a la base de dades.

Cada restricció es prova amb una escriptura que la base de dades ha de rebutjar, no amb
`full_clean`. Només dades inventades.
"""

import datetime
import hashlib
import re

import pytest
from django.db import DatabaseError, IntegrityError, connection, transaction

from apps.core.charges import create_charge
from apps.core.models import AppendOnlyError, Person, UndeletableError
from apps.members.models import (
    AnnualFee,
    LicenceRecord,
    Member,
    MemberCard,
    MemberRequest,
    MembershipNumberCounter,
    MembershipType,
    MemberStatusChange,
)
from conftest import CommittedDataTestCase, run_together

TODAY = datetime.date(2026, 11, 4)
HASH = hashlib.sha256(b"testimoni-inventat").hexdigest()


def rejected(make, error=IntegrityError):
    """La base de dades rebutja l'escriptura (dins d'un punt de desat, per poder continuar)."""
    with pytest.raises(error), transaction.atomic():
        make()


@pytest.fixture
def supporter(db):
    return MembershipType.objects.get(code="supporter")


@pytest.fixture
def full(db):
    return MembershipType.objects.get(code="full")


@pytest.fixture
def make_member(make_person, supporter):
    def make(person=None, **fields):
        fields.setdefault("type", supporter)
        fields.setdefault("joined_on", TODAY)
        return Member.objects.create(person=person or make_person(), **fields)

    return make


@pytest.fixture
def member(make_member):
    return make_member(member_number=87)


class TestMembershipType:
    def test_initial_types_and_prices(self, db):
        # VC-01: 3500 i 9000 cèntims, validats pel responsable del projecte el 03/11/2026.
        types = {
            t.code: (t.name, t.annual_fee_cents, t.active) for t in MembershipType.objects.all()
        }
        assert types == {
            "supporter": ("Simpatitzant", 3500, True),
            "full": ("Ple dret", 9000, True),
        }

    def test_code_is_unique(self, supporter):
        rejected(
            lambda: MembershipType.objects.create(code="supporter", name="X", annual_fee_cents=1)
        )

    def test_fee_must_be_positive(self, db):
        rejected(lambda: MembershipType.objects.create(code="zero", name="X", annual_fee_cents=0))
        assert MembershipType.objects.create(code="one", name="X", annual_fee_cents=1).pk


class TestMember:
    def test_one_member_per_person(self, make_member, make_person):
        person = make_person()
        make_member(person)
        rejected(lambda: make_member(person))

    def test_member_number_is_unique_when_set(self, make_member):
        make_member(member_number=None)
        make_member(member_number=None)
        make_member(member_number=1287)
        rejected(lambda: make_member(member_number=1287))

    def test_cluber_id_is_unique_when_set(self, make_member):
        make_member(cluber_id=None)
        make_member(cluber_id=None)
        make_member(cluber_id="C-0001")
        rejected(lambda: make_member(cluber_id="C-0001"))

    def test_status_must_be_known(self, make_member):
        rejected(lambda: make_member(status="expelled"))

    def test_defaults(self, make_member):
        new = make_member()
        assert (new.status, new.joined_on_is_approximate, new.left_on) == ("pending", False, None)

    def test_avatar_seed_is_random_not_from_the_name(self, make_member, make_person):
        # RN-M01-30 amb la lectura de la 060: el mateix nom no dona la mateixa llavor.
        first = make_member(make_person("Anna", "Puig"))
        second = make_member(make_person("Anna", "Puig"))
        assert re.fullmatch(r"[0-9a-f]{64}", first.avatar_seed)
        assert first.avatar_seed != second.avatar_seed

    def test_avatar_seed_never_changes(self, member):
        other_seed = "0" * 64
        member.avatar_seed = other_seed
        with pytest.raises(DatabaseError, match="llavor"), transaction.atomic():
            member.save()
        with pytest.raises(DatabaseError, match="llavor"), transaction.atomic():
            Member.objects.filter(pk=member.pk).update(avatar_seed=other_seed)
        with pytest.raises(DatabaseError, match="llavor"), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE members_member SET avatar_seed = %s WHERE id = %s",
                    [other_seed, member.pk],
                )

    @pytest.mark.parametrize(
        "bad_seed",
        ["", "abc", "A" * 64, "g" * 64, "0" * 63, "0" * 65, " " + "0" * 63],
        ids=["buida", "curta", "majuscules", "no-hex", "63", "65", "espai"],
    )
    def test_avatar_seed_must_be_64_lowercase_hex(self, make_member, bad_seed):
        # Només el format de token_hex(32); no demostra que sigui aleatòria.
        # 65 caràcters ja els rebutja la longitud de la columna (DataError).
        rejected(lambda: make_member(avatar_seed=bad_seed), DatabaseError)

    def test_anonymising_other_data_is_not_blocked(self, member):
        # El disparador i el format només afecten la llavor (T-M01-22 pot anonimitzar la resta).
        seed = member.avatar_seed
        Person.objects.filter(pk=member.person_id).update(first_name="Anònim", last_name="")
        Member.objects.filter(pk=member.pk).update(cluber_id=None)
        member.refresh_from_db()
        assert member.avatar_seed == seed

    def test_saving_other_fields_keeps_the_seed(self, member):
        seed = member.avatar_seed
        member.status = Member.Status.ACTIVE
        member.save()
        Member.objects.filter(pk=member.pk).update(left_on=TODAY)
        member.refresh_from_db()
        assert (member.status, member.left_on, member.avatar_seed) == ("active", TODAY, seed)


class TestMembershipNumberCounter:
    def test_single_row_created_at_zero(self, db):
        assert list(MembershipNumberCounter.objects.values_list("pk", "last_number")) == [(1, 0)]

    def test_second_row_is_rejected(self, db):
        rejected(lambda: MembershipNumberCounter.objects.create(last_number=5))

    def test_negative_value_is_rejected(self, db):
        rejected(lambda: MembershipNumberCounter.objects.update(last_number=-1))


class TestMemberStatusChange:
    def change(self, member, **fields):
        fields.setdefault("to_status", "active")
        fields.setdefault("to_type", member.type)
        fields.setdefault("effective_on", TODAY)
        return MemberStatusChange.objects.create(member=member, **fields)

    def test_activation_needs_no_reason(self, member):
        assert self.change(member, from_status="pending", to_status="active").pk

    @pytest.mark.parametrize(
        ("from_status", "to_status"),
        [("active", "left"), ("active", "unpaid"), ("unpaid", "active")],
    )
    @pytest.mark.parametrize("reason", ["", "   "])
    def test_reason_required_for_leaving_and_unpaid(self, member, from_status, to_status, reason):
        rejected(
            lambda: self.change(member, from_status=from_status, to_status=to_status, reason=reason)
        )
        assert self.change(member, from_status=from_status, to_status=to_status, reason="Motiu").pk

    def test_status_must_be_known(self, member):
        rejected(lambda: self.change(member, to_status="expelled"))
        rejected(lambda: self.change(member, from_status="expelled"))

    def test_orm_cannot_change_or_delete(self, member):
        entry = self.change(member)
        entry.reason = "canvi"
        with pytest.raises(AppendOnlyError):
            entry.save()
        with pytest.raises(AppendOnlyError):
            entry.delete()
        with pytest.raises(AppendOnlyError):
            MemberStatusChange.objects.update(reason="canvi")
        with pytest.raises(AppendOnlyError):
            MemberStatusChange.objects.all().delete()

    @pytest.mark.parametrize(
        "sql",
        [
            "UPDATE members_memberstatuschange SET reason = 'canvi' WHERE id = %s",
            "DELETE FROM members_memberstatuschange WHERE id = %s",
        ],
    )
    def test_database_rejects_direct_update_and_delete(self, member, sql):
        entry = self.change(member)
        with pytest.raises(DatabaseError, match="historial del soci"), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql, [entry.pk])

    def test_database_rejects_truncate(self, member):
        self.change(member)
        with pytest.raises(DatabaseError, match="TRUNCATE"), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE members_memberstatuschange")


class TestMemberRequest:
    def request(self, person, **fields):
        fields.setdefault("kind", "join")
        fields.setdefault("channel", "web")
        if fields["kind"] in ("join", "change_type"):
            fields.setdefault("requested_type", MembershipType.objects.get(code="supporter"))
        return MemberRequest.objects.create(person=person, **fields)

    def test_rejected_leave_keeps_both_reasons(self, member):
        # CA-M01-47.
        leave = self.request(
            member.person, kind="leave", member=member, request_reason="Canvi de ciutat"
        )
        leave.status = "rejected"
        leave.resolution_reason = "Quota pendent de revisar"
        leave.save()
        leave.refresh_from_db()
        assert (leave.request_reason, leave.resolution_reason) == (
            "Canvi de ciutat",
            "Quota pendent de revisar",
        )

    @pytest.mark.parametrize("reason", ["", "   "])
    def test_leave_needs_request_reason(self, member, reason):
        rejected(
            lambda: self.request(member.person, kind="leave", member=member, request_reason=reason)
        )

    @pytest.mark.parametrize("reason", ["", "   "])
    def test_rejection_needs_resolution_reason(self, make_person, reason):
        rejected(lambda: self.request(make_person(), status="rejected", resolution_reason=reason))

    @pytest.mark.parametrize("status", ["pending", "approved", "cancelled"])
    def test_other_statuses_need_no_resolution_reason(self, make_person, status):
        assert self.request(make_person(), status=status).pk

    def test_only_one_pending_per_person_and_kind(self, member):
        person = member.person
        self.request(person)
        rejected(lambda: self.request(person))
        assert self.request(person, kind="change_type", member=member).pk
        self.request(person, status="approved")
        self.request(person, status="rejected", resolution_reason="Duplicada")

    def test_requested_type_depends_on_kind(self, member, supporter):
        rejected(lambda: self.request(member.person, requested_type=None))
        rejected(
            lambda: self.request(
                member.person, kind="change_type", member=member, requested_type=None
            )
        )
        rejected(
            lambda: self.request(
                member.person,
                kind="leave",
                member=member,
                request_reason="Motiu",
                requested_type=supporter,
            )
        )

    def test_member_required_for_change_type_and_leave(self, make_person):
        person = make_person()
        rejected(lambda: self.request(person, kind="change_type"))
        rejected(lambda: self.request(person, kind="leave", request_reason="Motiu"))
        assert self.request(person, kind="join").member is None

    def test_person_must_be_the_members_person(self, member, make_person):
        # Clau forana composta (member, person) → (id, person): la base de dades la comprova a
        # l'instant, dins del mateix punt de desat.
        rejected(lambda: self.request(make_person("Pere"), kind="change_type", member=member))
        assert self.request(member.person, kind="change_type", member=member).pk

    @pytest.mark.parametrize(
        ("field", "value"), [("kind", "transfer"), ("channel", "phone"), ("status", "lost")]
    )
    def test_choices_must_be_known(self, make_person, field, value):
        rejected(lambda: self.request(make_person(), **{field: value}))

    def test_created_at_is_set(self, make_person):
        assert self.request(make_person()).created_at is not None


class TestMemberCard:
    def test_token_hash_is_unique(self, member, make_member):
        MemberCard.objects.create(member=member, token_hash=HASH)
        rejected(lambda: MemberCard.objects.create(member=make_member(), token_hash=HASH))

    @pytest.mark.parametrize("value", ["", "abc", HASH.upper(), HASH[:-1] + "g", HASH + "0"])
    def test_token_hash_has_sha256_hex_format(self, member, value):
        # Format coherent amb SHA-256 en hexadecimal. No garanteix que no es desi el testimoni
        # en clar: generar-lo i resumir-lo és del servei del carnet (T-M01-19).
        rejected(lambda: MemberCard.objects.create(member=member, token_hash=value), DatabaseError)

    def test_one_non_revoked_card_per_member(self, member):
        card = MemberCard.objects.create(member=member, token_hash=HASH)
        other = hashlib.sha256(b"altre").hexdigest()
        # 079 (RN-M01-85): cada carnet del soci té la seva versió.
        rejected(lambda: MemberCard.objects.create(member=member, token_hash=other, version=2))
        card.revoked_at = card.issued_at
        card.revoked_reason = "Canvi de tipus"
        card.save()
        assert MemberCard.objects.create(member=member, token_hash=other, version=2).pk

    @pytest.mark.parametrize(
        ("revoked", "reason"), [(True, ""), (True, "   "), (False, "Motiu sense data")]
    )
    def test_revocation_date_and_reason_go_together(self, member, revoked, reason):
        revoked_at = datetime.datetime(2026, 11, 4, tzinfo=datetime.UTC) if revoked else None
        rejected(
            lambda: MemberCard.objects.create(
                member=member, token_hash=HASH, revoked_at=revoked_at, revoked_reason=reason
            )
        )


class TestLicenceRecord:
    def record(self, member, **fields):
        fields.setdefault("licence_type", "Aficionat")
        fields.setdefault("issued_on", TODAY)
        fields.setdefault("source", "manual")
        return LicenceRecord.objects.create(member=member, **fields)

    def test_expiry_not_before_issue(self, member):
        rejected(lambda: self.record(member, expires_on=TODAY - datetime.timedelta(days=1)))
        assert self.record(member, expires_on=TODAY).pk

    def test_unknown_expiry_is_allowed(self, member):
        # Addenda de la 058: caducitat desconeguda.
        assert self.record(member, expires_on=None).expires_on is None

    def test_source_must_be_known(self, member):
        rejected(lambda: self.record(member, source="licences"))

    def test_licence_type_is_free_text_up_to_100(self, member):
        assert self.record(member, licence_type="x" * 100).pk
        rejected(lambda: self.record(member, licence_type="x" * 101), DatabaseError)


class TestAnnualFee:
    def charge(self, member):
        return create_charge(
            member.person,
            kind="fee",
            amount_cents=3500,
            concept="Quota 2027",
            origin="members",
            by=None,
        )

    def fee(self, member, charge=None, **fields):
        fields.setdefault("period", 2027)
        fields.setdefault("kind", "annual")
        fields.setdefault("due_on", datetime.date(2027, 1, 31))
        return AnnualFee.objects.create(
            member=member, charge=charge or self.charge(member), **fields
        )

    def test_unique_per_member_period_and_kind(self, member):
        self.fee(member)
        rejected(lambda: self.fee(member))
        assert self.fee(member, kind="type_change_supplement").pk
        assert self.fee(member, period=2028).pk

    def test_kind_must_be_known(self, member):
        rejected(lambda: self.fee(member, kind="donation"))

    def test_one_fee_per_charge(self, member):
        fee = self.fee(member)
        rejected(lambda: self.fee(member, charge=fee.charge, period=2028))

    def test_cannot_be_deleted(self, member):
        fee = self.fee(member)
        with pytest.raises(UndeletableError):
            fee.delete()
        with pytest.raises(UndeletableError):
            AnnualFee.objects.all().delete()


class TestConcurrentPendingRequests(CommittedDataTestCase):
    # Amb soci: la neteja final també passa per la clau forana composta (conftest.py).
    def test_two_simultaneous_pending_requests_store_only_one(self):
        person = Person.objects.create(
            first_name="Anna", last_name="Puig", origin=Person.Origin.WEB
        )
        full = MembershipType.objects.get(code="full")
        member = Member.objects.create(
            person=person, type=MembershipType.objects.get(code="supporter"), joined_on=TODAY
        )

        def submit():
            try:
                with transaction.atomic():
                    MemberRequest.objects.create(
                        person=person,
                        member=member,
                        kind="change_type",
                        channel="web",
                        requested_type=full,
                    )
                return "desada"
            except IntegrityError:
                return "rebutjada"

        assert sorted(run_together([submit, submit])) == ["desada", "rebutjada"]
        assert MemberRequest.objects.filter(person=person, status="pending").count() == 1
