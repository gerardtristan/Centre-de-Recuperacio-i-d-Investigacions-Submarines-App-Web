"""T-M02-20 (P-41): tipus de fitxer privat per a les fotos d'una sortida de medi ambient, xifrat a
l'aplicació com la resta (cap clau nova) i sense URL pública."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0082_website_public_images_permission"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="privatefile",
            name="private_file_kind_valid",
        ),
        migrations.AlterField(
            model_name="privatefile",
            name="kind",
            field=models.CharField(
                choices=[
                    ("gdpr_export", "Exportació de dades (RGPD)"),
                    ("payment_proof", "Comprovant d'un pagament a mà"),
                    ("expense_invoice", "Factura d'una despesa"),
                    ("expense_bank_proof", "Comprovant del banc d'una despesa"),
                    ("expense_masked_copy", "Còpia amb l'IBAN emmascarat"),
                    ("issued_invoice", "PDF d'una factura emesa"),
                    ("grant_package", "Paquet de justificació d'un ajut"),
                    ("certification_photo", "Foto del carnet d'una titulació"),
                    ("environment_photo", "Foto d'una sortida de medi ambient"),
                ],
                max_length=20,
                verbose_name="tipus",
            ),
        ),
        migrations.AddConstraint(
            model_name="privatefile",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    (
                        "kind__in",
                        [
                            "gdpr_export",
                            "payment_proof",
                            "expense_invoice",
                            "expense_bank_proof",
                            "expense_masked_copy",
                            "issued_invoice",
                            "grant_package",
                            "certification_photo",
                            "environment_photo",
                        ],
                    )
                ),
                name="private_file_kind_valid",
            ),
        ),
    ]
