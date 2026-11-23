"""Quina prova e2e cobreix quins fitxers (T-M00-07, CA-M00-07f; decisió 081, punt 1).

El hook de fi de torn fa servir aquest mapa per triar les proves e2e que passa:

- **Conjunt mínim** (`SMOKE`): sempre que hi ha canvis, els quatre fluxos crítics.
- **Fitxers del mapa** (`MAP`): les proves del mapa per a cada fitxer canviat, més el conjunt
  mínim, si el temps estimat hi cap.
- **Fitxers compartits** (`SHARED`): plantilles base, estils, configuració, models, migracions,
  serveis comuns, permisos, sessions... Afecten moltes pantalles: el hook només passa el conjunt
  mínim i la **verificació completa queda obligatòria** abans del commit.
- **Fitxers desconeguts** (cap patró): igual que els compartits. Una prova unitària, una
  plantilla de correu o un fitxer nou que no és al mapa no el pot verificar el hook.

Els patrons són de `fnmatch` sobre camins amb «/»: `*` també travessa carpetes. Una prova
(`test_e2e_map_*` a `apps/core/tests/test_verificacio_t_m00_07.py`) comprova que cada prova e2e
és al mapa i que cada patró correspon a algun fitxer.

`SECONDS` són temps de referència per fitxer de prova, en local amb la base reutilitzada; el hook
els substitueix pels que mesura cada vegada (`.e2e-captures/.verificacio.json`).
"""

from fnmatch import fnmatch

E2E_DIR = "apps/core/tests/e2e"
SMOKE = "test_smoke.py"

SHARED = (
    "templates/base*.html",
    "templates/403.html",
    "templates/accounts/_camp.html",
    "templates/accounts/_admin_nav.html",
    "templates/members/_personal_nav.html",
    "static/css/*",
    "static/js/tema.js",
    "static/vendor/*",
    "static/fonts/*",
    "config/*",
    "conftest.py",
    "pyproject.toml",
    "manage.py",
    "apps/*/migrations/*",
    "apps/*/models.py",
    "apps/*/apps.py",
    "apps/*/urls.py",
    "apps/*/admin_urls.py",
    "apps/*/permissions.py",
    "apps/*/checks.py",
    "apps/*/templatetags/*",
    "apps/*/management/*",
    "apps/core/audit.py",
    "apps/core/permissions.py",
    "apps/core/permission_catalog.py",
    "apps/core/roles.py",
    "apps/core/mail.py",
    "apps/core/persons.py",
    "apps/core/charges.py",
    "apps/core/crypto.py",
    "apps/core/files.py",
    "apps/core/consents.py",
    "apps/core/normalization.py",
    "apps/core/business_settings.py",
    "apps/core/tasks.py",
    "apps/accounts/middleware.py",
    "apps/accounts/sessions.py",
    "apps/accounts/security.py",
    "apps/accounts/views.py",
    "apps/accounts/forms.py",
    "apps/accounts/totp.py",
    "apps/accounts/reauth.py",
    "apps/members/services.py",
    "apps/members/forms.py",
    "apps/members/demo_data.py",
    "apps/core/tests/e2e/conftest.py",
    "apps/core/tests/conftest.py",
    ".claude/hooks/*",
    "tools/*",
    ".github/workflows/*",
)

