"""Referència de transferència (T-M04-10; RN-T20; VT-03): l'algorisme del caràcter de control i
el servei `treasury.transfer_reference`. Només dades inventades."""

import inspect
import itertools
import re

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction

from apps.core import audit, charges
from apps.core.models import AppendOnlyError, AuditEntry, Person
from apps.treasury import references, services
from apps.treasury.models import TransferReference
from conftest import CommittedDataTestCase, run_together

A = references.ALPHABET
SYSTEM = audit.system("proves-t-m04-10")


class TestAlgorithm:
    def test_vt_03_alphabet_without_characters_that_get_confused(self):
        assert len(A) == len(set(A)) == 32
        assert not set("0O1I") & set(A)

    def test_luhn_mod_n_gives_the_published_example(self):
        # Exemple de l'algorisme Luhn mod N (alfabet «abcdef», entrada «abcdef» → «e»).
        assert references.check_character("abcdef", alphabet="abcdef") == "e"

    @pytest.mark.parametrize("code", ["22222", "ZZZZZ", "7K3Q9", "A2B3C"])
    def test_every_single_changed_character_is_detected(self, code):
        check = references.check_character(code)
        for pos, char in itertools.product(range(len(code)), A):
            if char != code[pos]:
                changed = code[:pos] + char + code[pos + 1 :]
                assert references.check_character(changed) != check, changed

    def test_every_swap_of_neighbours_is_detected_except_2_and_z(self):
        """La limitació coneguda de Luhn mod N: el primer i el darrer caràcter de l'alfabet."""
        missed = set()
        for a, b in itertools.permutations(A, 2):
            for pos in range(4):
                code = ["X"] * 5
                code[pos], code[pos + 1] = a, b
                swapped = code.copy()
                swapped[pos], swapped[pos + 1] = b, a
                if references.check_character("".join(code)) == references.check_character(
                    "".join(swapped)
                ):
                    missed.add(frozenset((a, b)))
        assert missed == {frozenset("2Z")}


class TestReference:
    def test_vt_03_shape_prefix_five_characters_and_control(self, settings):
        settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
        for _ in range(50):
            reference = references.new_reference()
            assert re.fullmatch(rf"CRIS-[{A}]{{5}}-[{A}]", reference)
            assert references.is_valid(reference)

    @pytest.mark.parametrize(
        "reference",
        ["CRIS-7K3Q9-X", "ALTRE-7K3Q9-{c}", "cris-7K3Q9-{c}", "CRIS-7K3Q-{c}", "CRIS7K3Q9{c}"]
        + ["CRIS-7K3O9-{c}", "CRIS-7K3Q9-{c}-2", "", "CRIS--{c}"],
    )
    def test_anything_else_is_not_a_valid_reference(self, settings, reference):
        settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
        check = references.check_character("7K3Q9")
        assert check != "X"
        assert references.is_valid(f"CRIS-7K3Q9-{check}")
        assert not references.is_valid(reference.format(c=check))

    def test_the_longest_prefix_still_fits_in_twenty_characters(self, settings):
        settings.TRANSFER_REFERENCE_PREFIX = "A" * 12
        assert len(references.new_reference()) == 20

    @pytest.mark.parametrize("prefix", ["", "cris", "CR-IS", "A" * 13, "CRÍS"])
    def test_a_wrong_prefix_is_a_configuration_error(self, settings, prefix):
        settings.TRANSFER_REFERENCE_PREFIX = prefix
        with pytest.raises(ImproperlyConfigured):
            references.new_reference()


def new_charge(person):
    return charges.create_charge(
        person, kind="fee", amount_cents=9000, concept="Quota", origin="proves", by=SYSTEM
    )


@pytest.mark.django_db
class TestService:
    @pytest.fixture
    def charge(self, make_person):
        return new_charge(make_person("Núria", "Coll"))

    def test_m04_8_contract(self):
        assert services.transfer_reference is references.transfer_reference
        assert list(inspect.signature(services.transfer_reference).parameters) == ["charge"]

    def test_rn_t20_created_the_first_time_and_never_changes(self, charge):
        reference = services.transfer_reference(charge)
        assert references.is_valid(reference)
        assert services.transfer_reference(charge) == reference
        assert TransferReference.objects.get().reference == reference
        entry = AuditEntry.objects.get(action=references.REFERENCE_CREATED)
        assert entry.details == {"charge": charge.pk, "reference": reference}

    def test_rn_t20_one_per_charge_and_unique(self, charge, make_person):
        other = new_charge(make_person("Pere", "Prova"))
        assert services.transfer_reference(charge) != services.transfer_reference(other)
        with pytest.raises(IntegrityError), transaction.atomic():
            TransferReference.objects.create(charge=charge, reference="CRIS-22222-2")

    def test_rn_t20_the_row_is_never_modified(self, charge):
        services.transfer_reference(charge)
        row = TransferReference.objects.get()
        row.reference = "CRIS-22222-2"
        with pytest.raises(AppendOnlyError):
            row.save()
        with pytest.raises(AppendOnlyError):
            row.delete()

    def test_a_code_already_taken_is_drawn_again(self, charge, make_person, monkeypatch):
        taken = services.transfer_reference(charge)
        fresh = "CRIS-7K3Q9-" + references.check_character("7K3Q9")
        drawn = iter([taken, fresh])
        monkeypatch.setattr(references, "new_reference", lambda: next(drawn))
        assert services.transfer_reference(new_charge(make_person("Pere", "Prova"))) == fresh

    def test_if_every_draw_is_taken_it_fails_and_creates_nothing(
        self, charge, make_person, monkeypatch
    ):
        taken = services.transfer_reference(charge)
        monkeypatch.setattr(references, "new_reference", lambda: taken)
        other = new_charge(make_person("Pere", "Prova"))
        with transaction.atomic():  # la transacció de qui crida continua
            with pytest.raises(IntegrityError):
                services.transfer_reference(other)
            assert TransferReference.objects.count() == 1


class TestSimultaneous(CommittedDataTestCase):
    def test_rn_t20_two_first_requests_at_once_give_the_same_reference(self):
        person = Person.objects.create(first_name="Núria", last_name="Coll", origin="web")
        charge = new_charge(person)
        first, second = run_together([lambda: services.transfer_reference(charge)] * 2)
        assert first == second
        assert TransferReference.objects.filter(charge=charge).count() == 1
