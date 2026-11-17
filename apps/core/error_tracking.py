"""Seguiment d'errors (checklist E4, part del nivell 1; R11): GlitchTip o Sentry amb el mateix SDK.

Només s'activa a producció i només amb `ERROR_TRACKING_DSN` (config/settings/prod.py): sense, no
s'inicialitza res i no surt res per la xarxa. El host del DSN decideix on van les dades, per
això el DSN ha de ser `https` i el host ha de ser a `ERROR_TRACKING_ALLOWED_HOSTS` o l'aplicació
no arrenca.

Mai no s'envia: el cos, les galetes, la cadena de consulta ni l'URL de la petició (un enllaç de
convidat porta el testimoni al camí; a la transacció, els trossos del camí que semblen un
testimoni es tapen),
cap capçalera fora de `_SAFE_HEADERS`, l'usuari, les variables locals, els `extra` ni els
paràmetres de les consultes SQL. Als missatges d'error i de registre es tapen els IBAN, les
targetes i altres números llargs, els correus, els DNI i NIE, els telèfons i les IP.

Aquest mòdul es carrega des dels settings: no pot importar res de Django que necessiti les apps.
"""

import re
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

# Al codi i no a l'entorn: qui posa el DSN no ha de poder posar també el host permès; un host nou
# entra amb una PR revisada. P-294 (propietari, 17/11/2026): GlitchTip autoallotjat al mateix VPS
# de Hetzner (UE). El nom del subdomini és [A validar] (arquitectura §2, «Domini i DNS»).
ERROR_TRACKING_ALLOWED_HOSTS = ("errors.cris1954.cat",)

MASK = "[tapat]"
_SAFE_HEADERS = {"user-agent", "content-type", "accept", "accept-language"}
# shortcut: patrons amples (tapen també algun identificador que no és personal); si un error
# real queda il·legible, s'afina el patró concret amb una prova.
_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),  # correu
    # IBAN, també enganxat a una paraula («iban_ES00…»)
    re.compile(r"(?<![A-Za-z0-9])[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?\b", re.I),
    re.compile(r"\d(?:[ -]?\d){11,}"),  # targeta, compte antic de 20 dígits
    re.compile(r"(?<![A-Za-z0-9])(?:\d{8}|[XYZ]\d{7})[ -]?[A-Z](?![A-Za-z0-9])", re.I),  # DNI, NIE
    re.compile(r"(?:\+\d{2}[ -]?|(?<![\d+]))[6-9](?:[ -]?\d){8}(?!\d)"),  # telèfon
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),  # IPv4
    # IPv6: sencera o comprimida amb «::» (una hora com 12:30:45 no hi entra)
    re.compile(
        r"(?<![\w:])(?:(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}"
        r"|(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4})*)?::(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4})*)?)(?![\w:])",
        re.I,
    ),
]
# Tros del camí que sembla un testimoni: llarg i amb alguna majúscula o xifra. Les paraules de
# les rutes (minúscules i guions) i els patrons com `<int:pk>` es queden llegibles.
_TOKEN_SEGMENT = re.compile(r"(?=.*[A-Z0-9])[A-Za-z0-9_:-]{16,}")


def mask(text):
    if not isinstance(text, str):
        return text
    for pattern in _PATTERNS:
        text = pattern.sub(MASK, text)
    return text


def mask_path(path):
    segments = path.split("/")
    return mask("/".join(MASK if _TOKEN_SEGMENT.fullmatch(s) else s for s in segments))


def before_send(event, hint):
    # Sense ruta resolta, la integració de Django posa el camí tal qual.
    if isinstance(event.get("transaction"), str):
        event["transaction"] = mask_path(event["transaction"])
    if "request" in event:
        request = event["request"] or {}
        headers = request.get("headers") or {}
        event["request"] = {
            "method": request.get("method"),
            "headers": {k: v for k, v in headers.items() if k.lower() in _SAFE_HEADERS},
        }
    for key in ("user", "extra"):
        event.pop(key, None)
    if "message" in event:
        event["message"] = mask(event["message"])
    if event.get("logentry"):
        # Sense `params`: el text ja formatat i tapat n'és prou.
        event["logentry"] = {k: mask(v) for k, v in event["logentry"].items() if k != "params"}
    for exception in (event.get("exception") or {}).get("values") or []:
        exception["value"] = mask(exception.get("value"))
        for frame in (exception.get("stacktrace") or {}).get("frames") or []:
            frame.pop("vars", None)
    return event


def before_breadcrumb(crumb, hint):
    # Les consultes SQL porten els paràmetres (dades de socis): no es guarden.
    if crumb.get("category") == "query":
        return None
    crumb.pop("data", None)
    crumb["message"] = mask(crumb.get("message"))
    return crumb


def dsn_host_allowed(dsn, allowed_hosts):
    parts = urlsplit(dsn)
    host = (parts.hostname or "").lower()
    allowed = {h.strip().lower() for h in allowed_hosts}
    return parts.scheme.lower() == "https" and bool(host) and host in allowed


def init(dsn, environment):
    if not dsn_host_allowed(dsn, ERROR_TRACKING_ALLOWED_HOSTS):
        raise ImproperlyConfigured(
            "ERROR_TRACKING_DSN ha de ser https i el host ha de ser a ERROR_TRACKING_ALLOWED_HOSTS "
            "(apps/core/error_tracking.py): el seguiment d'errors només pot enviar dades a un "
            "servei de la UE que hagi triat el propietari (P-294)."
        )
    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        traces_sample_rate=0,
        max_breadcrumbs=10,
        before_send=before_send,
        before_breadcrumb=before_breadcrumb,
    )