MAP = {
    SMOKE: (
        "apps/members/join.py",
        "apps/members/views/public.py",
        "templates/members/join.html",
        "templates/members/_join_*.html",
        "templates/members/member_list.html",
        "templates/accounts/login*.html",
    ),
    "test_altes_079.py": (
        "apps/members/admissions.py",
        "apps/accounts/invitations.py",
        "templates/members/join_requests.html",
        "templates/accounts/invitation.html",
    ),
    "test_carnet_079.py": (
        "apps/members/cards.py",
        "apps/members/card_keys.py",
        "apps/members/validity.py",
        "apps/members/views/personal_card.py",
        "apps/members/views/public_card.py",
        "templates/members/personal_card.html",
        "templates/members/card_verify.html",
        "templates/members/_card_renew.html",
        "static/js/imprimeix.js",
    ),
    "test_carnet_3d.py": (
        "apps/members/views/personal_card.py",
        "templates/members/personal_card.html",
        "templates/members/_card_renew.html",
        "static/js/carnet.js",
    ),
    "test_duermevela.py": (
        "static/js/tema.js",
        "static/js/eclipse.js",
        "static/css/eclipse.css",
        "templates/_eclipse.html",
    ),
    "test_pwa_079.py": (
        "static/js/service-worker.js",
        "static/js/carnet-copia.js",
        "static/js/carnet.js",
        "static/js/pwa.js",
        "static/manifest.json",
        "static/img/*",
        "apps/core/views/pwa.py",
        "apps/members/cards.py",
        "apps/members/views/personal_card.py",
        "templates/members/personal_card.html",
        "templates/core/install_help_iphone.html",
    ),
    "test_comptes_emergencia.py": (
        "apps/accounts/emergency.py",
        "templates/accounts/_avis_emergencia.html",
        "templates/accounts/admin_accounts.html",
        "templates/accounts/admin_home.html",
    ),
    "test_permisos.py": (
        "apps/core/permission_matrix.py",
        "apps/core/views/permission_matrix.py",
        "templates/core/permission_matrix.html",
        "templates/emails/avis-canvi-permisos.*",
        "static/css/avisador.css",
    ),
    "test_rols.py": (
        "apps/core/roles.py",
        "apps/core/admin_urls.py",
        "apps/core/views/roles.py",
        "templates/emails/avis-canvi-rol.*",
        "templates/emails/avis-desactivacio-admin.*",
        "templates/core/account_roles.html",
        "templates/core/account_deactivate.html",
        "templates/accounts/login.html",
        "templates/accounts/admin_accounts.html",
    ),
    "test_activitats_crear.py": (
        "apps/activities/views/*",
        "apps/activities/forms.py",
        "templates/activities/activity_form.html",
    ),
    "test_activitats_cost_material.py": (
        "apps/activities/views/admin_activities.py",
        "templates/activities/activity_detail.html",
    ),
    "test_activitats_cataleg.py": (
        "apps/activities/views/admin_catalogue.py",
        "apps/activities/forms.py",
        "templates/activities/catalogue*.html",
    ),
    "test_activitats_llocs.py": (
        "apps/activities/views/admin_places.py",
        "apps/activities/forms.py",
        "templates/activities/place*.html",
    ),
    "test_activitats_admin.py": (
        "apps/activities/views/*",
        "apps/activities/admin_urls.py",
        "templates/activities/*",
    ),
    "test_despeses.py": (
        "apps/expenses/views.py",
        "apps/expenses/admin_urls.py",
        "templates/expenses/*",
    ),
    "test_marge_activitat.py": (
        "apps/margins/views.py",
        "apps/margins/admin_urls.py",
        "templates/margins/*",
    ),
    "test_calendari_ajuts.py": (
        "apps/grants/views.py",
        "apps/grants/admin_urls.py",
        "apps/grants/calendar.py",
        "templates/grants/*",
    ),
    "test_periodes.py": (
        "apps/margins/views.py",
        "apps/margins/admin_urls.py",
        "apps/margins/period_closing.py",
        "templates/margins/periods.html",
    ),
    "test_meves_factures.py": (
        "apps/invoicing/views.py",
        "apps/invoicing/urls.py",
        "templates/invoicing/*",
    ),
    "test_llicencies.py": (
        "apps/licences/views.py",
        "apps/licences/personal_views.py",
        "apps/licences/listing.py",
        "apps/licences/filing.py",
        "templates/licences/*",
    ),
    "test_pagaments_llistat.py": (
        "apps/payments/payment_admin_views.py",
        "apps/payments/reviews.py",
        "templates/payments/payments.html",
        "templates/payments/review_close.html",
    ),
    "test_mandats.py": (
        "apps/payments/admin_views.py",
        "templates/payments/mandates.html",
        "templates/payments/mandate_admin_revoke.html",
    ),
    "test_campanya_mandats.py": (
        "apps/payments/admin_views.py",
        "apps/payments/campaigns.py",
        "templates/payments/campaign.html",
    ),
    "test_remeses.py": (
        "apps/payments/remittance_views.py",
        "apps/payments/remittances.py",
        "apps/payments/sepa_xml.py",
        "templates/payments/remittance*.html",
        "templates/payments/_remittance_status.html",
    ),
    "test_retornats.py": (
        "apps/payments/return_views.py",
        "apps/payments/returns.py",
        "apps/payments/bank_returns.py",
        "templates/payments/returns.html",
    ),
    "test_mandat_signatura.py": (
        "apps/payments/mandate_views.py",
        "apps/payments/forms.py",
        "templates/payments/mandate.html",
        "templates/payments/mandate_revoke.html",
    ),
    "test_metode_quota.py": (
        "apps/payments/preference_views.py",
        "apps/payments/preferences.py",
        "templates/payments/fee_method.html",
    ),
    "test_targeta_guardada.py": (
        "apps/payments/card_views.py",
        "apps/payments/cards.py",
        "apps/payments/providers/fake.py",
        "templates/payments/saved_card.html",
        "templates/payments/saved_card_remove.html",
        "templates/payments/fake_pay.html",
    ),
    "test_tresoreria.py": (
        "apps/treasury/views.py",
        "apps/treasury/admin_urls.py",
        "apps/treasury/reconciliation.py",
        "apps/treasury/settlements.py",
        "apps/treasury/balances.py",
        "apps/treasury/exports.py",
        "templates/treasury/*.html",
    ),
    "test_tresoreria_exclusions.py": (  # T-M04-14d
        "apps/treasury/views.py",
        "apps/treasury/admin_urls.py",
        "apps/treasury/reconciliation.py",
        "templates/treasury/reconciliation.html",
    ),
    "test_tresoreria_moviments_casats.py": (  # T-M04-12f
        "apps/treasury/views.py",
        "apps/treasury/admin_urls.py",
        "apps/treasury/reconciliation.py",
        "templates/treasury/reconciliation.html",
        "templates/treasury/match_movements.html",
    ),
    "test_tresoreria_entrades.py": (
        "apps/treasury/entry_views.py",
        "apps/treasury/admin_urls.py",
        "apps/treasury/settlements.py",
        "templates/treasury/*.html",
    ),
    "test_ajustos.py": (
        "apps/core/views/business_settings.py",
        "apps/core/texts.py",
        "apps/core/templatetags/textos.py",
        "apps/core/views/legal_texts.py",
        "templates/core/legal_text*.html",
        "apps/members/settings.py",
        "apps/payments/returns.py",
        "apps/members/types.py",
        "apps/members/views/admin_types.py",
        "templates/core/setting*.html",
        "templates/members/membership_type*.html",
        "apps/payments/transfer_reminders.py",
    ),
    "test_dades_bloquejades.py": (
        "apps/core/locked_data.py",
        "apps/core/views/locked_data.py",
        "templates/core/locked_data_*.html",
    ),
    "test_edicio_soci_079.py": (
        "apps/members/member_edit.py",
        "apps/members/birth_date.py",
        "apps/members/views/admin.py",
        "apps/members/views/admin_member_edit.py",
        "apps/accounts/personal_reset.py",
        "templates/members/member_detail.html",
        "templates/members/member_edit.html",
        "templates/members/member_join_date.html",
        "templates/members/member_totp_reset.html",
        "templates/members/_member_edit_links.html",
        "templates/members/_join_date_history.html",
    ),
    "test_fitxa_081.py": (
        "apps/members/birth_date.py",
        "apps/members/views/admin.py",
        "apps/members/views/admin_member_edit.py",
        "apps/accounts/personal_reset.py",
        "templates/members/member_detail.html",
        "templates/members/member_totp_reset.html",
        "templates/members/_member_edit_links.html",
    ),
    "test_extracte_bancari.py": (
        "apps/core/imports/bank_statement.py",
        "apps/core/views/bank_statement.py",
        "templates/core/bank_statement.html",
    ),
    "test_enllacos_convidat.py": (
        "apps/core/guest_links.py",
        "apps/core/views/guest.py",
        "templates/core/guest*.html",
    ),
    "test_monograma.py": (
        "apps/members/templatetags/monograma.py",
        "apps/members/templatetags/member_notices.py",
        "templates/core/home.html",
        "templates/members/personal_profile.html",
        "static/css/monograma.css",
    ),
    "test_naixement_035.py": (
        "apps/members/birth_date.py",
        "apps/members/views/personal.py",
        "templates/members/_birth_date_notice.html",
        "templates/members/personal_profile.html",
    ),
    "test_navegacio.py": (
        "apps/accounts/navigation.py",
        "static/js/menu-admin.js",
        "templates/accounts/admin_home.html",
    ),
    "test_pagines_error.py": ("templates/404.html", "templates/500.html"),
    "test_logotip.py": ("static/img/marca/*",),  # T-DX-51
    "test_disposicio.py": (  # T-DX-57; l'inici del soci, T-DX-60
        "static/css/disposicio.css",
        "templates/core/home.html",
        "static/css/oleaje.css",
    ),
    "test_vigencia_admin.py": ("templates/members/_licence_records.html",),
    "test_oleaje.py": (
        "apps/members/templatetags/member_notices.py",
        "templates/core/home.html",
        "static/css/oleaje.css",
    ),
    "test_previews.py": ("apps/previews/*", "templates/previews/*"),
    "test_activitats.py": (  # T-DX-63
        "apps/previews/screens/activitats*",
        "templates/previews/*activitats*",
        "static/css/activitats.css",
        "static/js/activitats.js",
    ),
    "test_vigencia.py": (
        "apps/members/templatetags/vigencia.py",
        "templates/members/_vigencia.html",
        "static/css/vigencia.css",
    ),
    "test_ramillete.py": (
        "static/js/ramillete.js",
        "static/css/ramillete.css",
        "templates/members/_ramillete.html",
    ),
    "test_navegacio_soci.py": (  # T-DX-59
        "static/js/ramillete.js",
        "static/css/ramillete.css",
        "templates/members/_ramillete.html",
        "apps/members/templatetags/member_nav.py",
    ),
    "test_solapas.py": (
        "static/js/solapas.js",
        "static/css/solapas.css",
        "templates/members/member_detail.html",
        "templates/members/request_detail.html",
    ),
    "test_errata.py": (
        "templates/_errata.html",
        "static/css/errata.css",
        "static/js/errata.js",
        "templates/members/_join_form.html",
    ),
    "test_pas_a_simpatitzant_073.py": (
        "apps/members/member_requests.py",
        "apps/members/views/personal_requests.py",
        "apps/members/views/admin_requests.py",
        "templates/members/personal_change_type.html",
        "templates/members/personal_downgrade.html",
        "templates/members/request_detail.html",
        "templates/members/requests_list.html",
        "templates/members/_requests_table.html",
    ),
    "test_politiques_079.py": (
        "apps/members/policies.py",
        "apps/members/views/personal_policies.py",
        "templates/members/accept_policies.html",
        "templates/members/cluber_preview.html",
        "static/js/textos-legals.js",
    ),
    "test_quotes_079.py": (
        "apps/members/fees.py",
        "apps/payments/returns.py",
        "apps/members/fee_rules.py",
        "apps/members/validity.py",
        "apps/members/roster.py",
        "templates/members/fees.html",
        "templates/members/_fee_state.html",
        "templates/members/_charge_status.html",
        "templates/members/personal_fees.html",
        "templates/members/personal_fee_detail.html",
    ),
    "test_rgpd_notes_22c.py": (
        "apps/core/privacy.py",
        "apps/core/views/gdpr.py",
        "apps/members/privacy.py",
        "templates/core/gdpr_notes_export.html",
        "templates/members/_member_edit_links.html",
    ),
    "test_rgpd_menor_22c.py": (
        "apps/core/erasure.py",
        "apps/core/views/gdpr.py",
        "templates/core/gdpr_in_person.html",
        "templates/core/gdpr_request_detail.html",
        "templates/members/_member_edit_links.html",
    ),
    "test_recuperacio_39b.py": (
        "apps/accounts/email_links.py",
        "apps/accounts/views.py",
        "templates/accounts/password_reset_request.html",
    ),
    "test_terminis_049.py": (
        "apps/members/instalments.py",
        "apps/members/views/personal.py",
        "apps/members/views/admin.py",
        "apps/members/urls.py",
        "apps/members/permissions.py",
        "templates/members/personal_fee_detail.html",
        "templates/members/fees.html",
        "apps/members/views/admin_member_edit.py",
        "templates/members/member_fee_instalments.html",
        "templates/members/member_fee_choose_instalments.html",
    ),
    "test_recorreguts_048.py": ("design/*",),
    "test_revisio_pantalles_045.py": (
        "templates/members/join_requests.html",
        "templates/members/member_join_date.html",
        "templates/members/personal_leave.html",
        "templates/members/personal_change_type.html",
        "templates/members/leave_create.html",
        "templates/accounts/admin_home.html",
    ),
    "test_rgpd.py": (
        "apps/core/erasure.py",
        "apps/core/privacy.py",
        "apps/core/views/gdpr.py",
        "apps/members/privacy.py",
        "apps/accounts/privacy.py",
        "templates/core/gdpr_*.html",
        "templates/members/personal_erase.html",
        "templates/members/personal_profile.html",
    ),
    "test_sessio_caducada_081.py": ("templates/accounts/session_expired.html",),
    "test_exempcio_040.py": (
        "apps/members/fees.py",
        "apps/members/validity.py",
        "apps/members/views/admin.py",
        "apps/members/views/admin_member_edit.py",
        "apps/core/charges.py",
        "templates/members/member_detail.html",
        "templates/members/member_fee_resolve.html",
        "templates/members/_charge_status.html",
    ),
    # El flux sencer «fer-se soci» (llesca 1) encadena tots els trams: es lliga als fitxers que
    # decideixen si el soci està al corrent i si el carnet val, que ja demanen la verificació
    # completa. Així el hook de fi de torn no s'allarga.
    "test_flux_fer_se_soci.py": (
        "apps/members/validity.py",
        "apps/members/cards.py",
        # P-12: el tram 4, el pagament a mà, només el cobreix aquest flux.
        "apps/treasury/entry_views.py",
        "templates/treasury/manual_payment.html",
    ),
    "test_flux_primer_euro.py": (
        "apps/payments/processing.py",
        "apps/payments/webhooks.py",
        "apps/treasury/services.py",
    ),
    "test_rebut.py": (
        "apps/payments/receipts.py",
        "templates/payments/receipt.html",
    ),
    "test_pagament_targeta.py": (
        "apps/payments/views.py",
        "apps/payments/checkout.py",
        "apps/payments/providers/fake.py",
        "templates/payments/*",
        "templates/members/personal_fee_detail.html",
    ),
    "test_pagament_bizum.py": (
        "apps/payments/views.py",
        "apps/payments/checkout.py",
        "apps/payments/providers/fake.py",
        "templates/payments/*",
    ),
    "test_pagament_transferencia.py": (
        "apps/payments/views.py",
        "apps/payments/checkout.py",
        "apps/payments/transfers.py",
        "apps/treasury/reconciliation.py",
        "templates/payments/*",
        "static/js/copia.js",
    ),
    "test_pagament_convidat.py": (
        "apps/payments/views.py",
        "apps/payments/checkout.py",
        "apps/payments/attempts.py",
        "templates/payments/*",
        "templates/core/guest.html",
    ),
    # Accessibilitat del flux de mandat (T-M05a-18) a tres amplades: triga més que el pressupost.
    "test_accessibilitat_mandat.py": (
        "templates/payments/fee_method.html",
        "templates/payments/mandate*.html",
        "templates/payments/campaign.html",
    ),
    # Transferència de principi a fi per les pantalles (T-M05b-18).
    "test_principi_a_fi_transferencia.py": (
        "templates/core/bank_statement.html",
        "templates/treasury/reconciliation.html",
        "apps/treasury/reconciliation.py",
        "apps/core/imports/bank_statement.py",
    ),
    # L'auditoria d'accessibilitat recorre 31 pantalles: qualsevol plantilla la necessita. Triga
    # més que el pressupost del hook, de manera que un canvi de plantilla sempre deixa la
    # verificació completa obligatòria.
    "test_accessibilitat_028.py": ("templates/*.html",),
    # Auditoria d'accessibilitat (B8) de la tresoreria i del 05b, a dues amplades: com la 028,
    # triga més que el pressupost del hook.
    "test_accessibilitat_tresoreria.py": (
        "templates/treasury/*.html",
        "templates/core/bank_statement.html",
    ),
    "test_accessibilitat_05b.py": (
        "templates/payments/payments.html",
        "templates/payments/remittance*.html",
        "templates/payments/returns.html",
        "templates/payments/charge.html",
        "templates/payments/_status.html",
        "templates/payments/_tramite.html",
        "templates/payments/receipt.html",
        "templates/members/personal_fees.html",
        "templates/members/personal_fee_detail.html",
        "templates/core/setting*.html",
    ),
}

