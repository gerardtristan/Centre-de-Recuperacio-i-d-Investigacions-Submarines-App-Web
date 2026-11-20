"""T-M01-25c: el codi de línia «last_renewal» (falta la «Data alta/renovació» de Cluber, T-M01-25b)
entra a la llista tancada `IMPORT_LINE_CODES`. Fins ara `members.imports.final._codes` el treia
abans de desar la línia."""

from django.db import migrations, models

# La llista de la 0030; la migració no importa el model (ha de valer encara que canviï).
CODES = [
    "field_count",
    "field_too_long",
    "member_number_invalid",
    "email_invalid",
    "duplicate_document",
    "duplicate_member_number",
    "identity_conflict",
    "member_number_unavailable",
    "date_invalid",
    "amount_invalid",
    "balance_invalid",
    "member_number_leading_zeros",
    "match_without_document_type",
    "total_price_differs",
    "left_in_cluber",
    "member_type",
    "member_status",
    "joined_on",
    "id_document_type",
    "member_number",
    "first_name",
    "last_name",
    "id_document",
    "email",
    "phone",
]


def _constraint(codes):
    return models.CheckConstraint(
        condition=models.Q(("codes__contained_by", codes)),
        name="importline_codes_closed_list",
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0053_payment_proof")]

    operations = [
        migrations.RemoveConstraint(model_name="importline", name="importline_codes_closed_list"),
        migrations.AddConstraint(
            model_name="importline", constraint=_constraint([*CODES, "last_renewal"])
        ),
    ]
