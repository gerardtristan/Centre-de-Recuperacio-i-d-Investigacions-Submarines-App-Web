"""P-291 (095, provisional fins que el banc ho confirmi): els codis de retorn i l'acció de cada un
són ajustos editables, amb els valors per defecte de RN-M05b-15. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import AuditEntry, Role, SettingVersion
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.payments import returns
from apps.payments.models import SepaMandate
from apps.payments.tests.test_remittance_settlement import (  # noqa: F401 (fixtures)
    club,
    sent,
    treasurer,
)
from apps.payments.tests.test_remittances import signer, text  # noqa: F401 (fixtures)
from apps.payments.tests.test_returns import collected  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db

RETRY, BLOCK = returns.RETRY_CODES, returns.BLOCK_CODES


def test_valors_per_defecte_de_rn_m05b_15():
    assert business_settings.get(RETRY) == "AM04"
    assert business_settings.get(BLOCK) == "AC04, MD01"
    assert returns.codes(BLOCK) == {"AC04", "MD01"}


def test_un_codi_passat_de_bloquejar_a_reintent_canvia_la_proposta(collected, treasurer):  # noqa: F811
    business_settings.change(BLOCK, "AC04", treasurer)
    business_settings.change(RETRY, "AM04,MD01", treasurer, note="Prova")

    assert returns.register_return(collected[0], "MD01", by=treasurer) == returns.RETRY
    collected[0].mandate.refresh_from_db()
    assert collected[0].mandate.status == SepaMandate.Status.ACTIVE  # ja no el bloqueja
    entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED, field=RETRY)
    assert (entry.old_value, entry.new_value, entry.reason) == ("AM04", "AM04,MD01", "Prova")


def test_un_codi_nou_que_bloqueja_el_mandat(collected, treasurer):  # noqa: F811
    business_settings.change(BLOCK, "AC04 MD01 MS02", treasurer)

    assert returns.register_return(collected[1], "MS02", by=treasurer) == returns.SENT
    collected[1].mandate.refresh_from_db()
    assert collected[1].mandate.status == SepaMandate.Status.BLOCKED


@pytest.mark.parametrize(
    ("key", "value"),
    [
        (RETRY, "am04"),  # en majúscules
        (RETRY, "AM4"),
        (BLOCK, "AC04, AC04"),
        (BLOCK, "AC04, MD01, AM04"),  # AM04 ja proposa un reintent
        (RETRY, "AM04, MD01"),  # MD01 ja bloqueja el mandat
    ],
)
def test_errors_de_validacio(treasurer, key, value):  # noqa: F811
    with pytest.raises(ValidationError):
        business_settings.change(key, value, treasurer)
    assert not SettingVersion.objects.exists()


def test_l_edita_el_tresorer_i_ningu_mes(treasurer, make_admin):  # noqa: F811
    client = admin_client(treasurer)
    url = reverse("administration:setting_detail", args=["payments", RETRY])
    page = client.post(url, {"value": "AM04, MS02", "note": ""})
    assert page.status_code == 302 and returns.codes(RETRY) == {"AM04", "MS02"}

    administrator = make_admin(Role.Code.ADMINISTRATOR)  # veu l'apartat, no l'edita
    with pytest.raises(Http404):
        business_settings.change(BLOCK, "AC04", administrator)
    secretary = admin_client(make_admin(Role.Code.SECRETARY))
    assert secretary.get(url).status_code == 404
    assert secretary.post(url, {"value": "AM04"}).status_code == 404
    assert returns.codes(RETRY) == {"AM04", "MS02"}
