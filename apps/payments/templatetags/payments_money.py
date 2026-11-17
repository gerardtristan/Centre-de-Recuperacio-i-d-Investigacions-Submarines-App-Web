"""Imports en cèntims a les plantilles de pagaments: «120,00 €» (`charges.euros`)."""

from django import template

from apps.core.charges import euros as _euros

register = template.Library()
register.filter("euros", _euros)
