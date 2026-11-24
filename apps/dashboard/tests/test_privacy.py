"""Supressió de grups petits (T-M08-03; RN-M08-02; CA-M08-03; P-487)."""

import pytest

from apps.core import business_settings
from apps.core.models import Setting
from apps.dashboard import privacy
from apps.dashboard.privacy import BELOW, HIDDEN, SHOWN, Cell, suppress


def states(cells):
    return {key: (cell.value, cell.state) for key, cell in cells.items()}


def labels(cells, n=3):
    return [cell.label(n) for cell in cells.values()]


def test_ca_m08_03_two_small_cells_say_less_than_n_and_the_total_is_shown():
    cells, total = suppress({"A": 120, "B": 40, "C": 2, "D": 1}, 3)
    assert labels(cells) == ["120", "40", "menys de 3", "menys de 3"]
    assert total == Cell(163, SHOWN) and total.label(3) == "163"


def test_ca_m08_03_one_small_cell_also_hides_the_next_smallest():
    cells, total = suppress({"A": 120, "B": 40, "C": 7, "D": 2}, 3)
    assert states(cells) == {
        "A": (120, SHOWN), "B": (40, SHOWN), "C": (7, HIDDEN), "D": (2, BELOW),
    }  # fmt: skip
    assert labels(cells) == ["120", "40", "amagat", "menys de 3"]
    assert total.label(3) == "169"


def test_nothing_is_hidden_when_every_cell_reaches_the_minimum():
    cells, total = suppress({"A": 3, "B": 10}, 3)
    assert states(cells) == {"A": (3, SHOWN), "B": (10, SHOWN)}
    assert total == Cell(13, SHOWN)


def test_a_tie_for_the_next_smallest_hides_the_first_in_order():
    cells, _ = suppress({"A": 5, "B": 1, "C": 5}, 3)
    assert states(cells) == {"A": (5, HIDDEN), "B": (1, BELOW), "C": (5, SHOWN)}


def test_zero_is_also_less_than_n():
    cells, _ = suppress({"A": 0, "B": 9, "C": 4}, 3)
    assert states(cells) == {"A": (0, BELOW), "B": (9, SHOWN), "C": (4, HIDDEN)}


def test_two_cells_one_small_hides_both_and_keeps_the_total():
    cells, total = suppress({"A": 120, "B": 2}, 3)
    assert states(cells) == {"A": (120, HIDDEN), "B": (2, BELOW)}
    assert total == Cell(122, SHOWN)


def test_a_single_small_cell_hides_the_total_too():
    cells, total = suppress({"A": 2}, 3)
    assert states(cells) == {"A": (2, BELOW)}
    assert total.label(3) == "menys de 3"


def test_a_single_big_cell_shows_everything():
    cells, total = suppress({"A": 8}, 3)
    assert states(cells) == {"A": (8, SHOWN)} and total == Cell(8, SHOWN)


def test_an_empty_breakdown():
    assert suppress({}, 3) == ({}, Cell(0, SHOWN))


@pytest.mark.parametrize("n", [2, 10])
def test_the_minimum_is_a_parameter(n):
    cells, _ = suppress({"A": 9, "B": 9, "C": 1}, n)
    assert labels(cells, n)[2] == f"menys de {n}"
    assert [cell.state for cell in cells.values()] == (
        [HIDDEN, SHOWN, BELOW] if n == 2 else [BELOW, BELOW, BELOW]
    )


@pytest.mark.django_db
def test_p487_the_minimum_is_a_setting_of_3_from_2_to_10():
    setting = Setting.objects.get(key=privacy.MIN_GROUP_SIZE)
    assert (setting.module, setting.value_type, setting.min_value, setting.max_value) == (
        "dashboard", "integer", 2, 10,
    )  # fmt: skip
    assert privacy.min_group_size() == 3 == business_settings.get(privacy.MIN_GROUP_SIZE)
