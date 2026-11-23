"""Rutes del 09 (marge d'una activitat i períodes) a l'àrea d'administració (M09-8): s'inclouen a
`apps.accounts.admin_urls`, dins de l'espai de noms `administration`."""

from django.urls import path

from . import views

urlpatterns = [
    path("marges/<int:activity_id>/", views.activity_view, name="activity_margin"),
    path("marges/<int:activity_id>/previst/", views.planned_view, name="activity_margin_planned"),
    path("marges/<int:activity_id>/tanca/", views.close_view, name="activity_margin_close"),
    path("marges/periodes/", views.periods_view, name="margin_periods"),
    path("marges/periodes/nou/", views.period_create_view, name="margin_period_create"),
    path(
        "marges/periodes/<int:period_id>/tanca/",
        views.period_close_view,
        name="margin_period_close",
    ),
    path(
        "marges/periodes/<int:period_id>/reobre/",
        views.period_reopen_view,
        name="margin_period_reopen",
    ),  # fmt: skip
]
