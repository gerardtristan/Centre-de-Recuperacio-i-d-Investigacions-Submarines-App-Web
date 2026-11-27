"""La biblioteca de claus d'accés hi és (WebAuthn, decisió 108, D.3)."""

import json

from webauthn import generate_registration_options, options_to_json


def test_webauthn_genera_les_opcions_de_registre():
    options = generate_registration_options(
        rp_id="cris1954.cat", rp_name="C.R.I.S.", user_name="persona@exemple.invalid"
    )
    data = json.loads(options_to_json(options))
    assert data["rp"]["id"] == "cris1954.cat"
    assert data["challenge"]
