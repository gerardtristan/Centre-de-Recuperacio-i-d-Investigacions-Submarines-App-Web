"""`website.counts()` (M08-2, per al 08; T-M08-08): recomptes de la web pública, sense cap
persona. Consulta agregada sense permís: el permís DB1 el comprova la vista del dashboard
(T-M08-09)."""

from .models import ContactMessage, NewsletterSubscription


def counts() -> dict[str, int]:
    """Subscriptors del butlletí que han confirmat el correu i missatges de contacte nous (encara
    sense resposta ni tancats)."""
    return {
        "confirmed_subscribers": NewsletterSubscription.objects.filter(
            status=NewsletterSubscription.Status.CONFIRMED
        ).count(),
        "pending_contact_messages": ContactMessage.objects.filter(
            status=ContactMessage.Status.NEW
        ).count(),
    }
