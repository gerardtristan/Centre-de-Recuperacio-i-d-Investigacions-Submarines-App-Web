"""P-123 (095, provisional fins que el banc ho confirmi): els països de l'IBAN admesos al mandat
són una llista editable a «Ajustos», que de bon principi és tota la zona SEPA. Un IBAN vàlid d'un
país que no hi és es rebutja amb «País no admès» i no es desa res. Només dades inventades: IBAN
de format vàlid amb un compte de zeros."""

import importlib

import pytest
from django.apps import apps as django_apps
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.accounts.models import FailedLogin
from apps.accounts.sessions import AUTH_AT_SESSION_KEY
from apps.accounts.tests.test_reauth import NOT_IT
from apps.core import business_settings
from apps.core.models import (
    AuditEntry,
    PermissionMatrixVersion,
    Role,
    RolePermission,
    Setting,
    SettingVersion,
)
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.payments import mandates
from apps.payments.models import MandateBankAccount, SepaMandate
from apps.payments.tests.test_mandate_signing import (  # noqa: F401 (fixtures)
    account,
    age_session,
    browser,
    member,
    sign,
    signing_on,
    text,
)
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

KEY = mandates.IBAN_COUNTRIES
TURKISH = "TR200000000000000000000001"  # 26 caràcters, vàlid, d'un país fora de la zona SEPA
FRENCH = "FR4900000000000000000000001"
REFUSED = "El banc del club no admet IBAN d&#x27;aquest país per domiciliar."


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


def test_de_bon_principi_tota_la_zona_sepa():
    countries = mandates.iban_countries()
    assert {"ES", "FR", "DE", "PT", "IT", "AD", "CH", "GB", "NO", "IS", "LI", "MC"} <= countries
    assert "TR" not in countries and "US" not in countries


def test_un_iban_d_un_pais_no_admes_es_rebutja_i_no_es_desa_res(browser, text):  # noqa: F811
    response = sign(browser, iban=TURKISH)
    page = response.content.decode()
    assert response.status_code == 200 and REFUSED in page
    assert not SepaMandate.objects.exists() and not MandateBankAccount.objects.exists()
    assert TURKISH[4:] not in page  # la resposta no repeteix mai l'IBAN rebutjat


def test_un_iban_d_un_pais_admes_es_desa(browser, text):  # noqa: F811
    sign(browser, iban=FRENCH)
    assert SepaMandate.objects.get().bank_account.iban_country == "FR"


def test_si_el_tresorer_treu_un_pais_ja_no_s_admet(browser, text, treasurer):  # noqa: F811
    business_settings.change(KEY, "ES", treasurer, note="Prova")
    assert REFUSED in sign(browser, iban=FRENCH).content.decode()
    assert not SepaMandate.objects.exists()
    entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED, field=KEY)
    assert entry.new_value == "ES" and "FR" in entry.old_value


def test_el_servei_tambe_ho_comprova(member, account, text):  # noqa: F811
    with pytest.raises(mandates.CountryNotAllowed):
        mandates.create_mandate(
            member,
            iban=TURKISH,
            holder_name="Anna Prova",
            holder_is_member=True,
            legal_text=text,
            account=account,
            creditor_identifier="ES00ZZZ00000000",
            evidence={},
        )
    assert not SepaMandate.objects.exists()


def test_si_la_llista_canvia_entre_el_formulari_i_el_servei_no_hi_ha_cap_500(
    browser,  # noqa: F811
    text,  # noqa: F811
    treasurer,
    monkeypatch,
):
    """El país el mira `create_mandate`, amb una sola lectura de l'ajust, i la vista en mostra
    l'error al camp. Aquí el Tresorer treu França just després que el formulari sigui vàlid
    (revisió de la #230)."""
    from apps.payments import mandate_views

    real = mandate_views._reauth_error

    def meanwhile(*args):
        business_settings.change(KEY, "ES", treasurer)
        return real(*args)

    monkeypatch.setattr(mandate_views, "_reauth_error", meanwhile)
    response = sign(browser, iban=FRENCH)
    assert response.status_code == 200 and REFUSED in response.content.decode()
    assert FRENCH[4:] not in response.content.decode()
    assert not SepaMandate.objects.exists() and not MandateBankAccount.objects.exists()


