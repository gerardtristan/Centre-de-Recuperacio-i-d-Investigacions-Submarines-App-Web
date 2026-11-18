"""Permís que exigeix cada ruta del 01 (T-M01-37; CA-RP-13; matriu inicial de la 059).

Un sol lloc per declarar què demana cada vista del mòdul. La prova per cel·la
(`apps/members/tests/test_route_permissions.py`) hi compara la resposta real de cada ruta per a
cada rol de la configuració inicial, i falla si apareix una ruta del 01 que no hi és. Les vistes
continuen comprovant el permís amb `permission_required` i els serveis, de nou, al servidor:
aquesta taula no dona ni treu cap accés.

- `PUBLIC`: ruta pública declarada (RN-40; la mateixa llista a `apps/core/tests/test_access.py`).
- `OWN`: àrea del soci amb el compte personal. Cap permís de rol (059, punt 4.2): l'objecte surt
  de la sessió i l'identificador d'un altre dona «no trobat».
- Administració: per a cada mètode, els permisos que calen tots alhora, amb `READ` (qualsevol
  abast, també «Cons.») o `WRITE` (un abast que no sigui només de consulta). Sense permís, la
  vista respon «no trobat» (404), també abans de comprovar el mètode.
"""

PUBLIC = "public"
OWN = "own"
READ, WRITE = False, True

M2 = "core.people.manage"  # de la 00: perfils d'altres persones i els seus comptes personals
P2 = "members.create_in_person"
P3A = "members.requests.view"
P3 = "members.requests.approve_join"
P4 = "members.list"
P5 = "members.edit"
P6 = "members.edit_join_date"
P7 = "members.requests.resolve_change"
P7A = "members.requests.cancel_supplement"
P8 = "members.fees.generate"
P9 = "members.unpaid.mark"
P10 = "members.fees.view"
P11 = "members.export"
P18 = "members.cluber_import.run"
P19 = "members.licence_record.manage"
P21 = "members.card.revoke"
P22 = "members.fees.exempt"
AJ01 = "settings.section.members"  # ajustos de socis: «Cons.» veu, «Sí» edita (RN-RP-22)
AJ01_2 = "settings.edit.members.membership_types"  # T-M01-52 (P-376)


def _both(*needs):
    """GET i POST demanen el mateix (el permís es comprova abans que el mètode)."""
    return {"GET": needs, "POST": needs}


ROUTES = {
    # --- Públiques ---
    "members:join": PUBLIC,
    "members:card_verify": PUBLIC,
    # --- Àrea del soci (P12 a P16: accions pròpies) ---
    "members:profile": OWN,
    "members:accept_policies": OWN,
    "members:declare_expiry": OWN,
    "members:consent": OWN,
    "members:change_email": OWN,
    "members:birth_date": OWN,
    "members:erase": OWN,
    "members:export_data": OWN,
    "members:fees": OWN,
    "members:fee_detail": OWN,
    "members:card": OWN,
    "members:card_renew": OWN,
    "members:change_type": OWN,
    # 079 (RN-M01-93, punt 4): retirar el pas a simpatitzant propi mentre és pendent. Només POST.
    "members:change_type_withdraw": OWN,
    "members:leave": OWN,
    # --- Administració ---
    "administration:cluber_preview": _both((P18, READ)),
    "administration:join_in_person": _both((P2, WRITE)),
    "administration:join_requests": _both((P3A, READ)),
    "administration:join_approve": _both((P3, WRITE)),
    "administration:join_reject": _both((P3, WRITE)),
    "administration:members_list": _both((P4, READ)),
    "administration:member_detail": _both((P4, READ)),
    "administration:members_export": _both((P11, READ), (P4, READ)),
    "administration:member_edit": _both((P5, WRITE), (P4, READ)),
    # P6 demana P4 sencer: «dades mínimes» no veu la data d'alta.
    "administration:member_join_date": _both((P6, WRITE), (P4, WRITE)),
    # 079 (RN-M01-87): tornar a enviar la invitació del compte personal.
    "administration:member_invite": _both((M2, WRITE), (P4, READ)),
    # 079 (A-21, RN-M01-92): revocar el carnet d'un soci amb motiu.
    "administration:member_card_revoke": _both((P21, WRITE), (P4, READ)),
    # 081, punt 24 (P-52): restabliment presencial del doble factor del compte personal.
    "administration:member_totp_reset": _both((M2, WRITE), (P4, READ)),
    # 081, punt 16: C1 el comprova el servei (`birth_date.can_check`).
    "administration:member_birth_date_check": _both((P5, WRITE), (P4, READ)),
    # T-M01-40 (RN-M01-72 i RN-M01-94; 085): eximir o anul·lar una quota des de la fitxa.
    "administration:member_fee_exempt": _both((P22, WRITE), (P4, READ), (P10, READ)),
    "administration:member_fee_cancel": _both((P22, WRITE), (P4, READ), (P10, READ)),
    "administration:fees": _both((P10, READ)),
    "administration:fee_mark_unpaid": _both((P9, WRITE)),
    "administration:fee_unmark_unpaid": _both((P9, WRITE)),
    # 079 (A-17, RN-M01-89): marcar com a revisat el pagament d'un soci de baixa.
    "administration:fee_payment_reviewed": _both((P8, WRITE), (P10, READ)),
    "administration:licence_add": _both((P19, WRITE), (P4, READ)),
    "administration:licence_edit": _both((P19, WRITE), (P4, READ)),
    "administration:licence_bulk_confirm": _both((P19, WRITE), (P4, READ)),
    "administration:member_requests": _both((P3A, READ)),
    "administration:member_request_detail": {
        "GET": ((P3A, READ),),
        # Resoldre; anul·lar el suplement vençut és a `ACTIONS`.
        "POST": ((P3A, READ), (P7, WRITE)),
    },
    # 075 (RN-M01-83, CA-M01-84): també P4, per veure el nom del soci.
    "administration:member_leave_create": _both((P7, WRITE), (P4, READ)),
    # T-M01-52: tipus de soci. Desar també es pot amb «Sí» de l'apartat (`types.can_edit`); la
    # matriu inicial no el dona a cap rol.
    "administration:membership_types": {
        "GET": ((AJ01, READ),),
        "POST": ((AJ01, READ), (AJ01_2, WRITE)),
    },
    "administration:membership_type_edit": {
        "GET": ((AJ01, READ),),
        "POST": ((AJ01, READ), (AJ01_2, WRITE)),
    },
}

# Accions d'un POST que no demanen el permís de la ruta sinó **un** dels de la llista (qualsevol).
ACTIONS = {
    # 075 (RN-M01-82, CA-M01-83): P7a o P8 amb edició, a més de P3a per veure la sol·licitud.
    ("administration:member_request_detail", "cancel_supplement"): ((P7A, WRITE), (P8, WRITE)),
}
