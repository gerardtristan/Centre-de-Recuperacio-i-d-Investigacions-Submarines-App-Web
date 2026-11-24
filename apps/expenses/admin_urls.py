"""Rutes del 09 (despeses) a l'àrea d'administració (M09-8): s'inclouen a
`apps.accounts.admin_urls`, dins de l'espai de noms `administration`. Cap ruta
pública."""

from django.urls import path

from . import views

urlpatterns = [
    path("despeses/nova/", views.new_view, name="expense_new"),
    path("despeses/sense-factura/", views.without_invoice_view, name="expenses_without_invoice"),
    path("despeses/<int:pk>/documents/", views.documents_view, name="expense_documents"),
]
