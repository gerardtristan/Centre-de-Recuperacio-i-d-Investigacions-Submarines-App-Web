"""CA-M09-35 des de les pantalles (T-M09-26; condició b de la 055): el tresorer canvia la durada
dels períodes a trimestral a la pantalla d'ajustos i el període nou que crea a «Períodes» dura
tres mesos; els que ja hi havia no canvien i cap dia queda fora de cap període ni dins de dos.
Només dades inventades."""

import calendar
import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.core import business_settings
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.margins import period_closing
from apps.margins.models import Period

pytestmark = pytest.mark.django_db


def month_end(day):
    return day.replace(day=calendar.monthrange(day.year, day.month)[1])


def test_ca_m09_35_quarterly_from_the_settings_screen(login_as, make_admin):  # noqa: F811
    current = timezone.localdate().replace(day=1)
    previous = (current - datetime.timedelta(days=1)).replace(day=1)
    existing = [(previous, month_end(previous)), (current, month_end(current))]
    for starts_on, ends_on in existing:
        Period.objects.create(starts_on=starts_on, ends_on=ends_on)
    client = login_as(make_admin(Role.Code.TREASURER), AREA_ADMIN)

    detail = reverse("administration:setting_detail", args=["margin", period_closing.LENGTH])
    response = client.post(detail, {"value": "quarterly", "note": "Trimestral (inventat)."})
    assert response.status_code == 302
    assert business_settings.get(period_closing.LENGTH) == "quarterly"
    assert client.post(reverse("administration:margin_period_create")).status_code == 302

    start = month_end(current) + datetime.timedelta(days=1)
    third = (start.replace(day=28) + datetime.timedelta(days=62)).replace(day=1)
    rows = list(Period.objects.order_by("starts_on").values_list("starts_on", "ends_on"))
    assert rows == [*existing, (start, month_end(third))]
    for before, after in zip(rows, rows[1:], strict=False):
        assert after[0] == before[1] + datetime.timedelta(days=1)  # sense forats ni solapaments
