"""Rutes de l'àrea personal del 09 (facturació): s'inclouran a `config/urls.py` al torn del nucli.
L'accés el controla el middleware de l'àrea personal (compte personal amb sessió vàlida)."""

from django.urls import path

from . import views

app_name = "invoicing"

urlpatterns = [
    path("socis/factures/", views.my_invoices_view, name="my_invoices"),
]
