from django.apps import AppConfig


class GrantsConfig(AppConfig):
    name = "apps.grants"
    verbose_name = "Ajuts"

    def ready(self):
        # La Junta a AJ4, AJ5 i AJ13: només les sol·licituds de què és responsable (059).
        from apps.core.permissions import register_scope_check

        register_scope_check(
            "own_applications",
            lambda account, obj: getattr(obj, "responsible_id", None) == account.person_id,
        )

        # T-M09A-10b (RN-M09A-18): avisos si canvia una despesa d'una versió enviada.
        from apps.expenses import documents
        from apps.expenses import services as expenses

        from . import package

        expenses.expense_annulled.connect(package.on_expense_annulled)
        documents.document_marked_illegible.connect(package.on_document_marked_illegible)
