"""Senyals del compte personal. `email_verified` surt quan un compte pendent confirma el correu
(`email_links.confirm_email`), dins de la mateixa transacció: el 07 hi subscriu al butlletí qui
ho havia triat en crear el compte (T-M07-32), sense que `accounts` depengui de `website`."""

from django.dispatch import Signal

email_verified = Signal()  # arguments: account, request
