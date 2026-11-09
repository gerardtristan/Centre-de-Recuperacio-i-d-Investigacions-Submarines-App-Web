"""Camps opcionals del perfil (072, P-58): telèfon fix i adreça desglossada. Mai obligatoris
per ser soci; el soci i la secretaria amb permís els poden editar, amb registre (RN-50).
Només dades inventades."""

import pytest

from apps.core import audit, persons
from apps.core.models import AuditEntry, Person

SYSTEM = audit.system("proves")


@pytest.mark.django_db
def test_optional_fields_are_blank_by_default_and_editable_from_the_profile():
    person = Person.objects.create(first_name="Ona", last_name="Prova", origin="web")
    assert (person.landline, person.postal_code, person.city, person.province) == ("", "", "", "")
    persons.update_profile(
        person,
        actor=SYSTEM,
        landline="933000000",
        postal_code="08001",
        city="Barcelona",
        province="Barcelona",
    )
    person.refresh_from_db()
    assert (person.postal_code, person.city, person.province) == ("08001", "Barcelona", "Barcelona")
    fields = set(
        AuditEntry.objects.filter(target_id=str(person.pk)).values_list("field", flat=True)
    )
    assert {"landline", "postal_code", "city", "province"} <= fields


def test_nationality_and_profession_are_not_collected():
    # Decisió del responsable (072): fora del perfil fins que hi hagi una finalitat.
    names = {f.name for f in Person._meta.get_fields()}
    assert not names & {"nationality", "profession", "observations"}
