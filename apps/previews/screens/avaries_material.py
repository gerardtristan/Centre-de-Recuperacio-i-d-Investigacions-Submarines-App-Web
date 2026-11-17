"""T-DX-32 Averia: comunicar una avaria d'una peça del material (mòdul 03). Proposta: el pla té
l'estat «a revisió» (P-M03-D, P-M03-F) però no aquest formulari ni les preguntes per tipus (D1).
Contingut d'exemple, inventat."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Comunicar una avaria")

YES, NO = _("Sí"), _("No")

CONTEXT = {
    "types": [_("Regulador"), _("Jaquet"), _("Ordinador"), _("Ampolla")],
    "type": 0,
    "item": {"code": "MAT-0112", "type": _("Regulador"), "review": "03/2027"},
    "questions": [
        {"id": "q-aire", "text": _("Perd aire amb l'ampolla oberta?"), "answer": YES},
        {"id": "q-boca", "text": _("La segona etapa dona aire sense prémer-la?"), "answer": NO},
        {"id": "q-manometre", "text": _("El manòmetre marca bé?"), "answer": YES},
    ],
    "answers": [YES, NO],
    "description": _("Fa un xiulet a la primera etapa des de la sortida de dissabte."),
}
