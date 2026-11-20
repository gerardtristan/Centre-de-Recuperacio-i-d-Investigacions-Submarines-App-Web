"""T-M09-03: categories de despesa i proveïdors. Només dades inventades."""

import pytest
from django.db import IntegrityError, transaction

from apps.expenses.models import ExpenseCategory, Supplier

pytestmark = pytest.mark.django_db


def test_categories_inicials_de_f_7_actives():
    assert set(ExpenseCategory.objects.filter(active=True).values_list("name", flat=True)) == {
        "Embarcació",
        "Aire",
        "Lloguer",
        "Instructor",
        "Taxa",
        "Instal·lacions",
        "Altres",
    }


def test_una_categoria_nova_s_afegeix_com_a_dada_i_el_nom_es_unic():
    ExpenseCategory.objects.create(name="Revisions")
    with pytest.raises(IntegrityError), transaction.atomic():
        ExpenseCategory.objects.create(name="Revisions")


def test_proveidor_amb_nom_i_nif_opcional():
    supplier = Supplier.objects.create(name="Nàutica Inventada SL")
    assert (supplier.tax_id, supplier.active, str(supplier)) == ("", True, "Nàutica Inventada SL")
    assert str(ExpenseCategory.objects.get(name="Aire")) == "Aire"
