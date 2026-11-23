"""Rutes del 02 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de l'espai
de noms `administration` (sessió d'administració i TOTP). Cada vista comprova el seu permís."""

from django.urls import path

from .views import admin_activities as activities
from .views import admin_filings as filings

urlpatterns = [
    path("activitats/", activities.activities_view, name="activities"),
    path("activitats/curs/nou/", activities.activity_course_add_view, name="activity_course_add"),
    path(
        "activitats/sortida/nova/", activities.activity_outing_add_view, name="activity_outing_add"
    ),
    path("activitats/<int:pk>/", activities.activity_detail_view, name="activity_detail"),
    path("activitats/<int:pk>/edita/", activities.activity_edit_view, name="activity_edit"),
    # T-M02-44b: homologacions a la federació (AC25 i AC26).
    path("homologacions/", filings.filings_view, name="filings"),
    path("homologacions/csv/", filings.filings_csv_view, name="filings_csv"),
    path("homologacions/demana/", filings.filing_request_view, name="filing_request"),
    path("homologacions/<int:pk>/", filings.filing_detail_view, name="filing_detail"),
    path("homologacions/<int:pk>/tramitada/", filings.filing_filed_view, name="filing_filed"),
    path("homologacions/<int:pk>/feta/", filings.filing_done_view, name="filing_done"),
    path("homologacions/<int:pk>/rebutja/", filings.filing_reject_view, name="filing_reject"),
]
