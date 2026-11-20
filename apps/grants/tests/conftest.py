import pytest

from apps.core.models import Department
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.grants.models import GrantCall, GrantCallDocument


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


@pytest.fixture
def general():
    return Department.objects.get(name="General")


@pytest.fixture
def call(treasurer):
    call = GrantCall.objects.create(
        body="Diputació Inventada", name="Medi marí", created_by=treasurer, max_resolution_days=90
    )
    for order, name in enumerate(["Memòria del projecte", "Pressupost"]):
        GrantCallDocument.objects.create(call=call, name=name, order=order)
    return call
