"""T-M03-17a (nucli): el tipus de lot «equipment» per a la càrrega inicial de l'inventari del 03
(P-M03-G). Només dades inventades."""

import pytest
from django.db import IntegrityError, transaction

from apps.core import imports
from apps.core.models import ImportBatch

pytestmark = pytest.mark.django_db


def test_an_equipment_batch_is_a_valid_kind(make_admin):
    by = make_admin("equipment_manager")
    batch = imports.open_confirmed(
        ImportBatch.Kind.EQUIPMENT, file_sha256="a" * 64, by=by, counts={"new_count": 0}
    )
    assert batch.kind == "equipment"
    with transaction.atomic(), pytest.raises(IntegrityError):
        imports.open_confirmed("inventat", file_sha256="b" * 64, by=by, counts={"new_count": 0})
