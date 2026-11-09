"""Verificació pública del carnet (T-M01-20; P15; RN-M01-26 a 28; CA-M01-09 part del carnet,
CA-M01-13, CA-M01-14, CA-M01-16).

- Ruta pública declarada (RN-40): qualsevol persona, amb sessió o sense (P15).
- Respon «Vàlid» o «No vàlid» segons `cards.valid_card_for_token`. Un testimoni inventat,
  revocat, d'un soci impagat, de baixa o caducat dona la mateixa pàgina, amb el mateix codi 200 i
  un temps mínim comú (RN-M01-27): no es pot saber si el testimoni ha existit.
- Cap dada personal. El número parcial (RN-M01-26, S-M01-06) i el nom de pila (S-M01-07) són
  [A validar: junta] i no es mostren (diari de la T-M01-20).
- Límit per origen de V-01 (RN-M01-28, `limits.start_card_verification`): compten totes les
  consultes, vàlides o no.
- El testimoni no es desa enlloc: ni al registre d'activitat, ni a la memòria cau (`never_cache`),
  ni al registre `django.request`. `noindex` i cap «Referer» cap a fora.
"""

from time import monotonic, sleep

from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from apps.accounts import limits
from apps.accounts.security import client_ip
from apps.members import cards

TEMPLATE = "members/card_verify.html"
# Temps mínim de resposta d'una consulta: un testimoni desconegut (una consulta) i un de conegut
# (carnet, soci i quotes) triguen el mateix vist des de fora (RN-M01-27).
MIN_SECONDS = 0.25


def _verify(request, token):
    if request.method not in ("GET", "HEAD"):
        return HttpResponseNotAllowed(["GET", "HEAD"])
    started = monotonic()
    with transaction.atomic():
        allowed = limits.start_card_verification(client_ip(request))
    if not allowed:
        return render(request, TEMPLATE, {"limited": True}, status=429)
    valid = cards.valid_card_for_token(token) is not None
    sleep(max(0.0, MIN_SECONDS - (monotonic() - started)))
    return render(request, TEMPLATE, {"valid": valid})


@login_not_required
@never_cache
def card_verify_view(request, token):
    response = _verify(request, token)
    # Django escriu el camí de les respostes 4xx (amb el testimoni) al registre `django.request`;
    # aquesta marca, la mateixa que fa servir Django per no registrar-les dues vegades, ho evita.
    response._has_been_logged = True
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Referrer-Policy"] = "no-referrer"
    return response
