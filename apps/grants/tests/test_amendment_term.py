"""T-M09A-16: termini d'esmena opcional per convocatòria (RN-M09A-23; CA-M09A-26). Només dades
inventades."""

from datetime import date

import pytest
from django.db import IntegrityError, transaction

from apps.grants import requirements as r
from apps.grants import services
from apps.grants.models import GrantCall
from apps.grants.tests.test_justification import granted  # noqa: F401 (fixture)
from apps.grants.tests.test_resolution import submitted  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


def record(application, by, **extra):
    fields = {
        "origin": "body",
        "received_on": date(2027, 3, 1),
        "description": "Cal la memòria signada",
        "responsible": by.person,
        "by": by,
    }
    return r.record_requirement(application, **{**fields, **extra})


def test_ca_m09a_26_la_data_limit_proposada_es_pot_canviar(granted, treasurer):  # noqa: F811
    GrantCall.objects.filter(pk=granted.call_id).update(amendment_term_days=10)
    assert record(granted, treasurer).due_on == date(2027, 3, 11)
    assert record(granted, treasurer, due_on=date(2027, 3, 20)).due_on == date(2027, 3, 20)


def test_sense_termini_la_data_limit_s_escriu(granted, treasurer):  # noqa: F811
    with pytest.raises(r.InvalidDates):
        record(granted, treasurer)


def test_el_termini_es_copia_a_l_edicio_seguent_i_no_pot_ser_zero(call, treasurer):
    call.amendment_term_days = 15
    call.save()
    assert services.copy_call(call, by=treasurer).amendment_term_days == 15
    with pytest.raises(IntegrityError), transaction.atomic():
        GrantCall.objects.filter(pk=call.pk).update(amendment_term_days=0)