def test_sense_l_ajust_val_la_zona_sepa():
    Setting.objects.filter(key=KEY).delete()
    assert mandates.iban_countries() == mandates.SEPA_COUNTRIES
    assert "FR" in mandates.iban_countries() and "TR" not in mandates.iban_countries()


def test_la_constant_i_la_migracio_tenen_la_mateixa_llista():
    migration = importlib.import_module("apps.payments.migrations.0024_paisos_iban")
    assert set(migration.SEPA.split(", ")) == mandates.SEPA_COUNTRIES


def test_un_codi_que_no_es_de_cap_pais_amb_iban_es_rebutja_i_es_diu_quin(treasurer):
    for value, named in (("ES, PO", "PO"), ("XX es", "XX"), ("FR, US, QQ", "QQ, US")):
        with pytest.raises(ValidationError) as refused:
            business_settings.change(KEY, value, treasurer)
        message = " ".join(refused.value.messages)
        assert named in message and "no és cap país amb IBAN" in message
    assert not SettingVersion.objects.exists()
    # Un país amb IBAN fora de la llista inicial (p. ex. RS, si el banc l'admet) sí que es desa.
    business_settings.change(KEY, "ES, RS", treasurer)
    assert mandates.iban_countries() == {"ES", "RS"}


def test_un_pais_no_admes_no_gasta_la_reautenticacio(browser, text, account):  # noqa: F811
    """El país es mira abans de demanar la contrasenya: el soci no l'escriu per res, i ni una
    contrasenya equivocada no compta com a intent fallit (revisió de la #230)."""
    age_session(browser, 16)
    before = browser.session[AUTH_AT_SESSION_KEY]
    page = sign(browser, iban=TURKISH, password=NOT_IT).content.decode()
    assert REFUSED in page and not SepaMandate.objects.exists()
    assert not FailedLogin.objects.filter(account=account).exists()
    page = sign(browser, iban=TURKISH, password=PASSWORD).content.decode()
    assert REFUSED in page and browser.session[AUTH_AT_SESSION_KEY] == before


def test_desfer_la_0024_no_esborra_l_historial_de_la_matriu():
    migration = importlib.import_module("apps.payments.migrations.0024_paisos_iban")
    versions = PermissionMatrixVersion.objects.count()
    migration.unload(django_apps, None)
    assert not RolePermission.objects.filter(permission_code=migration.CODE).exists()
    removed = PermissionMatrixVersion.objects.order_by("-number").first()
    assert removed.diff == [
        {"role": "treasurer", "permission": migration.CODE, "before": "all", "after": None}
    ]
    migration.load(django_apps, None)
    assert PermissionMatrixVersion.objects.count() == versions + 2  # cap no s'esborra


@pytest.mark.parametrize("value", ["", "E", "ESP", "E1", "ES, ES", "ES FR fr"])
def test_errors_de_validacio(treasurer, value):
    with pytest.raises(ValidationError):
        business_settings.change(KEY, value, treasurer)
    assert not SettingVersion.objects.exists()


def test_el_valor_es_desa_en_forma_canonica(treasurer):
    business_settings.change(KEY, " fr;es,,pt ", treasurer)
    assert business_settings.get(KEY) == "ES, FR, PT"
    assert mandates.iban_countries() == {"ES", "FR", "PT"}


def test_l_edita_el_tresorer_i_ningu_mes(treasurer, make_admin):  # noqa: F811
    url = reverse("administration:setting_detail", args=["payments", KEY])
    response = admin_client(treasurer).post(url, {"value": "ES, FR", "note": ""})
    assert response.status_code == 302 and mandates.iban_countries() == {"ES", "FR"}
    with pytest.raises(Http404):  # l'administrador veu l'apartat, no l'edita
        business_settings.change(KEY, "ES", make_admin(Role.Code.ADMINISTRATOR))
    secretary = admin_client(make_admin(Role.Code.SECRETARY))
    assert secretary.post(url, {"value": "ES"}).status_code == 404
    assert mandates.iban_countries() == {"ES", "FR"}