SECONDS = {
    SMOKE: 35,
    "test_accessibilitat_028.py": 120,
    "test_accessibilitat_mandat.py": 120,
    "test_accessibilitat_tresoreria.py": 100,
    "test_accessibilitat_05b.py": 170,
    "test_pwa_079.py": 45,
    "test_carnet_3d.py": 40,
    "test_recorreguts_048.py": 20,
    "test_logotip.py": 130,  # tres motors (T-DX-54)
    "test_navegacio_soci.py": 50,  # cinc amplades en clar i en fosc (T-DX-59)
    "test_activitats.py": 60,  # T-DX-63: cinc amplades i axe en clar i en fosc
}
DEFAULT_SECONDS = 25


def _matches(path: str, patterns) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def plan(changed, durations=None, budget=70.0):
    """Què passa el hook. Torna (proves, verificació completa obligatòria, motius).

    - Un fitxer e2e canviat es passa ell mateix.
    - Compartit o desconegut: només el conjunt mínim i la completa obligatòria.
    - Del mapa: les seves proves i el conjunt mínim, si el temps estimat no passa de `budget`;
      si en passa, només el conjunt mínim i la completa obligatòria.
    """
    durations = {**SECONDS, **(durations or {})}
    selected, reasons = {SMOKE}, []
    full = False
    for path in changed:
        if path.startswith(f"{E2E_DIR}/test_") and path.endswith(".py"):
            selected.add(path.rsplit("/", 1)[1])
            continue
        if _matches(path, SHARED):
            full = True
            reasons.append(f"compartit: {path}")
            continue
        tests = [test for test, patterns in MAP.items() if _matches(path, patterns)]
        if not tests:
            full = True
            reasons.append(f"sense prova e2e al mapa: {path}")
            continue
        selected.update(tests)
    estimate = sum(durations.get(test, DEFAULT_SECONDS) for test in selected)
    if estimate > budget:
        full = True
        reasons.append(f"selecció massa llarga: uns {estimate:.0f} s")
        selected = {SMOKE}
    return sorted(selected), full, reasons
