"""Rutes del 03 a l'àrea d'administració (T-M03-19 i T-M03-22): s'inclouen a
`apps.accounts.admin_urls`, dins de l'espai de noms `administration`."""

from django.urls import path

from . import views

urlpatterns = [
    path("material/informes/", views.reports_view, name="equipment_reports"),
    path(
        "material/informes/activitat/<int:activity_id>/",
        views.activity_cost_view,
        name="equipment_activity_cost",
    ),
    path("material/cost-d-us/", views.usage_rates_view, name="equipment_usage_rates"),
]
