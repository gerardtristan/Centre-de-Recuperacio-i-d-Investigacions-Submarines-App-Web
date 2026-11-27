"""Ajustos del 07 (T-M07-03; M07-6, «Valors configurables»). Per valor: fora de rang es rebutja,
el canvi queda al registre amb el valor anterior i sense permís és «no trobat». Els permisos
per rol i les pantalles són a `core/tests/test_permissions_07_08.py` (T-M07-02). Només dades
inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.core import business_settings
from apps.core.models import AuditEntry, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
R = Role.Code
SECTION = business_settings.section_code("website")

# Clau: (valor inicial, valor vàlid, valors fora de rang o de tipus).
VALUES = {
    "website.home_activities_count": (6, 12, [0, 13, "6"]),
    "website.news_on_home": (3, 0, [-1, 11]),
    "website.newsletter_enabled": (False, True, ["sí", 1]),
    "website.newsletter_confirm_hours": (48, 168, [0, 169]),
    "website.contact_enabled": (False, True, ["sí", 1]),
    "website.contact_retention_months": (6, 24, [0, 25]),
    "website.club_contact": ("", "Carrer Inventat 1, Barcelona", ["x" * 501, 5]),
}


def test_the_section_has_its_values_with_the_switches_off():
    settings = Setting.objects.filter(module="website")
    # L'interruptor de les fotos públiques (D2, `website/0008`) encara no té permís al catàleg del
    # nucli: ningú no el pot canviar, i no entra a les proves de rang.
    # Els de l'editor (decisió 106, `website/0011`) també esperen el seu permís (torn del nucli);
    # els rangs es comproven a `test_blocks_106.py`.
    switches = {
        "website.public_images_enabled": False,
        "website.youtube_enabled": False,
        "website.review_flow_enabled": False,
        "website.autosave_seconds": 20,
        "website.upload_max_mb": 10,
        "website.youtube_notice": "En prémer, es carrega YouTube (Google)",  # T-M07-23, P-574
        "website.video_upload_enabled": False,  # T-M07-23, P-610
    }
    assert {s.key: s.initial_value for s in settings} == {
        **{k: v[0] for k, v in VALUES.items()},
        **switches,
    }
    assert not any(s.affects_money or s.effective_dated for s in settings)
    assert business_settings.get("website.newsletter_enabled") is False
    assert business_settings.get("website.contact_enabled") is False


@pytest.mark.parametrize("key", VALUES)
def test_out_of_range_is_rejected_and_nothing_is_saved(make_admin, key):  # noqa: F811
    account = make_admin(R.ADMINISTRATOR)
    for value in VALUES[key][2]:
        with pytest.raises(ValidationError):
            business_settings.change(key, value, account, "Prova")
    assert not Setting.objects.get(key=key).versions.exists()


@pytest.mark.parametrize("key", VALUES)
def test_a_valid_change_is_recorded_with_the_previous_value(make_admin, key):  # noqa: F811
    initial, valid, _wrong = VALUES[key]
    account = make_admin(R.ADMINISTRATOR)
    business_settings.change(key, valid, account, "Prova")
    assert business_settings.get(key) == valid
    entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED, field=key)
    assert (entry.actor_account_id, entry.old_value, entry.new_value) == (
        account.pk, initial, valid,
    )  # fmt: skip


@pytest.mark.parametrize("key", VALUES)
def test_a_role_without_the_section_gets_not_found(make_admin, key):  # noqa: F811
    with pytest.raises(Http404):
        business_settings.change(key, VALUES[key][1], make_admin(R.SECRETARY), "Prova")
    assert business_settings.get(key) == VALUES[key][0]
